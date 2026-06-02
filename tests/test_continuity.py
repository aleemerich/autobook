#!/usr/bin/env python3
"""
tests/test_continuity.py — Unit tests for the global timeline and continuity validator.
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Include root dir to run tests
ROOT_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT_DIR))

from verify_continuity import parse_outline, run_continuity_validation

@pytest.fixture
def temp_outline(tmp_path):
    """Fixture to generate a temporary outline.md file."""
    outline_file = tmp_path / "outline.md"
    content = """# THE SECOND SON OF THE HOUSE OF BELLS
## Chapter Outline (reflects actual novel as-written)

**2 chapters, 5,000 words**

---

### Ch 1: Elisa's Discovery
**2500 words** | **Location:** ETH Office HPF 3.17
- **Characters:** Elisa, Marcus
- **Try-fail cycle:** yes-but
- **Emotional arc:** Elisa transitions from numb curiosity to sharp anxiety.

**Summary:** Elisa accesses the CERN 2018 backup data in the office safe and finds a recurring anomaly. Marcus warns her about the risks.

**Beats:**
1. Elisa opens the safe and runs the comparison scripts.
2. Marcus enters and expresses disbelief.
3. Elisa walks home to Hottingen through the cold night.

**Plants:**
- The key left by Helena.

**Chapter question:** What is the origin of the thermal fluctuation?

---

### Ch 2: The Silent Apartment
**2500 words** | **Location:** Elisa's Apartment, Hottingen
- **Characters:** Elisa
- **Try-fail cycle:** no-and
- **Emotional arc:** Terror turns into determined focus.

**Summary:** Elisa arrives at her apartment and finds the door unlocked. She receives a threatening message on her phone.

**Beats:**
1. Elisa walks up the stairs to her 5th floor flat.
2. She checks the rooms but finds no one.
3. Her phone buzzes with a private number warning.

**Harvests:**
- The key left by Helena fits the drawer lock.

**Chapter question:** Who sent the warning message?

---
"""
    outline_file.write_text(content, encoding="utf-8")
    return outline_file

def test_parse_outline(temp_outline):
    """Ensures that verify_continuity correctly parses outline.md structures."""
    entries = parse_outline(temp_outline)
    assert len(entries) == 2
    
    # Check Chapter 1
    ch1 = entries[0]
    assert ch1["num"] == 1
    assert ch1["title"] == "Elisa's Discovery"
    assert ch1["location"] == "ETH Office HPF 3.17"
    assert "Elisa" in ch1["characters"]
    assert "Marcus" in ch1["characters"]
    assert ch1["try_fail"] == "yes-but"
    assert "thermal fluctuation" in ch1["chapter_question"]
    assert "Helena" in ch1["plants"][0]
    assert len(ch1["beats"]) == 3
    
    # Check Chapter 2
    ch2 = entries[1]
    assert ch2["num"] == 2
    assert ch2["title"] == "The Silent Apartment"
    assert ch2["location"] == "Elisa's Apartment, Hottingen"
    assert ch2["try_fail"] == "no-and"
    assert "key left by Helena" in ch2["harvests"][0]
    assert len(ch2["beats"]) == 3

@patch("verify_continuity.call_llm")
@patch("verify_continuity.OUTLINE_PATH")
@patch("verify_continuity.EVAL_LOGS_DIR")
def test_validation_success(mock_eval_dir, mock_outline_path, mock_call_llm, temp_outline, tmp_path):
    """Simulates a successful continuity validation with score >= 7.5."""
    mock_outline_path.exists.return_value = True
    mock_outline_path.read_text.return_value = temp_outline.read_text()
    
    mock_eval_dir.mkdir = MagicMock()
    # Mock report path to be written to a temp file in tmp_path
    report_file = tmp_path / "continuity_report.json"
    
    # Setup LLM response for clean timeline
    clean_response = json.dumps({
        "continuity_score": 9.5,
        "inconsistencies": [],
        "timeline_flow": "The narrative transitions smoothly with no loops."
    })
    mock_call_llm.return_value = clean_response
    
    with patch("verify_continuity.EVAL_LOGS_DIR", tmp_path):
        # We catch sys.exit to verify exit codes
        with pytest.raises(SystemExit) as exc_info:
            run_continuity_validation(strict=True, threshold=7.5)
            
        assert exc_info.value.code == 0
        assert report_file.exists()
        
        # Verify saved data
        saved_data = json.loads(report_file.read_text(encoding="utf-8"))
        assert saved_data["continuity_score"] == 9.5
        assert len(saved_data["inconsistencies"]) == 0

@patch("verify_continuity.call_llm")
@patch("verify_continuity.OUTLINE_PATH")
@patch("verify_continuity.EVAL_LOGS_DIR")
def test_validation_failure_strict(mock_eval_dir, mock_outline_path, mock_call_llm, temp_outline, tmp_path):
    """Simulates a continuity validation failure in strict mode (score < 7.5)."""
    mock_outline_path.exists.return_value = True
    mock_outline_path.read_text.return_value = temp_outline.read_text()
    
    # Setup LLM response indicating timeline error
    error_response = json.dumps({
        "continuity_score": 6.0,
        "inconsistencies": [
            {
                "chapters": [1, 2],
                "severity": "high",
                "issue_type": "event_repetition",
                "description": "Chapter 2 repeats the debate from Chapter 1 as if it never happened.",
                "suggested_fix": "Remove debate from Chapter 2."
            }
        ],
        "timeline_flow": "Timeline is compromised due to repetitive dialogues."
    })
    mock_call_llm.return_value = error_response
    
    with patch("verify_continuity.EVAL_LOGS_DIR", tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            run_continuity_validation(strict=True, threshold=7.5)
            
        # Should exit with code 1 in strict mode
        assert exc_info.value.code == 1

@patch("verify_continuity.call_llm")
@patch("verify_continuity.OUTLINE_PATH")
@patch("verify_continuity.EVAL_LOGS_DIR")
def test_validation_failure_non_strict(mock_eval_dir, mock_outline_path, mock_call_llm, temp_outline, tmp_path):
    """Simulates a continuity validation failure in non-strict mode (should exit code 0)."""
    mock_outline_path.exists.return_value = True
    mock_outline_path.read_text.return_value = temp_outline.read_text()
    
    error_response = json.dumps({
        "continuity_score": 6.0,
        "inconsistencies": [
            {
                "chapters": [1, 2],
                "severity": "high",
                "issue_type": "event_repetition",
                "description": "Chapter 2 repeats the debate from Chapter 1.",
                "suggested_fix": "Remove debate."
            }
        ],
        "timeline_flow": "Timeline is compromised."
    })
    mock_call_llm.return_value = error_response
    
    with patch("verify_continuity.EVAL_LOGS_DIR", tmp_path):
        with pytest.raises(SystemExit) as exc_info:
            # strict=False should not exit with error even if score < threshold
            run_continuity_validation(strict=False, threshold=7.5)
            
        assert exc_info.value.code == 0
