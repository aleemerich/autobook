#!/usr/bin/env python3
"""
tests/test_editorial_revision_steps.py — Unit tests for the editorial revision helpers.
"""

import json
from pathlib import Path
import pytest
from pipelines.editorial_revision_steps.context import (
    parse_chapter_number,
    list_chapter_files,
    filter_chapter_files,
    load_chapter_text,
)
from pipelines.editorial_revision_steps.evaluation import (
    load_evaluation_json,
    format_eval_feedback,
)


def test_parse_chapter_number():
    assert parse_chapter_number(Path("ch_01.md")) == 1
    assert parse_chapter_number(Path("ch_12.md")) == 12
    assert parse_chapter_number(Path("ch_00.md")) == 0
    assert parse_chapter_number(Path("ch_123.md")) == 123
    assert parse_chapter_number(Path("ch_abc.md")) is None
    assert parse_chapter_number(Path("outline.md")) is None
    assert parse_chapter_number(Path("ch_01.txt")) is None
    assert parse_chapter_number(Path("ch_01_extra.md")) is None
    assert parse_chapter_number(Path("some/dir/ch_05.md")) == 5


def test_list_chapter_files(tmp_path):
    chapters_dir = tmp_path / "chapters"
    
    # Test non-existing directory
    assert list_chapter_files(chapters_dir) == []
    
    chapters_dir.mkdir()
    # Create some mock files
    (chapters_dir / "ch_02.md").touch()
    (chapters_dir / "ch_01.md").touch()
    (chapters_dir / "ch_10.md").touch()
    (chapters_dir / "outline.md").touch()
    (chapters_dir / "ch_abc.md").touch()
    (chapters_dir / "ch_05.txt").touch()  # invalid extension
    
    expected = [
        chapters_dir / "ch_01.md",
        chapters_dir / "ch_02.md",
        chapters_dir / "ch_10.md",
    ]
    assert list_chapter_files(chapters_dir) == expected


def test_filter_chapter_files():
    files = [
        Path("ch_01.md"),
        Path("ch_02.md"),
        Path("ch_10.md"),
    ]
    # If selected_chapters is None/empty, return all
    assert filter_chapter_files(files, None) == files
    assert filter_chapter_files(files, []) == files
    
    # Filter specific chapters
    assert filter_chapter_files(files, [2, 10, 5]) == [Path("ch_02.md"), Path("ch_10.md")]
    assert filter_chapter_files(files, [5]) == []


def test_load_chapter_text(tmp_path):
    f = tmp_path / "ch_01.md"
    content = "Era uma vez... Ação e Emoção. 🚀"
    f.write_text(content, encoding="utf-8")
    assert load_chapter_text(f) == content


def test_load_evaluation_json(tmp_path):
    f_valid = tmp_path / "eval_valid.json"
    data = {"overall_score": 8.5, "comments": "Muito bom"}
    f_valid.write_text(json.dumps(data), encoding="utf-8")
    
    f_invalid = tmp_path / "eval_invalid.json"
    f_invalid.write_text("{broken json", encoding="utf-8")
    
    f_missing = tmp_path / "eval_missing.json"
    
    assert load_evaluation_json(f_valid) == data
    assert load_evaluation_json(f_invalid) == {}
    assert load_evaluation_json(f_missing) == {}


