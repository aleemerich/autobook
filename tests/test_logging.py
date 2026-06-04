#!/usr/bin/env python3
"""
tests/test_logging.py — Unit tests for pipeline logging and log directory redirects.
"""

import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from run import Tee
from evaluate import evaluate_chapter

def test_tee_logger(tmp_path):
    # Setup temporary log file
    log_file = tmp_path / "test_pipeline.log"
    
    # Mock a stream (like sys.stdout)
    mock_stream = MagicMock()
    
    # Create Tee logger
    tee = Tee(str(log_file), mock_stream)
    
    # Write data
    test_data = "Hello, pipeline logging!\n"
    tee.write(test_data)
    tee.flush()
    
    # Check that data was written to file
    assert log_file.exists()
    assert log_file.read_text(encoding="utf-8") == test_data
    
    # Check that data was written to stream
    mock_stream.write.assert_called_once_with(test_data)
    assert mock_stream.flush.call_count == 2


@patch("evaluate.load_layer_files")
@patch("evaluate.load_chapter")
@patch("evaluate.call_judge")
def test_evaluate_chapter_programmatic_logging(mock_call_judge, mock_load_chapter, mock_load_layer_files, tmp_path):
    # Setup mock returns
    mock_load_layer_files.return_value = {
        "voice": "Voice guidelines",
        "world": "World bible details",
        "characters": "Character registry details",
        "outline": "### Ch 1\nBeat 1: test beat",
        "canon": "Established canon facts",
    }
    mock_load_chapter.return_value = "This is a clean chapter text without slop or banned words."
    
    # Mock judge response
    mock_call_judge.return_value = json.dumps({
        "overall_score": 8.0,
        "voice_adherence": {"score": 8, "weakest_moment": "none", "fix": "none", "note": "good"},
        "prose_quality": {"score": 8, "weakest_moment": "none", "fix": "none", "note": "good"},
        "top_3_revisions": ["Revision 1", "Revision 2"],
        "three_strongest_sentences": ["S1", "S2", "S3"],
        "three_weakest_sentences": ["W1", "W2", "W3"],
    })
    
    # Patch BASE_DIR in evaluate.py to use our temp path
    with patch("evaluate.BASE_DIR", tmp_path):
        result = evaluate_chapter(1)
        
        # Verify scores and results
        assert result["overall_score"] == 8.0
        
        # Verify that directories were created
        eval_log_dir = tmp_path / "logs" / "eval_logs"
        edit_log_dir = tmp_path / "logs" / "edit_logs"
        
        assert eval_log_dir.exists()
        assert edit_log_dir.exists()
        
        # Check files exist
        eval_files = list(eval_log_dir.glob("*_ch01.json"))
        edit_files = list(edit_log_dir.glob("*_ch01_edits.json"))
        
        assert len(eval_files) == 1
        assert len(edit_files) == 1
        
        # Verify content of eval log
        eval_data = json.loads(eval_files[0].read_text(encoding="utf-8"))
        assert eval_data["overall_score"] == 8.0
        
        # Verify content of edit log
        edit_data = json.loads(edit_files[0].read_text(encoding="utf-8"))
        assert edit_data["chapter"] == 1
        assert edit_data["overall_score"] == 8.0
        assert edit_data["top_3_revisions"] == ["Revision 1", "Revision 2"]
