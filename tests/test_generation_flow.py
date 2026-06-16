#!/usr/bin/env python3
"""
tests/test_generation_flow.py — Unit tests for the modular chapter generation flow,
including critics execution, sequential synthesis, and logging/archiving.
"""

import os
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from pipelines.book_generation import DraftChaptersStep, BookGenerationPipeline

@patch("pipelines.book_generation.evaluate_chapter")
@patch("pipelines.book_generation_steps.persistence.subprocess.run")
@patch("agents.call_llm")
def test_modular_generation_flow(mock_call_llm, mock_subprocess, mock_eval_chapter, tmp_path):
    # Setup mock file structure in tmp_path
    book_data = tmp_path / "book_data"
    book_data.mkdir(parents=True, exist_ok=True)
    
    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outline with 1 chapter and 2 beats
    outline_content = (
        "# Novel Outline\n\n"
        "### Chapter 1: The Awakening\n"
        "**Beats:**\n"
        "- Protagonist wake up and check the device.\n"
        "- Protagonist talks to Subject and checks the reading.\n"
    )
    (book_data / "outline.md").write_text(outline_content, encoding="utf-8")

    # Create empty state
    state = {"chapters_drafted": 0}
    (book_data / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Create empty/basic resource files
    (book_data / "world.md").write_text("World info", encoding="utf-8")
    (book_data / "canon.md").write_text("Canon rules", encoding="utf-8")
    (book_data / "characters.md").write_text("Characters list", encoding="utf-8")
    (book_data / "voice.md").write_text("Voice guidelines", encoding="utf-8")

    # Mock LLM returns for:
    # 1. raw beat 1 drafting
    # 2. raw beat 2 drafting
    # 3. canon critic critique
    # 4. style critic critique
    # 5. flow critic critique
    # 6. synthesis step 1 (canon)
    # 7. synthesis step 2 (flow)
    # 8. synthesis step 3 (style)
    mock_call_llm.side_effect = [
        "Beat 1: Protagonist wakes up.",  # raw beat 1
        "Beat 2: Protagonist talks to Subject.",  # raw beat 2
        "Critique Canon: Subject is lucid.",  # critique_canon
        "Critique Style: Good voice.",  # critique_style
        "Critique Flow: Smooth flow.",  # critique_flow
        "Draft after Canon Critique.",  # synthesis step 1
        "Draft after Flow Critique.",  # synthesis step 2
        "Draft after Style Critique: Final Chapter text."  # synthesis step 3
    ]
    
    # Mock evaluate_chapter
    mock_eval_chapter.return_value = {
        "overall_score": 7.5,
        "slop": {"slop_penalty": 0.0, "tier1_hits": [], "tier2_hits": []}
    }
    
    # Mock subprocess runs
    mock_sub_run = MagicMock()
    mock_sub_run.returncode = 0
    mock_subprocess.return_value = mock_sub_run
    
    # Patch all directories and base paths
    with patch("pipelines.book_generation.BASE_DIR", tmp_path), \
         patch("pipelines.book_generation.BOOK_DATA_DIR", book_data), \
         patch("pipelines.book_generation.CHAPTERS_DIR", chapters_dir), \
         patch("evaluate.CHAPTERS_DIR", chapters_dir), \
         patch("evaluate.BASE_DIR", tmp_path):
         
        step = DraftChaptersStep()
        context = {"chapters": [1]}
        step.run(context)
        
        # Verify final chapter file content and location
        ch_file = chapters_dir / "ch_01.md"
        assert ch_file.exists()
        assert ch_file.read_text(encoding="utf-8") == "Draft after Style Critique: Final Chapter text."
        
        # Verify logs/tmp_draft files
        tmp_draft_dir = logs_dir / "tmp_draft"
        assert tmp_draft_dir.exists()
        assert (tmp_draft_dir / "beat_01_raw.md").exists()
        assert (tmp_draft_dir / "beat_02_raw.md").exists()
        assert (tmp_draft_dir / "chapter_raw.md").exists()
        assert (tmp_draft_dir / "critique_canon.md").exists()
        assert (tmp_draft_dir / "critique_style.md").exists()
        assert (tmp_draft_dir / "critique_flow.md").exists()
        
        # Verify the archived attempt directory exists and contains all files
        attempts_dir = logs_dir / "generation_attempts" / "ch01_attempt01"
        assert attempts_dir.exists()
        assert (attempts_dir / "beat_01_raw.md").exists()
        assert (attempts_dir / "critique_style.md").exists()
        assert (attempts_dir / "ch_01_final_attempt.md").exists()
        assert (attempts_dir / "evaluation.json").exists()
        
        # Verify the archived final version
        archived_final = attempts_dir / "ch_01_final_attempt.md"
        assert archived_final.read_text(encoding="utf-8") == "Draft after Style Critique: Final Chapter text."

        # Verify the archived revision plan
        revision_plan_file = attempts_dir / "revision_plan.json"
        assert revision_plan_file.exists()
        saved_plan = json.loads(revision_plan_file.read_text(encoding="utf-8"))
        assert len(saved_plan["findings"]) == 3
        assert saved_plan["findings"][0]["source"] == "canon_critic"
        assert saved_plan["findings"][1]["source"] == "flow_critic"
        assert saved_plan["findings"][2]["source"] == "style_critic"

@patch("pipelines.book_generation.evaluate_chapter")
@patch("pipelines.book_generation_steps.persistence.subprocess.run")
@patch("agents.call_llm")
def test_generation_flow_custom_critics(mock_call_llm, mock_subprocess, mock_eval_chapter, tmp_path):
    # Setup mock file structure in tmp_path
    book_data = tmp_path / "book_data"
    book_data.mkdir(parents=True, exist_ok=True)
    
    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outline with 1 chapter and 1 beat
    outline_content = (
        "# Novel Outline\n\n"
        "### Chapter 1: The Awakening\n"
        "**Beats:**\n"
        "- Protagonist wake up and check the device.\n"
    )
    (book_data / "outline.md").write_text(outline_content, encoding="utf-8")

    # Create empty state
    state = {"chapters_drafted": 0}
    (book_data / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Create empty/basic resource files
    (book_data / "world.md").write_text("World info", encoding="utf-8")
    (book_data / "canon.md").write_text("Canon rules", encoding="utf-8")
    (book_data / "characters.md").write_text("Characters list", encoding="utf-8")
    (book_data / "voice.md").write_text("Voice guidelines", encoding="utf-8")

    # We will pass critics_roles=["canon_critic"]
    # So we mock returns for:
    # 1. raw beat 1 drafting
    # 2. canon critic critique
    # 3. synthesis step 1 (canon)
    mock_call_llm.side_effect = [
        "Beat 1: Protagonist wakes up.",  # raw beat 1
        "Critique Canon: Subject is lucid.",  # critique_canon
        "Draft after Canon Critique: Final Chapter text."  # synthesis step 1
    ]
    
    # Mock evaluate_chapter
    mock_eval_chapter.return_value = {
        "overall_score": 7.5,
        "slop": {"slop_penalty": 0.0, "tier1_hits": [], "tier2_hits": []}
    }
    
    # Mock subprocess runs
    mock_sub_run = MagicMock()
    mock_sub_run.returncode = 0
    mock_subprocess.return_value = mock_sub_run
    
    # Patch base dirs
    with patch("pipelines.book_generation.BASE_DIR", tmp_path), \
         patch("pipelines.book_generation.BOOK_DATA_DIR", book_data), \
         patch("pipelines.book_generation.CHAPTERS_DIR", chapters_dir), \
         patch("evaluate.CHAPTERS_DIR", chapters_dir), \
         patch("evaluate.BASE_DIR", tmp_path):
         
        step = DraftChaptersStep(critics_roles=["canon_critic"])
        context = {"chapters": [1]}
        step.run(context)
        
        # Verify final chapter file content and location
        ch_file = chapters_dir / "ch_01.md"
        assert ch_file.exists()
        assert ch_file.read_text(encoding="utf-8") == "Draft after Canon Critique: Final Chapter text."
        
        # Verify only critique_canon is created (no flow or style)
        tmp_draft_dir = logs_dir / "tmp_draft"
        assert tmp_draft_dir.exists()
        assert (tmp_draft_dir / "beat_01_raw.md").exists()
        assert (tmp_draft_dir / "critique_canon.md").exists()
        assert not (tmp_draft_dir / "critique_style.md").exists()
        assert not (tmp_draft_dir / "critique_flow.md").exists()

@patch("pipelines.book_generation.evaluate_chapter")
@patch("pipelines.book_generation_steps.persistence.subprocess.run")
@patch("agents.call_llm")
def test_generation_flow_evaluation_error(mock_call_llm, mock_subprocess, mock_eval_chapter, tmp_path):
    # Setup mock file structure in tmp_path
    book_data = tmp_path / "book_data"
    book_data.mkdir(parents=True, exist_ok=True)

    chapters_dir = tmp_path / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Create outline with 1 chapter and 1 beat
    outline_content = (
        "# Novel Outline\n\n"
        "### Chapter 1: The Awakening\n"
        "**Beats:**\n"
        "- Protagonist wake up and check the device.\n"
    )
    (book_data / "outline.md").write_text(outline_content, encoding="utf-8")

    # Create empty state
    state = {"chapters_drafted": 0}
    (book_data / "state.json").write_text(json.dumps(state), encoding="utf-8")

    # Create empty/basic resource files
    (book_data / "world.md").write_text("World info", encoding="utf-8")
    (book_data / "canon.md").write_text("Canon rules", encoding="utf-8")
    (book_data / "characters.md").write_text("Characters list", encoding="utf-8")
    (book_data / "voice.md").write_text("Voice guidelines", encoding="utf-8")

    # Mock LLM returns
    mock_call_llm.side_effect = [
        "Beat 1: Protagonist wakes up.",  # raw beat 1
        "Critique Canon: Subject is lucid.",  # critique_canon
        "Critique Style: Good voice.",  # critique_style
        "Critique Flow: Smooth flow.",  # critique_flow
        "Draft after Canon Critique.",  # synthesis step 1
        "Draft after Flow Critique.",  # synthesis step 2
        "Draft after Style Critique: Final Chapter text."  # synthesis step 3
    ]

    # Mock evaluate_chapter to raise an exception
    mock_eval_chapter.side_effect = Exception("Evaluation engine failure")

    # Mock subprocess runs
    mock_sub_run = MagicMock()
    mock_sub_run.returncode = 0
    mock_subprocess.return_value = mock_sub_run

    # Patch all directories and base paths
    with patch("pipelines.book_generation.BASE_DIR", tmp_path), \
         patch("pipelines.book_generation.BOOK_DATA_DIR", book_data), \
         patch("pipelines.book_generation.CHAPTERS_DIR", chapters_dir), \
         patch("evaluate.CHAPTERS_DIR", chapters_dir), \
         patch("evaluate.BASE_DIR", tmp_path):

        step = DraftChaptersStep()
        context = {"chapters": [1]}

        # O step.run deve levantar a exceção da avaliação
        with pytest.raises(Exception, match="Evaluation engine failure"):
            step.run(context)

        # Mesmo com o erro de avaliação, a tentativa deve ter sido arquivada
        attempts_dir = logs_dir / "generation_attempts" / "ch01_attempt01"
        assert attempts_dir.exists()
        assert (attempts_dir / "beat_01_raw.md").exists()
        assert (attempts_dir / "ch_01_final_attempt.md").exists()

        # E evaluation.json NÃO deve existir, pois a avaliação falhou
        assert not (attempts_dir / "evaluation.json").exists()
