#!/usr/bin/env python3
"""
tests/test_batch_generators_unit.py — Unit tests for Phase 5 batch and media migrated scripts.
Verifies that all call_writer/call_judge/call_review_llm/call_claude/call_model functions correctly
delegate to llm.call_llm with the expected configuration parameters.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def force_english_env():
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "EN"}):
        yield

@patch("llm.call_llm")
def test_gen_revision_call_writer(mock_call_llm):
    """Verifies gen_revision.call_writer correctly routes to call_llm with appropriate temperature and is_judge=False."""
    from gen_revision import call_writer
    mock_call_llm.return_value = "Mocked Revised Chapter Prose"
    
    prompt = "Test revision prompt"
    res = call_writer(prompt)
    
    assert res == "Mocked Revised Chapter Prose"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "revision brief" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.8
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_reader_panel_call_reader(mock_call_llm):
    """Verifies reader_panel.call_reader correctly routes to call_llm with is_judge=True."""
    from reader_panel import call_reader
    mock_call_llm.return_value = '{"momentum_loss": "none", "earned_ending": "yes"}'
    
    res = call_reader("editor", "Arc summary text")
    
    assert "momentum_loss" in res
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert "Arc summary text" in called_kwargs["prompt"]
    assert "senior fiction editor" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.7
    assert called_kwargs["is_judge"] is True

@patch("llm.call_llm")
def test_review_call_review_llm(mock_call_llm):
    """Verifies review.call_review_llm correctly routes to call_llm with is_review=True."""
    from review import call_review_llm
    mock_call_llm.return_value = "Mocked deep review content"
    
    prompt = "Test manuscript text"
    res = call_review_llm(prompt)
    
    assert res == "Mocked deep review content"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "literary critic" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.3
    assert called_kwargs["is_review"] is True

@patch("llm.call_llm")
def test_gen_art_directions_call_claude(mock_call_llm):
    """Verifies gen_art_directions.call_claude correctly routes to call_llm."""
    from gen_art_directions import call_claude
    mock_call_llm.return_value = "Mocked art directions response"
    
    prompt = "Test art direction prompt"
    res = call_claude(prompt)
    
    assert res == "Mocked art directions response"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "art director" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.9
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_gen_art_call_claude(mock_call_llm):
    """Verifies gen_art.call_claude correctly routes to call_llm."""
    from gen_art import call_claude
    mock_call_llm.return_value = "Mocked visual style JSON"
    
    prompt = "Test visual style prompt"
    res = call_claude(prompt)
    
    assert res == "Mocked visual style JSON"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "art director" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.3
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_gen_audiobook_script_call_claude(mock_call_llm):
    """Verifies gen_audiobook_script.call_claude correctly routes to call_llm."""
    from gen_audiobook_script import call_claude
    mock_call_llm.return_value = "Mocked audiobook script JSON"
    
    prompt = "Test audiobook script parsing prompt"
    res = call_claude(prompt)
    
    assert res == "Mocked audiobook script JSON"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "audiobook producer" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.1
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_compare_chapters_call_judge(mock_call_llm):
    """Verifies compare_chapters.call_judge correctly routes to call_llm with is_judge=True."""
    from compare_chapters import call_judge
    mock_call_llm.return_value = "Mocked comparison winner details"
    
    prompt = "Test matchup comparison prompt"
    res = call_judge(prompt)
    
    assert res == "Mocked comparison winner details"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "literary editor comparing two chapters" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.2
    assert called_kwargs["is_judge"] is True

@patch("llm.call_llm")
def test_build_outline_call_model(mock_call_llm):
    """Verifies build_outline.call_model correctly routes to call_llm with is_judge=True."""
    from build_outline import call_model
    mock_call_llm.return_value = '{"title": "Morning Pitch", "location": "Furnace District"}'
    
    res = call_model("Test outlines analysis prompt")
    
    assert "title" in res
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == "Test outlines analysis prompt"
    assert "structured outline entries" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.1
    assert called_kwargs["is_judge"] is True

def test_parse_json_response_resilience():
    """Verifies build_outline.parse_json_response resilience against markdown, commas, and unescaped quotes."""
    from build_outline import parse_json_response
    
    # Test case 1: markdown fences, trailing commas, and unescaped internal double quotes
    raw_response = """```json
    {
      "title": "Test Title",
      "summary": "This is a "nested string" with some quotes, and a trailing comma",
      "beats": [
        "First beat",
        "Second beat",
      ]
    }
    ```"""
    
    res = parse_json_response(raw_response)
    assert res["title"] == "Test Title"
    assert "nested string" in res["summary"]
    assert len(res["beats"]) == 2
    assert res["beats"][1] == "Second beat"

@patch("llm.call_llm")
def test_build_arc_summary_call_writer(mock_call_llm):
    """Verifies build_arc_summary.call_writer correctly routes to call_llm."""
    from build_arc_summary import call_writer
    mock_call_llm.return_value = "Mocked condensed chapter summary"
    
    prompt = "Test chapter text to summarize"
    res = call_writer(prompt)
    
    assert res == "Mocked condensed chapter summary"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "summarize novel chapters precisely" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.1
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_adversarial_edit_call_judge(mock_call_llm):
    """Verifies adversarial_edit.call_judge correctly routes to call_llm with is_judge=True."""
    from adversarial_edit import call_judge
    mock_call_llm.return_value = "Mocked ruthless editor JSON"
    
    prompt = "Test adversarial cuts prompt"
    res = call_judge(prompt)
    
    assert res == "Mocked ruthless editor JSON"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "ruthless literary editor" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.3
    assert called_kwargs["is_judge"] is True
