#!/usr/bin/env python3
"""
tests/test_foundation_generators_unit.py — Unit tests for Phase 4 foundation generator scripts.
Verifies that all call_writer functions correctly delegate to llm.call_llm with expected parameters.
"""

import pytest
from unittest.mock import patch, MagicMock

@patch("llm.call_llm")
def test_gen_world_call_writer(mock_call_llm):
    """Verifies gen_world.call_writer correctly routes to call_llm with the appropriate system prompt and temperature."""
    from gen_world import call_writer
    mock_call_llm.return_value = "Mocked World Bible Response"
    
    prompt = "Test worldbuilding prompt"
    res = call_writer(prompt)
    
    assert res == "Mocked World Bible Response"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "worldbuilder" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.7
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_gen_characters_call_writer(mock_call_llm):
    """Verifies gen_characters.call_writer correctly routes to call_llm."""
    from gen_characters import call_writer
    mock_call_llm.return_value = "Mocked Character Registry Response"
    
    prompt = "Test character registry prompt"
    res = call_writer(prompt)
    
    assert res == "Mocked Character Registry Response"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "character designer" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.7
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_gen_outline_call_writer(mock_call_llm):
    """Verifies gen_outline.call_writer correctly routes to call_llm."""
    from gen_outline import call_writer
    mock_call_llm.return_value = "Mocked Chapter Outline Response"
    
    prompt = "Test outline prompt"
    res = call_writer(prompt)
    
    assert res == "Mocked Chapter Outline Response"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "novel architect" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.5
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_gen_outline_part2_call_writer(mock_call_llm):
    """Verifies gen_outline_part2.call_writer correctly routes to call_llm."""
    from gen_outline_part2 import call_writer
    mock_call_llm.return_value = "Mocked Continuing Outline Response"
    
    prompt = "Test outline continuation prompt"
    res = call_writer(prompt)
    
    assert res == "Mocked Continuing Outline Response"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "continuing an outline" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.5
    assert called_kwargs["is_judge"] is False

@patch("llm.call_llm")
def test_gen_canon_call_writer(mock_call_llm):
    """Verifies gen_canon.call_writer correctly routes to call_llm."""
    from gen_canon import call_writer
    mock_call_llm.return_value = "Mocked Continuity Database Response"
    
    prompt = "Test canon prompt"
    res = call_writer(prompt)
    
    assert res == "Mocked Continuity Database Response"
    mock_call_llm.assert_called_once()
    called_kwargs = mock_call_llm.call_args[1]
    assert called_kwargs["prompt"] == prompt
    assert "continuity editor" in called_kwargs["system_prompt"]
    assert called_kwargs["temperature"] == 0.2
    assert called_kwargs["is_judge"] is False
