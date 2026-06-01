#!/usr/bin/env python3
"""
tests/test_editorial.py — Unit tests for the run_editorial.py orchestrator,
Markdown loading, hybrid classification, and cascading continuity warning injection.
"""

import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to python path to import run_editorial
sys.path.insert(0, str(Path(__file__).parent.parent))

import run_editorial
from run_editorial import (
    load_editorial_markdown,
    load_editorial_markdown_fallback,
    classify_brief_with_ai,
    parse_score,
)

@pytest.fixture
def mock_editorial_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "editorial.md"
    monkeypatch.setattr(run_editorial, "EDITORIAL_MD", temp_file)
    return temp_file

def test_load_editorial_markdown_creates_default(mock_editorial_file):
    # Verify that if editorial.md does not exist, it gets created with default template
    # and exits gracefully
    with pytest.raises(SystemExit) as excinfo:
        load_editorial_markdown()
        
    assert excinfo.value.code == 0
    assert mock_editorial_file.exists()
    
    # Read created template
    content = mock_editorial_file.read_text(encoding="utf-8")
    assert "# Diretrizes Gerais" in content
    assert "# Capítulo 11" in content
    assert "# Capítulo 17" in content

@patch("llm.call_llm")
def test_load_editorial_markdown_loads_via_llm(mock_call_llm, mock_editorial_file):
    markdown_content = (
        "# Diretrizes Gerais\n"
        "Test notes\n\n"
        "# Capítulo 10\n"
        "Test brief\n"
    )
    mock_editorial_file.write_text(markdown_content, encoding="utf-8")
    
    mock_response = """
    {
      "general_notes": "Test notes",
      "chapters": {
        "10": {
          "brief": "Test brief",
          "type": "continuity_breaking",
          "affects_downstream": [11, 12]
        }
      }
    }
    """
    mock_call_llm.return_value = mock_response
    
    loaded = load_editorial_markdown()
    
    assert loaded["general_notes"] == "Test notes"
    assert loaded["chapters"][10]["brief"] == "Test brief"
    assert loaded["chapters"][10]["type"] == "continuity_breaking"
    assert loaded["chapters"][10]["affects_downstream"] == [11, 12]
    mock_call_llm.assert_called_once()

@patch("llm.call_llm")
def test_load_editorial_markdown_llm_fallback_on_exception(mock_call_llm, mock_editorial_file):
    markdown_content = (
        "# Diretrizes Gerais\n"
        "Test notes fallback\n\n"
        "# Capítulo 10\n"
        "Test brief fallback\n"
        "affects_downstream: 11, 12\n"
    )
    mock_editorial_file.write_text(markdown_content, encoding="utf-8")
    
    # Make LLM call raise an exception to force fallback
    mock_call_llm.side_effect = Exception("API Timeout")
    
    loaded = load_editorial_markdown()
    
    # Verify we successfully fell back to regex parsing
    assert loaded["general_notes"] == "Test notes fallback"
    assert loaded["chapters"][10]["brief"] == "Test brief fallback"
    assert loaded["chapters"][10]["type"] == "continuity_breaking"
    assert loaded["chapters"][10]["affects_downstream"] == [11, 12]
    mock_call_llm.assert_called_once()

def test_load_editorial_markdown_fallback_direct():
    markdown_content = (
        "# Guidelines\n"
        "Style guidelines here\n\n"
        "# Chapter 5\n"
        "Punctual edit style\n\n"
        "# Cap 8\n"
        "Structural changes\n"
        "affects: 9, 10\n"
    )
    
    loaded = load_editorial_markdown_fallback(markdown_content)
    
    assert loaded["general_notes"] == "Style guidelines here"
    assert loaded["chapters"][5]["brief"] == "Punctual edit style"
    assert loaded["chapters"][5]["type"] == "punctual"
    assert loaded["chapters"][8]["brief"] == "Structural changes"
    assert loaded["chapters"][8]["type"] == "continuity_breaking"
    assert loaded["chapters"][8]["affects_downstream"] == [9, 10]

@patch("llm.call_llm")
def test_classify_brief_with_ai_punctual(mock_call):
    response_json = """
    {
      "type": "punctual",
      "affects_downstream": [],
      "criticism": "This is a direct criticism."
    }
    """
    mock_call.return_value = response_json
    
    result = classify_brief_with_ai(11, "Modify Padre Tomás dialogue.")
    assert result["type"] == "punctual"
    assert result["affects_downstream"] == []
    assert result["criticism"] == "This is a direct criticism."

