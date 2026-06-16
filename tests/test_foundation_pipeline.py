#!/usr/bin/env python3
import pytest
from unittest.mock import patch, MagicMock
import json

import pipelines.foundation
from pipelines.foundation import (
    FoundationPipeline,
    VerifySeedStep,
    GenerateWorldStep,
    GenerateCharactersStep,
    GenerateOutlineStep,
    GenerateCanonStep,
    CommitFoundationStep
)

@pytest.fixture
def mock_foundation_paths(tmp_path):
    # Store originals
    orig_seed = pipelines.foundation.SEED_PATH
    orig_voice = pipelines.foundation.VOICE_PATH
    orig_craft = pipelines.foundation.CRAFT_PATH
    orig_mystery = pipelines.foundation.MYSTERY_PATH
    orig_world = pipelines.foundation.WORLD_PATH
    orig_chars = pipelines.foundation.CHARACTERS_PATH
    orig_outline = pipelines.foundation.OUTLINE_PATH
    orig_canon = pipelines.foundation.CANON_PATH
    orig_state = pipelines.foundation.STATE_FILE
    orig_book_data = pipelines.foundation.BOOK_DATA_DIR

    # Override
    pipelines.foundation.SEED_PATH = tmp_path / "seed.txt"
    pipelines.foundation.BOOK_DATA_DIR = tmp_path / "book_data"
    pipelines.foundation.BOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    pipelines.foundation.VOICE_PATH = pipelines.foundation.BOOK_DATA_DIR / "voice.md"
    pipelines.foundation.MYSTERY_PATH = pipelines.foundation.BOOK_DATA_DIR / "MYSTERY.md"
    pipelines.foundation.WORLD_PATH = pipelines.foundation.BOOK_DATA_DIR / "world.md"
    pipelines.foundation.CHARACTERS_PATH = pipelines.foundation.BOOK_DATA_DIR / "characters.md"
    pipelines.foundation.OUTLINE_PATH = pipelines.foundation.BOOK_DATA_DIR / "outline.md"
    pipelines.foundation.CANON_PATH = pipelines.foundation.BOOK_DATA_DIR / "canon.md"
    pipelines.foundation.STATE_FILE = pipelines.foundation.BOOK_DATA_DIR / "state.json"
    
    doc_dir = tmp_path / "doc"
    doc_dir.mkdir(parents=True, exist_ok=True)
    pipelines.foundation.CRAFT_PATH = doc_dir / "CRAFT.md"

    # Setup standard files needed for inputs
    pipelines.foundation.SEED_PATH.write_text("Mock Seed Concept content", encoding="utf-8")
    pipelines.foundation.VOICE_PATH.write_text("Part 1: Tone\nPart 2: Specific voice details", encoding="utf-8")
    pipelines.foundation.CRAFT_PATH.write_text("Save the Cat outline rules", encoding="utf-8")
    pipelines.foundation.MYSTERY_PATH.write_text("The Central Mystery secrets", encoding="utf-8")

    yield tmp_path

    # Restore
    pipelines.foundation.SEED_PATH = orig_seed
    pipelines.foundation.VOICE_PATH = orig_voice
    pipelines.foundation.CRAFT_PATH = orig_craft
    pipelines.foundation.MYSTERY_PATH = orig_mystery
    pipelines.foundation.WORLD_PATH = orig_world
    pipelines.foundation.CHARACTERS_PATH = orig_chars
    pipelines.foundation.OUTLINE_PATH = orig_outline
    pipelines.foundation.CANON_PATH = orig_canon
    pipelines.foundation.STATE_FILE = orig_state
    pipelines.foundation.BOOK_DATA_DIR = orig_book_data

def test_verify_seed_step_success(mock_foundation_paths):
    """Test seed verification passes if seed.txt exists."""
    step = VerifySeedStep()
    context = {}
    step.run(context)  # should not raise any error

def test_verify_seed_step_failure(mock_foundation_paths):
    """Test seed verification raises FileNotFoundError if seed.txt does not exist."""
    pipelines.foundation.SEED_PATH.unlink()
    step = VerifySeedStep()
    context = {}
    with pytest.raises(FileNotFoundError):
        step.run(context)

@patch("pipelines.foundation.call_llm")
def test_generate_world_step(mock_call_llm, mock_foundation_paths):
    """Test world.md generation calls the LLM and writes to file."""
    mock_call_llm.return_value = "## World Bible Lore Details"
    step = GenerateWorldStep()
    context = {}
    step.run(context)

    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert "worldbuilder" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.7
    assert pipelines.foundation.WORLD_PATH.exists()
    assert pipelines.foundation.WORLD_PATH.read_text(encoding="utf-8") == "## World Bible Lore Details"

