#!/usr/bin/env python3
"""
tests/test_seed_unit.py — Unit tests for the seed.py generator prompts logic.
"""

import pytest
from unittest.mock import patch, MagicMock

# We patch the call_llm inside seed.py to avoid hits to OpenRouter
@patch("seed.call_llm")
def test_seed_generation_prompt_assembly(mock_call_llm):
    """Ensures seed generation correctly formats the prompt and uses the writer persona."""
    import seed
    
    # Mock return value
    mock_call_llm.return_value = "Generated Novel Seeds!"
    
    with patch("sys.argv", ["seed.py", "--count=3"]):
        # Simulate main execution
        with patch("builtins.print") as mock_print:
            seed.main()
            
            # Verify call
            mock_call_llm.assert_called_once()
            called_kwargs = mock_call_llm.call_args[1]
            
            # Assert proper prompts and configurations are passed
            assert "3" in called_kwargs["prompt"]
            assert "fantasy novelist" in called_kwargs["system_prompt"]
            assert called_kwargs["temperature"] == 1.0
            assert called_kwargs["is_judge"] is False


@patch("seed.call_llm")
def test_seed_riff_prompt_assembly(mock_call_llm):
    """Ensures seed riff mode correctly injects user's idea into the prompt."""
    import seed
    
    mock_call_llm.return_value = "Riffed Novel Seeds!"
    
    with patch("sys.argv", ["seed.py", "--riff", "magic costs blood"]):
        with patch("builtins.print") as mock_print:
            seed.main()
            
            mock_call_llm.assert_called_once()
            called_kwargs = mock_call_llm.call_args[1]
            
            assert "magic costs blood" in called_kwargs["prompt"]
            assert "variations" in called_kwargs["prompt"]
            assert called_kwargs["is_judge"] is False