@patch("llm.call_llm")
def test_classify_brief_with_ai_continuity_breaking(mock_call):
    response_json = """
    {
      "type": "continuity_breaking",
      "affects_downstream": [18, 19, 20],
      "criticism": "This introduces a key item."
    }
    """
    mock_call.return_value = response_json
    
    result = classify_brief_with_ai(17, "Helena gives Elisa a physical key.")
    assert result["type"] == "continuity_breaking"
    assert result["affects_downstream"] == [18, 19, 20]
    assert result["criticism"] == "This introduces a key item."

def test_parse_score():
    stdout = "Evaluating chapter... \noverall_score: 7.23 \nProse: 8"
    assert parse_score(stdout, "overall_score") == 7.23
    assert parse_score(stdout, "novel_score") == 0.0

@patch("run_editorial.classify_brief_with_ai")
@patch("run_editorial.run_tool")
@patch("builtins.input")
@patch("llm.call_llm")
def test_run_editorial_abort(mock_call_llm, mock_input, mock_run_tool, mock_classify, mock_editorial_file, monkeypatch):
    markdown_content = (
        "# Diretrizes Gerais\n"
        "Test notes\n\n"
        "# Capítulo 10\n"
        "Punctual edit\n"
    )
    mock_editorial_file.write_text(markdown_content, encoding="utf-8")
    
    # Mock LLM parser
    mock_call_llm.return_value = """
    {
      "general_notes": "Test notes",
      "chapters": {
        "10": {
          "brief": "Punctual edit",
          "type": "punctual",
          "affects_downstream": []
        }
      }
    }
    """
    
    # Mock AI returning punctual
    mock_classify.return_value = {
        "type": "punctual",
        "affects_downstream": [],
        "criticism": "Test criticism"
    }
    
    # Mock user input to abort ('n')
    mock_input.return_value = "n"
    
    # Run the pipeline
    run_editorial.run_editorial()
    
    # Verify we did NOT run the gen_revision tool since user aborted
    for call in mock_run_tool.call_args_list:
        cmd = call[0][0]
        assert "gen_revision.py" not in cmd

@patch("run_editorial.classify_brief_with_ai")
@patch("run_editorial.run_tool")
@patch("builtins.input")
@patch("llm.call_llm")
@patch("run_editorial.git_add_commit")
@patch("run_editorial.git_reset_hard")
def test_run_editorial_dynamic_timeouts(mock_git_reset, mock_git_commit, mock_call_llm, mock_input, mock_run_tool, mock_classify, mock_editorial_file, monkeypatch):
    # Mock env variables
    monkeypatch.setenv("AUTOBOOK_PIPELINE_TIMEOUT", "4000")
    monkeypatch.setenv("AUTOBOOK_REVISION_TIMEOUT", "5000")
    monkeypatch.setenv("AUTOBOOK_EVAL_TIMEOUT", "2500")
    
    markdown_content = (
        "# Capítulo 10\n"
        "Test brief\n"
    )
    mock_editorial_file.write_text(markdown_content, encoding="utf-8")
    
    # Mock LLM parser
    mock_call_llm.return_value = """
    {
      "general_notes": "",
      "chapters": {
        "10": {
          "brief": "Test brief",
          "type": "punctual",
          "affects_downstream": []
        }
      }
    }
    """
    
    # Mock AI classification
    mock_classify.return_value = {
        "type": "punctual",
        "affects_downstream": [],
        "criticism": "Good"
    }
    
    # Mock user input to proceed
    mock_input.return_value = "y"
    
    # Mock run_tool to return a CompletedProcess-like object with stdout
    mock_pre_eval = MagicMock()
    mock_pre_eval.stdout = "overall_score: 8.5"
    mock_run_tool.return_value = mock_pre_eval
    
    # Run the pipeline
    run_editorial.run_editorial()
    
    # Verify run_tool was called with the specific granular timeouts
    eval_call_count = 0
    revision_call_count = 0
    for call in mock_run_tool.call_args_list:
        cmd = call[0][0]
        kwargs = call[1]
        if "evaluate.py" in cmd:
            assert kwargs["timeout"] == 2500
            eval_call_count += 1
        elif "gen_revision.py" in cmd:
            assert kwargs["timeout"] == 5000
            revision_call_count += 1
            
    assert eval_call_count == 2
    assert revision_call_count == 1
