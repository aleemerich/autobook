#!/usr/bin/env python3
"""
tests/test_llm_unit.py — Unit tests for the llm.py engine.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Import the code to test
from llm import call_llm, PROVIDER_PROFILES


def test_invalid_provider():
    """Ensures call_llm exits with error on unknown provider."""
    with patch.dict(os.environ, {"AUTOBOOK_PROVIDER": "invalido"}):
        with pytest.raises(SystemExit) as excinfo:
            call_llm("prompt", "system")
        assert excinfo.value.code == 1


def test_missing_api_key():
    """Ensures call_llm exits with error when required key is missing."""
    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": ""  # Missing!
    }):
        with pytest.raises(SystemExit) as excinfo:
            call_llm("prompt", "system")
        assert excinfo.value.code == 1


@patch("httpx.Client.post")
def test_model_resolution_specific(mock_post):
    """Ensures call_llm resolves provider-specific model configs first."""
    # Mock HTTP response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_ok = True
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Olá!"}}]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "OPENAI_WRITER_MODEL": "specific-model-writer",
        "AUTOBOOK_WRITER_MODEL": "generic-model-writer"
    }):
        call_llm("prompt", "system", is_judge=False, is_review=False)
        
        # Check payload
        called_args, called_kwargs = mock_post.call_args
        payload = called_kwargs["json"]
        assert payload["model"] == "specific-model-writer"


@patch("httpx.Client.post")
def test_model_resolution_generic_fallback(mock_post):
    """Ensures call_llm falls back to generic AUTOBOOK_WRITER_MODEL when specific is missing."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Olá!"}}]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "OPENAI_WRITER_MODEL": "",  # Missing specific!
        "AUTOBOOK_WRITER_MODEL": "generic-model-writer"
    }):
        call_llm("prompt", "system", is_judge=False, is_review=False)
        
        called_args, called_kwargs = mock_post.call_args
        payload = called_kwargs["json"]
        assert payload["model"] == "generic-model-writer"


@patch("httpx.Client.post")
def test_model_resolution_curated_default(mock_post):
    """Ensures call_llm falls back to profile default model when all env vars are missing."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Olá!"}}]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "OPENAI_WRITER_MODEL": "",
        "AUTOBOOK_WRITER_MODEL": ""  # All missing!
    }):
        call_llm("prompt", "system", is_judge=False, is_review=False)
        
        called_args, called_kwargs = mock_post.call_args
        payload = called_kwargs["json"]
        assert payload["model"] == PROVIDER_PROFILES["openai"]["default_model"]


@patch("httpx.Client.post")
def test_anthropic_payload_structure(mock_post):
    """Ensures Anthropic provider builds the correct native Messages API structure."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"text": "Claude reply!"}]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "test-anth-key"
    }):
        call_llm("prompt", "system-rules", temperature=0.9, is_judge=False)
        
        called_args, called_kwargs = mock_post.call_args
        headers = called_kwargs["headers"]
        payload = called_kwargs["json"]
        
        # Anthropic nativeness verification
        assert headers["x-api-key"] == "test-anth-key"
        assert headers["anthropic-version"] == "2023-06-01"
        assert payload["system"] == "system-rules"
        assert payload["messages"] == [{"role": "user", "content": "prompt"}]
        assert payload["temperature"] == 0.9
