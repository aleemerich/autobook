#!/usr/bin/env python3
"""
tests/test_editorial.py — Unit tests for the run_editorial.py orchestrator, Markdown loading, hybrid classification, and cascading continuity warning injection.
"""

import sys
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to python path to import run_editorial
sys.path.insert(0, str(Path(__file__).parent.parent))

import run_editorial
from run_editorial import load_editorial_markdown, classify_brief_with_ai, parse_score

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

def test_load_editorial_markdown_loads_existing(mock_editorial_file):
    markdown_content = (
        "# Diretrizes Gerais\n"
        "Test notes\n\n"
        "# Capítulo 10\n"
        "Test brief\n"
        "affects_downstream: 11, 12\n"
    )
    mock_editorial_file.write_text(markdown_content, encoding="utf-8")
    
    loaded = load_editorial_markdown()
    assert "Test notes" in loaded["general_notes"]
    assert "Test brief" in loaded["chapters"][10]["brief"]
    assert loaded["chapters"][10]["affects_downstream"] == [11, 12]
    assert loaded["chapters"][10]["type"] == "continuity_breaking"

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
def test_run_editorial_abort(mock_input, mock_run_tool, mock_classify, mock_editorial_file, monkeypatch):
    markdown_content = (
        "# Diretrizes Gerais\n"
        "Test notes\n\n"
        "# Capítulo 10\n"
        "Punctual edit\n"
    )
    mock_editorial_file.write_text(markdown_content, encoding="utf-8")
    
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
