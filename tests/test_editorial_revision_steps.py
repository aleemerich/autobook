#!/usr/bin/env python3
"""
tests/test_editorial_revision_steps.py — Unit tests for the editorial revision helpers.
"""

import json
from pathlib import Path
import pytest
from unittest.mock import patch
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
from pipelines.editorial_revision_steps.revision import (
    build_initial_brief,
    build_corrective_brief,
    write_temp_brief,
    remove_temp_brief,
    execute_gen_revision,
    is_quality_target_reached,
    is_better_than_fallback,
    commit_revised_chapter,
    run_final_maintenance,
)
from pipelines.editorial_revision_steps import (
    load_editorial_config,
    get_retry_temperature,
    load_editorial_markdown_fallback,
    load_editorial_markdown,
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


@patch("pipelines.editorial_revision.evaluate_chapter")
@patch("pipelines.editorial_revision_steps.revision.subprocess.run")
def test_execute_editorial_step_flow(mock_sub_run, mock_evaluate, tmp_path, monkeypatch):
    import pipelines.editorial_revision
    from pipelines.editorial_revision import ExecuteEditorialStep

    # 1. Setup temporary directories and files
    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir()

    # Create valid chapter files out of order
    (chapters_dir / "ch_02.md").write_text("Chapter 2 content", encoding="utf-8")
    (chapters_dir / "ch_01.md").write_text("Chapter 1 content", encoding="utf-8")
    (chapters_dir / "ch_10.md").write_text("Chapter 10 content", encoding="utf-8")

    # Create invalid file names/extensions
    (chapters_dir / "ch_x.md").write_text("invalid name", encoding="utf-8")
    (chapters_dir / "ch_05.txt").write_text("invalid ext", encoding="utf-8")
    (chapters_dir / "outline.md").write_text("outline", encoding="utf-8")

    # 2. Patch CHAPTERS_DIR and BASE_DIR using monkeypatch
    monkeypatch.setattr(pipelines.editorial_revision, "CHAPTERS_DIR", chapters_dir)
    monkeypatch.setattr(pipelines.editorial_revision, "BASE_DIR", tmp_path)

    # Mock evaluations to succeed immediately (score 8.0, slop penalty 0)
    mock_evaluate.return_value = {
        "overall_score": 8.0,
        "slop": {"slop_penalty": 0.0}
    }

    # 3. Test: Filtros de capítulos selecionados continuam funcionando
    step = ExecuteEditorialStep()
    # We specify selection as [10, 1] in context
    context = {
        "chapters_briefs": {
            1: {"brief": "Ch 1 brief"},
            2: {"brief": "Ch 2 brief"},
            10: {"brief": "Ch 10 brief"},
        },
        "general_notes": "Some general notes",
        "chapters": [10, 1]
    }

    step.run(context)

    # Verify that only chapter 10 and chapter 1 were evaluated, NOT chapter 2, and not the invalid files
    called_chapters = [args[0] for args, kwargs in mock_evaluate.call_args_list]
    assert 10 in called_chapters
    assert 1 in called_chapters
    assert 2 not in called_chapters

    # Verify that subprocess was called for gen_revision.py for 10 and 1
    assert mock_sub_run.call_count > 0

    # 4. Test: a pipeline usa a ordenação numérica correta de capítulos (quando não selecionado pelo contexto)
    mock_evaluate.reset_mock()
    mock_sub_run.reset_mock()

    # Remove selection from context so it falls back to briefs keys, sorted numerically
    context_fallback = {
        "chapters_briefs": {
            10: {"brief": "Ch 10 brief"},
            2: {"brief": "Ch 2 brief"},
            1: {"brief": "Ch 1 brief"},
        },
        "general_notes": "Some general notes",
        "chapters": None
    }

    step.run(context_fallback)

    # When target_chapters is not specified, it falls back to:
    # sorted(list(chapters_briefs.keys())) -> [1, 2, 10]
    called_chapters_fallback = []
    for args, kwargs in mock_evaluate.call_args_list:
        ch = args[0]
        if not called_chapters_fallback or called_chapters_fallback[-1] != ch:
            called_chapters_fallback.append(ch)

    assert called_chapters_fallback == [1, 2, 10]


def test_build_initial_brief():
    brief = "Do X."
    general = "Rule Y."
    content = build_initial_brief(brief, general)
    assert "# DIRETIVAS EDITORIAIS" in content
    assert "Do X." in content
    assert "## DIRETIVAS GERAIS" in content
    assert "Rule Y." in content


def test_build_corrective_brief():
    content = build_corrective_brief(
        ch_num=5,
        retry_idx=2,
        feedback_str="Feedback description",
        brief="Original brief",
        general_notes="General notes"
    )
    assert "# DIRETIVAS DE RECORREÇÃO - CAPÍTULO 5 (TENTATIVA 3)" in content
    assert "Feedback description" in content
    assert "Original brief" in content
    assert "General notes" in content


def test_write_and_remove_temp_brief(tmp_path):
    brief_path = tmp_path / "temp_brief.txt"
    assert not brief_path.exists()

    write_temp_brief(brief_path, "Brief content")
    assert brief_path.exists()
    assert brief_path.read_text(encoding="utf-8") == "Brief content"

    remove_temp_brief(brief_path)
    assert not brief_path.exists()

    # Check that remove is safe if file doesn't exist
    remove_temp_brief(brief_path)  # should not raise any error


@patch("pipelines.editorial_revision_steps.revision.subprocess.run")
def test_execute_gen_revision(mock_sub_run, tmp_path):
    brief_path = tmp_path / "brief.txt"
    execute_gen_revision(ch_num=3, brief_path=brief_path, temperature=0.75, base_dir=tmp_path)
    mock_sub_run.assert_called_once()
    args, kwargs = mock_sub_run.call_args
    cmd = args[0]
    assert "gen_revision.py" in cmd
    assert "3" in cmd
    assert str(brief_path) in cmd
    assert "--temperature" in cmd
    assert "0.75" in cmd
    assert kwargs["cwd"] == str(tmp_path)


def test_is_quality_target_reached():
    # Success: post >= pre, post >= 7.0, slop == 0.0
    assert is_quality_target_reached(7.5, 7.0, 0.0) is True
    assert is_quality_target_reached(7.0, 7.0, 0.0) is True
    assert is_quality_target_reached(6.9, 6.0, 0.0) is False  # post < 7.0
    assert is_quality_target_reached(8.0, 8.5, 0.0) is False  # post < pre
    assert is_quality_target_reached(8.0, 7.0, 1.0) is False  # slop != 0.0


def test_is_better_than_fallback():
    # Better if higher score
    assert is_better_than_fallback(8.0, 7.5, 0.0, 0.0) is True
    assert is_better_than_fallback(7.0, 7.5, 0.0, 0.0) is False
    # Better if same score but lower slop
    assert is_better_than_fallback(7.5, 7.5, 0.5, 1.0) is True
    assert is_better_than_fallback(7.5, 7.5, 1.0, 0.5) is False
    # Not better if same score and same slop
    assert is_better_than_fallback(7.5, 7.5, 0.5, 0.5) is False


@patch("pipelines.editorial_revision_steps.revision.subprocess.run")
def test_commit_revised_chapter(mock_sub_run, tmp_path):
    commit_revised_chapter(ch_num=4, pre_score=6.0, final_score=8.5, base_dir=tmp_path)
    # 3 calls: git add, git commit, git push
    assert mock_sub_run.call_count == 3

    # 1. git add
    add_args, add_kwargs = mock_sub_run.call_args_list[0]
    assert add_args[0] == ["git", "add", "chapters/ch_04.md"]
    assert add_kwargs["cwd"] == str(tmp_path)

    # 2. git commit
    commit_args, commit_kwargs = mock_sub_run.call_args_list[1]
    assert commit_args[0] == ["git", "commit", "-m", "editorial: revised ch04 (6.0 -> 8.5)"]

    # 3. git push
    push_args, push_kwargs = mock_sub_run.call_args_list[2]
    assert push_args[0] == ["git", "push"]


@patch("pipelines.editorial_revision_steps.revision.subprocess.run")
def test_run_final_maintenance(mock_sub_run, tmp_path):
    # Setup dummy paths
    legacy_dir = tmp_path / "legacy"
    legacy_dir.mkdir()
    (legacy_dir / "build_outline.py").touch()

    verify_script = tmp_path / "verify_continuity.py"
    verify_script.touch()

    run_final_maintenance(tmp_path)
    # Should run both build_outline.py and verify_continuity.py
    assert mock_sub_run.call_count == 2

    call1_args = mock_sub_run.call_args_list[0][0][0]
    assert any("build_outline.py" in arg for arg in call1_args)

    call2_args = mock_sub_run.call_args_list[1][0][0]
    assert any("verify_continuity.py" in arg for arg in call2_args)


def test_load_editorial_config():
    config = load_editorial_config()
    assert isinstance(config, dict)
    assert "retry_temp_map" in config
    assert "feedback_labels" in config


def test_get_retry_temperature():
    assert get_retry_temperature(1) == 0.6
    assert get_retry_temperature(2) == 0.6
    assert get_retry_temperature(3) == 0.7
    assert get_retry_temperature(4) == 0.9
    assert get_retry_temperature(5) == 0.5
    assert get_retry_temperature(99) == 0.8


def test_load_editorial_markdown_fallback():
    markdown_text = """
# Geral
Alguma nota geral.

# Capítulo 1
Este é o brief do cap 1.
affects_downstream: 2, 3

# Cap 2
Brief cap 2.
"""
    res = load_editorial_markdown_fallback(markdown_text)
    assert res["general_notes"] == "Alguma nota geral."
    assert res["chapters"][1]["brief"] == "Este é o brief do cap 1."
    assert res["chapters"][1]["type"] == "continuity_breaking"
    assert res["chapters"][1]["affects_downstream"] == [2, 3]
    assert res["chapters"][2]["brief"] == "Brief cap 2."
    assert res["chapters"][2]["type"] == "punctual"


@patch("pipelines.editorial_revision_steps.parsing.call_llm")
def test_load_editorial_markdown_success(mock_call_llm, tmp_path, monkeypatch):
    import pipelines.editorial_revision_steps.parsing

    # 1. Setup mock file
    editorial_file = tmp_path / "editorial.md"
    editorial_file.write_text("# Geral\nNota", encoding="utf-8")

    monkeypatch.setattr(pipelines.editorial_revision_steps.parsing, "EDITORIAL_MD", editorial_file)

    # Mock call_llm response
    json_response = {
        "general_notes": "Nota geral mock",
        "chapters": {
            "3": {
                "brief": "Capítulo 3 brief mock",
                "type": "punctual",
                "affects_downstream": []
            }
        }
    }
    mock_call_llm.return_value = json.dumps(json_response)

    res = load_editorial_markdown()
    assert res["general_notes"] == "Nota geral mock"
    assert res["chapters"][3]["brief"] == "Capítulo 3 brief mock"


@patch("pipelines.editorial_revision.get_retry_temperature")
@patch("pipelines.editorial_revision.evaluate_chapter")
@patch("pipelines.editorial_revision_steps.revision.subprocess.run")
def test_execute_editorial_step_uses_get_retry_temperature(mock_sub_run, mock_evaluate, mock_get_temp, tmp_path, monkeypatch):
    import pipelines.editorial_revision
    from pipelines.editorial_revision import ExecuteEditorialStep

    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir()
    (chapters_dir / "ch_01.md").write_text("Chapter 1 content", encoding="utf-8")

    monkeypatch.setattr(pipelines.editorial_revision, "CHAPTERS_DIR", chapters_dir)
    monkeypatch.setattr(pipelines.editorial_revision, "BASE_DIR", tmp_path)

    mock_evaluate.side_effect = [
        {"overall_score": 5.0, "slop": {"slop_penalty": 1.0}}, # baseline
        {"overall_score": 5.0, "slop": {"slop_penalty": 1.0}}, # attempt 1
        {"overall_score": 6.0, "slop": {"slop_penalty": 1.0}}, # corrective retry 1
        {"overall_score": 8.0, "slop": {"slop_penalty": 0.0}}, # corrective retry 2
    ]

    mock_get_temp.side_effect = [0.44, 0.55]

    step = ExecuteEditorialStep()
    context = {
        "chapters_briefs": {
            1: {"brief": "Ch 1 brief"},
        },
        "general_notes": "General notes",
        "chapters": [1]
    }

    monkeypatch.setenv("NUM_EDITORIAL_RETRIES", "3")

    step.run(context)

    mock_get_temp.assert_any_call(1)
    mock_get_temp.assert_any_call(2)
    assert mock_get_temp.call_count == 2