def test_format_eval_feedback():
    eval_data = {
        "canon_compliance": {
            "score": 6,
            "violations": ["Personagem X apareceu em dois lugares", "Espada trocou de nome"]
        },
        "slop": {
            "tier1_hits": [("delve", 2), ("tapestry", 1)],
            "tier2_hits": [("synergy", 3)],
            "structural_ai_tics": [("not only", 2)],
            "fiction_ai_tells": [("help but", 1)],
            "em_dash_density": 18.5,
        },
        "voice_adherence": {"score": 5.0, "weakest_moment": "Frase de IA", "fix": "Melhorar tom"},
        "beat_coverage": {"score": 8.0, "weakest_moment": "", "fix": ""},
        "character_voice": {"score": 6.5, "weakest_moment": "Diálogo artificial", "fix": "Reescrever fala"},
        "prose_quality": {"score": 5.5, "fix": "Encurtar frases", "weakest_sentence": "Sentence weak"},
        "three_weakest_sentences": ["Frase ruim 1", "Frase ruim 2"]
    }
    
    # 1. Test when retry_idx < 2 (e.g. retry_idx = 1)
    # Target dimensions are empty (since retry_idx < 2).
    # Slop style is excluded (since retry_idx < 3).
    feedback = format_eval_feedback(eval_data, retry_idx=1)
    
    # Check canon
    assert "### VIOLAÇÕES DE CANON/LORE:" in feedback
    assert "- Personagem X apareceu em dois lugares" in feedback
    assert "- Espada trocou de nome" in feedback
    
    # Check slop critical
    assert "### PROBLEMAS DE SLOP CRÍTICO:" in feedback
    assert "PALAVRAS PROIBIDAS usadas (MUDAR IMEDIATAMENTE): 'delve' (usado 2 vezes), 'tapestry' (usado 1 vezes)" in feedback
    
    # Slop style should NOT be present
    assert "### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):" not in feedback
    
    # Target dimensions should NOT be present
    assert "### DEFICIÊNCIAS NAS DIMENSÕES NARRATIVAS:" not in feedback
    
    # Weakest sentences
    assert "### FRASES MAIS FRACAS (REESCREVER/MELHORAR):" in feedback
    assert '- "Frase ruim 1"' in feedback
    assert '- "Frase ruim 2"' in feedback
    
    # 2. Test when retry_idx = 2 (dimensions should be present, up to 2; slop style NOT present)
    feedback_r2 = format_eval_feedback(eval_data, retry_idx=2)
    assert "### DEFICIÊNCIAS NAS DIMENSÕES NARRATIVAS:" in feedback_r2
    # Failing dimensions (score < 7): voice_adherence (5.0), prose_quality (5.5), character_voice (6.5).
    # Sorted: voice_adherence (5.0), prose_quality (5.5), character_voice (6.5).
    # Since retry_idx = 2 is between 2 and 4, we take the top 2 failing dimensions: voice_adherence and prose_quality.
    assert "Dimensão 'voice_adherence' (Nota 5.0):" in feedback_r2
    assert "Ponto fraco: \"Frase de IA\"" in feedback_r2
    assert "Correção sugerida: Melhorar tom" in feedback_r2
    
    assert "Dimensão 'prose_quality' (Nota 5.5):" in feedback_r2
    # Wait, the fallback/dimension parser checks dimension "fix" and "weakest_moment"
    # For prose_quality, the structure is:
    # "prose_quality": {"score": 5.5, "fix": "Encurtar frases", "weakest_sentence": "Sentence weak"}
    # Wait, the dimension dict in evaluate_chapter uses "weakest_moment" for most, but prose_quality might use "weakest_moment" or "weakest_sentence"?
    # Let's check format_eval_feedback:
    # moment = dim_data.get("weakest_moment", "")
    # Since prose_quality in our dict does not have weakest_moment (it has weakest_sentence), "moment" will be empty. Let's verify that's handled.
    assert "Dimensão 'character_voice'" not in feedback_r2  # Only top 2
    
    # Slop style should NOT be present for retry_idx=2
    assert "### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):" not in feedback_r2
    
    # 3. Test when retry_idx = 3 (dimensions present, slop style present)
    feedback_r3 = format_eval_feedback(eval_data, retry_idx=3)
    assert "### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):" in feedback_r3
    assert "Palavras suspeitas usadas: 'synergy' (usado 3 vezes)" in feedback_r3
    assert "Tiques estruturais de IA detectados: 'not only' (usado 2 vezes)" in feedback_r3
    assert "Clichês/tells de IA detectados: 'help but' (usado 1 vezes)" in feedback_r3
    assert "Densidade excessiva de travessões: 18.5" in feedback_r3
