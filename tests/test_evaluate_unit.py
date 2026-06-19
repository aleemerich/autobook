#!/usr/bin/env python3
"""
tests/test_evaluate_unit.py — Unit tests for the evaluate.py mechanical slop checker.
"""

import os
import pytest
from unittest.mock import patch
from evaluate import slop_score

@pytest.fixture(autouse=True)
def force_english_env():
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "EN"}):
        yield


def test_clean_text():
    """Ensures natural, well-varied human prose has a 0.0 slop penalty."""
    text = (
        "The wind was cold. It carried the smell of wet earth from the valley below, "
        "whipping through the tall pines. Cass pulled his woolen cloak tighter around "
        "his shoulders and stepped forward. The path was narrow. One slip, and he would "
        "tumble into the dark canyon. He had to reach the village before nightfall."
    )
    result = slop_score(text)
    assert result["slop_penalty"] == 0.0
    assert len(result["tier1_hits"]) == 0
    assert result["telling_violations"] == 0


def test_tier1_banned_words():
    """Ensures typical AI words like 'delve' or 'tapestry' trigger appropriate penalties."""
    text = "We need to delve into the tapestry of this multifaceted project and utilize our synergy."
    result = slop_score(text)
    
    # Check that the banned words were caught
    caught_words = [word for word, count in result["tier1_hits"]]
    assert "delve" in caught_words
    assert "tapestry" in caught_words
    assert "multifaceted" in caught_words
    assert "utilize" in caught_words
    assert result["slop_penalty"] > 0.0


def test_fiction_ai_tells():
    """Ensures AI prose clichés like 'let out a breath' or 'couldn't help but feel' are caught."""
    text = (
        "He let out a breath he didn't realize he was holding. "
        "She couldn't help but feel a wave of fear wash over her."
    )
    result = slop_score(text)
    
    assert result["slop_penalty"] > 0.0
    caught_tells = [pattern for pattern, count in result["fiction_ai_tells"]]
    # The patterns are matched as substrings
    assert any("breath" in p or "holding" in p for p in caught_tells)
    assert any("help but feel" in p for p in caught_tells)


def test_ptbr_foreign_language_leftovers():
    """Ensures configured English leftovers are penalized in PT-BR prose."""
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "PT-BR"}):
        result = slop_score("Ele bateu o inside da bochecha antes de responder.")

    assert result["foreign_language_hits"] == [("inside", 1)]
    assert result["slop_penalty"] >= 2.0


def test_em_dash_overuse():
    """Ensures excessive em dashes trigger a penalty."""
    # A short text with excessive em-dashes to inflate density
    text = "This — is — a — very — fragmented — sentence — indeed."
    result = slop_score(text)
    
    assert result["em_dash_density"] > 15
    assert result["slop_penalty"] > 0.0


def test_sentence_uniformity():
    """Ensures uniform sentence lengths (monotone rhythm) trigger a penalty."""
    # Every sentence is exactly 4 words long (perfectly uniform, coefficient of variation = 0)
    text = "This is a book. That is a cat. She is very sad. He is very mad."
    result = slop_score(text)
    
    assert result["sentence_length_cv"] < 0.3
    assert result["slop_penalty"] > 0.0


def test_parse_json_response_resilience():
    """Verifies evaluate.parse_json_response resilience against markdown, commas, and unescaped quotes."""
    from evaluate import parse_json_response
    
    raw_response = """```json
    {
      "voice_adherence": {"score": 8.5, "note": "Valid structure"},
      "prose_quality": {"score": 7.0, "weakest_sentence": "This is a "nested string" with some quotes, and a trailing comma", "fix": "Rewrite it"},
      "three_weakest_sentences": [
        "First weak",
        "Second weak",
      ]
    }
    ```"""
    
    res = parse_json_response(raw_response)
    assert res["voice_adherence"]["score"] == 8.5
    assert "nested string" in res["prose_quality"]["weakest_sentence"]
    assert len(res["three_weakest_sentences"]) == 2
    assert res["three_weakest_sentences"][1] == "Second weak"


def test_validate_and_repair_json_success():
    """Ensures validate_and_repair_json parses correct JSON properly."""
    from evaluate import validate_and_repair_json
    raw_text = '{"overall_score": 8.0, "top_3_revisions": ["rev1"]}'
    res = validate_and_repair_json(raw_text, "overall_score")
    assert res is not None
    assert res["overall_score"] == 8.0
    assert res["top_3_revisions"] == ["rev1"]
    assert "canon_compliance" in res


def test_validate_and_repair_json_regex_fallback():
    """Ensures validate_and_repair_json parses broken JSON or plain text with key matching via regex."""
    from evaluate import validate_and_repair_json
    raw_text = 'This is invalid JSON but "overall_score" : 7.5 and "weakest_moment": "test comment"'
    res = validate_and_repair_json(raw_text, "overall_score")
    assert res is not None
    assert res["overall_score"] == 7.5
    assert res["weakest_moment"] == "test comment"
    assert res["top_3_revisions"] == []


def test_validate_and_repair_json_prefers_embedded_required_json():
    """Uses the final valid object when a model explains before returning JSON."""
    from evaluate import validate_and_repair_json
    raw_text = (
        'First I will think using an example {"schema": {"overall": "ignored"}}.\n'
        'Final answer:\n'
        '{"overall_score": 8.0, "top_3_revisions": ["fix"], '
        '"canon_compliance": {"score": 8, "violations": []}}'
    )
    res = validate_and_repair_json(raw_text, "overall_score")
    assert res is not None
    assert res["overall_score"] == 8.0
    assert res["top_3_revisions"] == ["fix"]


def test_debug_response_excerpt_truncates_long_text():
    from evaluation.json_utils import _debug_response_excerpt

    text = "a" * 2050

    excerpt = _debug_response_excerpt(text, limit=20)

    assert excerpt == "a" * 20 + "\n...[truncated 2030 chars]"


def test_chapter_evaluation_prompts_format_after_output_contract():
    import evaluate

    format_args = {
        "voice": "VOICE",
        "world": "WORLD",
        "characters": "CHARACTERS",
        "canon": "CANON",
        "chapter_outline": "OUTLINE",
        "prev_chapter_tail": "PREV",
        "chapter_text": "CHAPTER",
    }

    for template in [
        evaluate.CHAPTER_PROMPT,
        evaluate.CHAPTER_PROMPT_REDUCED,
        evaluate.CHAPTER_PROMPT_MINIMAL,
    ]:
        rendered = template.format(**format_args)
        assert "The first character of your response must be `{`." in rendered
        assert "The final character of your response must be `}`." in rendered


def test_extract_chapter_outline_entry_accepts_portuguese_headings():
    from evaluate import extract_chapter_outline_entry
    outline = """
## Ato I

### Capítulo 1 - A Primeira Letra
Resumo do primeiro capitulo.

### Capítulo 2 – O Livro Vivo
Resumo do segundo capitulo.

### Capítulo 3: O Nome Que Sobra
Resumo do terceiro capitulo.
"""
    entry = extract_chapter_outline_entry(outline, 2)
    assert "O Livro Vivo" in entry
    assert "Resumo do segundo" in entry
    assert "O Nome Que Sobra" not in entry


def test_validate_and_repair_json_failure():
    """Ensures validate_and_repair_json returns None if the key is not present."""
    from evaluate import validate_and_repair_json
    raw_text = '{"some_other_key": 8.0}'
    res = validate_and_repair_json(raw_text, "overall_score")
    assert res is None
