#!/usr/bin/env python3
"""
tests/test_ideation_unit.py — Unit tests for the FASE 0: IDEATION phase in run_pipeline.py.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from run_pipeline import run_ideation, default_state, save_state

BASE_DIR = Path(__file__).parent.parent


@pytest.fixture
def clean_state():
    return default_state()


@pytest.fixture
def mock_cauldron_output():
    return (
        "1. THE ECHO CHAMBER\n"
        "HOOK: In a city of silence, Cass discovers the noise of forgotten lives.\n"
        "WORLD: Rusted pipes, dripping water, copper towers.\n"
        "MAGIC/COST: Sound magic that decays the user's vocal cords.\n"
        "TENSION: Cass must speak to save his brother, but every word brings him closer to silence.\n"
        "THE CONSPIRACY: The High Rectors are harvesting vocal cords to fuel their golden cathedral.\n"
        "THEME: Is voice worth the cost of speech?\n\n"
        "2. THE WEAVERS OF RUST\n"
        "HOOK: A girl who can sew metal must mend the decaying heart of a sleeping war engine.\n"
        "WORLD: Rusted landscape, constant ash rain, neon smoke.\n"
        "MAGIC/COST: Rust-binding, which costs physical body heat.\n"
        "TENSION: She must revive the engine to save her village, even if she freezes to death doing so.\n"
        "THE CONSPIRACY: The engine's heart was intentionally poisoned by the governor.\n"
        "THEME: How much of yourself must you sacrifice to mend a broken world?\n\n"
        "3. THE BIOTECH REVELATION\n"
        "HOOK: In an ocular society, a blind detective is given a cybernetic eye that sees only sins.\n"
        "WORLD: Neon lights, towering monoliths, biomechanical decay.\n"
        "MAGIC/COST: Cybernetic sight that inflicts blinding head pains.\n"
        "TENSION: He must solve the murder of the Chancellor before his own eye burns his brain.\n"
        "THE CONSPIRACY: The ocular implants are spying on every citizen's thoughts.\n"
        "THEME: Does absolute sight lead to absolute madness?\n"
    )


@patch("run_pipeline.git_add_commit")
@patch("llm.call_llm")
@patch("builtins.input")
def test_run_ideation_select_option(mock_input, mock_call_llm, mock_git_commit, clean_state, mock_cauldron_output):
    """Ensures selecting a generated concept option (1-3) successfully writes it to seed.txt and advances phase."""
    # 1. Clean environment
    seed_file = BASE_DIR / "seed.txt"
    if seed_file.exists():
        seed_file.unlink()

    # 2. Mock inputs: 4 questionnaire questions, and choice "2"
    mock_input.side_effect = [
        "Sci-fi noir",  # Genre
        "cybernetic eye",  # Spark
        "neural damage",  # Cost
        "blind detective",  # Protagonist
        "2"  # Choice: Select Option 2
    ]
    
    mock_call_llm.return_value = mock_cauldron_output

    try:
        updated_state = run_ideation(clean_state)
        
        # Check seed.txt was written with concept 2
        assert seed_file.exists()
        written_content = seed_file.read_text(encoding="utf-8")
        assert "THE WEAVERS OF RUST" in written_content
        assert "rust-binding" in written_content.lower()
        
        # Check state transitioned to foundation
        assert updated_state["phase"] == "foundation"
        assert updated_state["current_focus"] == "planning"
        mock_git_commit.assert_called_once()
        
    finally:
        if seed_file.exists():
            seed_file.unlink()


@patch("run_pipeline.git_add_commit")
@patch("llm.call_llm")
@patch("builtins.input")
def test_run_ideation_custom_option(mock_input, mock_call_llm, mock_git_commit, clean_state, mock_cauldron_output):
    """Ensures user can select option 'C' to input a fully custom seed concept."""
    seed_file = BASE_DIR / "seed.txt"
    if seed_file.exists():
        seed_file.unlink()

    # Questionnaire, choose C, then enter custom text
    mock_input.side_effect = [
        "", "", "", "",  # Pressione Enter for all 4 questions
        "C",  # Choose Custom option
        "My completely unique custom idea about space and clocks."  # Custom idea text
    ]
    
    mock_call_llm.return_value = mock_cauldron_output

    try:
        updated_state = run_ideation(clean_state)
        
        assert seed_file.exists()
        assert seed_file.read_text(encoding="utf-8") == "My completely unique custom idea about space and clocks."
        assert updated_state["phase"] == "foundation"
        
    finally:
        if seed_file.exists():
            seed_file.unlink()


@patch("run_pipeline.git_add_commit")
@patch("builtins.input")
def test_run_ideation_bypass_existing_seed(mock_input, mock_git_commit, clean_state):
    """Ensures if seed.txt already exists, user can choose to bypass/skip the ideation phase."""
    seed_file = BASE_DIR / "seed.txt"
    seed_file.write_text("Existing pre-generated seed from elsewhere", encoding="utf-8")

    # Bypass question: Yes (Enter or S)
    mock_input.side_effect = ["S"]

    try:
        updated_state = run_ideation(clean_state)
        
        # Check that seed.txt was preserved
        assert seed_file.exists()
        assert seed_file.read_text(encoding="utf-8") == "Existing pre-generated seed from elsewhere"
        
        # Check that it advanced to foundation phase
        assert updated_state["phase"] == "foundation"
        mock_git_commit.assert_not_called()  # No git commit during bypass
        
    finally:
        if seed_file.exists():
            seed_file.unlink()
