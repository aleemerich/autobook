#!/usr/bin/env python3
"""
tests/test_pipeline_control.py — Unit tests for pipeline control, task-based checkpoint state, rewinding, status checklist, and truncated logging.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import copy

import run_pipeline
from run_pipeline import log_msg, save_state, run_pipeline as run_pipeline_main, default_state, TASK_LIST

@pytest.fixture
def mock_log_file(tmp_path):
    orig_log_file = run_pipeline.LOG_FILE
    temp_log = tmp_path / "pipeline.log"
    run_pipeline.LOG_FILE = temp_log
    yield temp_log
    run_pipeline.LOG_FILE = orig_log_file

@pytest.fixture
def mock_state_file(tmp_path):
    orig_state_file = run_pipeline.STATE_FILE
    temp_state = tmp_path / "state.json"
    run_pipeline.STATE_FILE = temp_state
    yield temp_state
    run_pipeline.STATE_FILE = orig_state_file

def test_log_msg_truncation(mock_log_file, monkeypatch):
    # Set limit to 10
    monkeypatch.setattr(run_pipeline, "LOG_TRUNCATE_LIMIT", 10)
    
    printed = []
    def mock_print(msg):
        printed.append(msg)
        
    monkeypatch.setattr("builtins.print", mock_print)
    
    test_msg = "Hello World Extra Long Message"
    log_msg(test_msg, level="INFO", truncate=True)
    
    # Check that screen output was truncated
    assert len(printed) == 1
    assert "Hello Worl..." in printed[0]  # "Hello Worl" is 10 chars
    
    # Check that log file has untruncated content
    log_content = mock_log_file.read_text(encoding="utf-8")
    assert "Hello World Extra Long Message" in log_content
    assert "[INFO]" in log_content

def test_log_msg_no_truncation(mock_log_file, monkeypatch):
    monkeypatch.setattr(run_pipeline, "LOG_TRUNCATE_LIMIT", 100)
    
    printed = []
    def mock_print(msg):
        printed.append(msg)
        
    monkeypatch.setattr("builtins.print", mock_print)
    
    test_msg = "Short"
    log_msg(test_msg, level="INFO", truncate=True)
    
    assert len(printed) == 1
    assert "Short" in printed[0]
    assert "..." not in printed[0]

def test_checkpoint_state_saving(mock_state_file):
    state = default_state()
    state["completed_tasks"] = ["0_ideation", "1_world"]
    state["current_task"] = "2_characters"
    save_state(state)
    
    assert mock_state_file.exists()
    saved = json.loads(mock_state_file.read_text())
    assert saved["completed_tasks"] == ["0_ideation", "1_world"]
    assert saved["current_task"] == "2_characters"

@patch("run_pipeline.save_state")
def test_cli_status(mock_save, mock_log_file, monkeypatch):
    monkeypatch.setattr(run_pipeline, "get_current_branch", lambda: "test-branch")
    
    printed = []
    monkeypatch.setattr("builtins.print", lambda msg: printed.append(str(msg)))
    
    # Mock CLI arguments
    class Args:
        status = True
        rewind = None
        task = None
        phase = None
        from_scratch = False
        max_cycles = None
        
    state = {
        "completed_tasks": ["0_ideation"],
        "current_task": "0_ideation"
    }
    
    # Run pipeline with status=True
    with patch("run_pipeline.load_state", return_value=state):
        run_pipeline_main(Args())
        
    # Check that status checklist was logged
    all_printed = "\n".join(printed)
    assert "[x] 0_ideation" in all_printed
    assert "[ ] 1_world" in all_printed

def test_cli_rewind(mock_log_file, monkeypatch):
    monkeypatch.setattr(run_pipeline, "get_current_branch", lambda: "test-branch")
    
    printed = []
    monkeypatch.setattr("builtins.print", lambda msg: printed.append(str(msg)))
    
    class Args:
        status = False
        rewind = "3_outline"
        task = None
        phase = None
        from_scratch = False
        max_cycles = None
        
    state = {
        "completed_tasks": ["0_ideation", "1_world", "2_characters", "3_outline", "4_outline_p2"],
        "current_task": "4_outline_p2"
    }
    
    saved_states = []
    def mock_save_state(s):
        saved_states.append(copy.deepcopy(s))
    monkeypatch.setattr(run_pipeline, "save_state", mock_save_state)
    
    # Mock all task executors to do nothing
    for task in TASK_LIST:
        fn_name = f"task_{task.split('_', 1)[1]}"
        monkeypatch.setattr(run_pipeline, fn_name, MagicMock(return_value=state))
    
    with patch("run_pipeline.load_state", return_value=state):
        run_pipeline_main(Args())
        
    # Verify that the first saved state was the rewound state
    # (The rewind block calls save_state immediately after setting completed_tasks)
    rewound_state = saved_states[0]
    assert rewound_state["completed_tasks"] == ["0_ideation", "1_world", "2_characters"]
    assert rewound_state["current_task"] == "3_outline"
    assert rewound_state["phase"] == "foundation"

@patch("run_pipeline.save_state")
def test_cli_single_task(mock_save, mock_log_file, monkeypatch):
    monkeypatch.setattr(run_pipeline, "get_current_branch", lambda: "test-branch")
    
    class Args:
        status = False
        rewind = None
        task = "1_world"
        phase = None
        from_scratch = False
        max_cycles = None
        
    state = default_state()
    
    mock_task_fn = MagicMock(return_value=state)
    monkeypatch.setattr(run_pipeline, "task_world", mock_task_fn)
    
    with patch("run_pipeline.load_state", return_value=state):
        run_pipeline_main(Args())
        
    mock_task_fn.assert_called_once_with(state)
