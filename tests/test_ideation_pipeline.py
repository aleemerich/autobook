#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import re

import pipelines.ideation
from pipelines.ideation import IdeationPipeline

@pytest.fixture
def mock_ideation_paths(tmp_path):
    # Store originals
    orig_seed = pipelines.ideation.SEED_PATH
    orig_mystery = pipelines.ideation.MYSTERY_PATH
    orig_state = pipelines.ideation.STATE_FILE
    orig_book_data_dir = pipelines.ideation.BOOK_DATA_DIR

    # Override
    pipelines.ideation.SEED_PATH = tmp_path / "seed.txt"
    pipelines.ideation.BOOK_DATA_DIR = tmp_path / "book_data"
    pipelines.ideation.BOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    pipelines.ideation.MYSTERY_PATH = pipelines.ideation.BOOK_DATA_DIR / "MYSTERY.md"
    pipelines.ideation.STATE_FILE = pipelines.ideation.BOOK_DATA_DIR / "state.json"

    yield tmp_path

    # Restore
    pipelines.ideation.SEED_PATH = orig_seed
    pipelines.ideation.BOOK_DATA_DIR = orig_book_data_dir
    pipelines.ideation.MYSTERY_PATH = orig_mystery
    pipelines.ideation.STATE_FILE = orig_state

@pytest.fixture
def mock_cauldron_output():
    return (
        "1. THE ECHO CHAMBER\n"
        "HOOK: In a city of silence, Cass discovers the noise of forgotten lives.\n"
        "WORLD: Rusted pipes, dripping water, copper towers.\n"
        "MAGIC/COST: Sound magic that decays the user's vocal cords.\n"
        "TENSION: Cass must speak to save his brother.\n"
        "THEME: Is voice worth the cost of speech?\n\n"
        "2. THE WEAVERS OF RUST\n"
        "HOOK: A girl who can sew metal must mend the decaying heart of a sleeping war engine.\n"
        "WORLD: Rusted landscape, constant ash rain.\n"
        "MAGIC/COST: Rust-binding, which costs physical body heat.\n"
        "TENSION: She must revive the engine to save her village.\n"
        "THEME: How much of yourself must you sacrifice to mend a world?\n\n"
        "3. THE BIOTECH REVELATION\n"
        "HOOK: In an ocular society, a blind detective is given a cybernetic eye.\n"
        "WORLD: Neon lights, towering monoliths.\n"
        "MAGIC/COST: Cybernetic sight that inflicts blinding head pains.\n"
        "TENSION: He must solve the murder of the Chancellor.\n"
        "THEME: Does absolute sight lead to absolute madness?\n"
    )

@patch("pipelines.ideation.call_llm")
@patch("builtins.input")
def test_ideation_pipeline_select_option(mock_input, mock_call_llm, mock_ideation_paths, mock_cauldron_output):
    """Test selecting a concept choice from LLM generated options."""
    # 4 questionnaire questions, Choice "2", No to mystery
    mock_input.side_effect = [
        "Fantasy",       # Genre
        "rust binding",  # Spark
        "body heat",     # Cost
        "weaver",        # Protagonist
        "2",             # Select concept 2
        "N"              # Skip mystery
    ]
    mock_call_llm.return_value = mock_cauldron_output

    pipeline = IdeationPipeline()
    context = {}
    pipeline.run(context)

    # Check seed.txt exists and contains the concept
    seed_path = pipelines.ideation.SEED_PATH
    assert seed_path.exists()
    seed_content = seed_path.read_text(encoding="utf-8")
    assert "THE WEAVERS OF RUST" in seed_content
    assert "Rust-binding" in seed_content

    # Check MYSTERY.md contains the fallback/empty template since we skipped it
    mystery_path = pipelines.ideation.MYSTERY_PATH
    assert mystery_path.exists()
    assert "### Author's Eyes Only" in mystery_path.read_text(encoding="utf-8")

    # Check state.json was initialized
    state_path = pipelines.ideation.STATE_FILE
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["chapters_drafted"] == 0
    assert state["phase"] == "foundation"

@patch("pipelines.ideation.call_llm")
@patch("builtins.input")
def test_ideation_pipeline_custom_option(mock_input, mock_call_llm, mock_ideation_paths, mock_cauldron_output):
    """Test writing a custom concept when option 'C' is chosen."""
    # 4 questions, Choice "C", custom text input, and No to mystery
    mock_input.side_effect = [
        "", "", "", "",  # standard defaults
        "C",
        "My completely unique custom idea.",
        "N"
    ]
    mock_call_llm.return_value = mock_cauldron_output

    pipeline = IdeationPipeline()
    context = {}
    pipeline.run(context)

    seed_path = pipelines.ideation.SEED_PATH
    assert seed_path.exists()
    assert seed_path.read_text(encoding="utf-8") == "My completely unique custom idea."

@patch("builtins.input")
def test_ideation_pipeline_bypass(mock_input, mock_ideation_paths):
    """Test bypassing the ideation pipeline when seed.txt already exists."""
    seed_path = pipelines.ideation.SEED_PATH
    seed_path.write_text("Existing pre-generated seed", encoding="utf-8")

    # Choice "S" to skip/bypass ideation
    mock_input.side_effect = ["S"]

    pipeline = IdeationPipeline()
    context = {}
    pipeline.run(context)

    # Check seed.txt is unchanged
    assert seed_path.read_text(encoding="utf-8") == "Existing pre-generated seed"
    # State.json should still be initialized/updated
    state_path = pipelines.ideation.STATE_FILE
    assert state_path.exists()

@patch("pipelines.ideation.call_llm")
@patch("builtins.input")
def test_ideation_pipeline_with_mystery(mock_input, mock_call_llm, mock_ideation_paths, mock_cauldron_output):
    """Test generating a central mystery bible."""
    mock_input.side_effect = [
        "Sci-fi", "", "", "",  # Questions
        "1",                    # Choice 1
        "S"                    # Yes, generate mystery
    ]
    mock_call_llm.side_effect = [
        mock_cauldron_output,
        "# THE CENTRAL MYSTERY\nWho killed the king?"
    ]

    pipeline = IdeationPipeline()
    context = {}
    pipeline.run(context)

    mystery_path = pipelines.ideation.MYSTERY_PATH
    assert mystery_path.exists()
    mystery_content = mystery_path.read_text(encoding="utf-8")
    assert "THE CENTRAL MYSTERY" in mystery_content
    assert "Who killed the king?" in mystery_content