@patch("pipelines.foundation.call_llm")
def test_generate_characters_step(mock_call_llm, mock_foundation_paths):
    """Test characters.md generation calls the LLM and writes to file."""
    mock_call_llm.return_value = "## Character Registry details"
    step = GenerateCharactersStep()
    context = {}
    step.run(context)

    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert "character designer" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.7
    assert pipelines.foundation.CHARACTERS_PATH.exists()
    assert pipelines.foundation.CHARACTERS_PATH.read_text(encoding="utf-8") == "## Character Registry details"

@patch("pipelines.foundation.call_llm")
def test_generate_outline_step(mock_call_llm, mock_foundation_paths):
    """Test outline.md generation calls the LLM and writes to file."""
    mock_call_llm.return_value = "## Chapter Outline beats details"
    step = GenerateOutlineStep()
    context = {}
    step.run(context)

    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert "novel architect" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.5
    assert pipelines.foundation.OUTLINE_PATH.exists()
    assert pipelines.foundation.OUTLINE_PATH.read_text(encoding="utf-8") == "## Chapter Outline beats details"

@patch("pipelines.foundation.call_llm")
def test_generate_canon_step(mock_call_llm, mock_foundation_paths):
    """Test canon.md generation calls the LLM and writes to file."""
    mock_call_llm.return_value = "## Canon facts checklist"
    step = GenerateCanonStep()
    context = {}
    step.run(context)

    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert "continuity editor" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.2
    assert pipelines.foundation.CANON_PATH.exists()
    assert pipelines.foundation.CANON_PATH.read_text(encoding="utf-8") == "## Canon facts checklist"

@patch("subprocess.run")
def test_commit_foundation_step(mock_sub_run, mock_foundation_paths):
    """Test committing files and initializing state.json cursor to 0."""
    step = CommitFoundationStep()
    context = {}
    step.run(context)

    # State file should show 0 drafted chapters and phase "writing"
    assert pipelines.foundation.STATE_FILE.exists()
    state = json.loads(pipelines.foundation.STATE_FILE.read_text(encoding="utf-8"))
    assert state["chapters_drafted"] == 0
    assert state["phase"] == "writing"
    assert state["current_focus"] == "chapters"

    # Git command should have been called
    assert mock_sub_run.call_count >= 5

@patch("subprocess.run")
@patch("pipelines.foundation.call_llm")
def test_full_foundation_pipeline(mock_call_llm, mock_sub_run, mock_foundation_paths):
    """Test the full FoundationPipeline executing all steps successfully."""
    mock_call_llm.side_effect = [
        "## World Bible Lore Details",
        "## Character Registry details",
        "## Chapter Outline beats details",
        "## Canon facts checklist"
    ]

    pipeline = FoundationPipeline()
    context = {}
    pipeline.run(context)

    assert pipelines.foundation.WORLD_PATH.exists()
    assert pipelines.foundation.CHARACTERS_PATH.exists()
    assert pipelines.foundation.OUTLINE_PATH.exists()
    assert pipelines.foundation.CANON_PATH.exists()
    assert pipelines.foundation.STATE_FILE.exists()
    
    state = json.loads(pipelines.foundation.STATE_FILE.read_text(encoding="utf-8"))
    assert state["chapters_drafted"] == 0
    assert state["phase"] == "writing"


def test_foundation_pipeline_steps_and_order() -> None:
    """Valida que o FoundationPipeline possui exatamente os passos esperados na mesma ordem."""
    pipeline = FoundationPipeline()
    steps = pipeline.steps
    assert len(steps) == 6
    assert isinstance(steps[0], VerifySeedStep)
    assert isinstance(steps[1], GenerateWorldStep)
    assert isinstance(steps[2], GenerateCharactersStep)
    assert isinstance(steps[3], GenerateOutlineStep)
    assert isinstance(steps[4], GenerateCanonStep)
    assert isinstance(steps[5], CommitFoundationStep)


@patch("pipelines.foundation.write_foundation_state")
@patch("pipelines.foundation.commit_foundation_artifacts", side_effect=ValueError("Simulated git error"))
def test_commit_foundation_step_writes_state_on_git_failure(mock_commit_artifacts, mock_write_state, mock_foundation_paths) -> None:
    """Valida que CommitFoundationStep escreve o estado mesmo se o commit falhar."""
    step = CommitFoundationStep()
    context = {}

    # Executamos o passo (não deve quebrar com ValueError)
    step.run(context)

    mock_commit_artifacts.assert_called_once()
    mock_write_state.assert_called_once_with(pipelines.foundation.STATE_FILE)
