#!/usr/bin/env python3
"""
tests/test_llm_unit.py — Unit tests for the llm.py engine.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

# Import the code to test
from llm import call_llm, PROVIDER_PROFILES, LLMConfigurationError

@pytest.fixture(autouse=True)
def force_clean_lang_env():
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": ""}):
        yield


def test_invalid_provider():
    """Ensures call_llm raises a typed error on unknown provider."""
    with patch.dict(os.environ, {"AUTOBOOK_PROVIDER": "invalido"}):
        with pytest.raises(LLMConfigurationError) as excinfo:
            call_llm("prompt", "system")
        assert "Unknown LLM provider 'invalido'" in str(excinfo.value)


def test_missing_api_key():
    """Ensures call_llm raises a typed error when required key is missing."""
    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": ""  # Missing!
    }):
        with pytest.raises(LLMConfigurationError) as excinfo:
            call_llm("prompt", "system")
        assert "API Key 'OPENAI_API_KEY'" in str(excinfo.value)


@patch("httpx.Client.post")
def test_model_resolution_specific(mock_post):
    """Ensures call_llm resolves provider-specific model configs first."""
    # Mock HTTP response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_ok = True
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
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
        "choices": [{"message": {"content": "Hello!"}}]
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
        "choices": [{"message": {"content": "Hello!"}}]
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

@patch("httpx.Client.post")
def test_llm_dynamic_timeout(mock_post):
    """Ensures call_llm respects dynamic timeouts from env variables."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
    }
    mock_post.return_value = mock_resp

    # Scenario 1: AUTOBOOK_LLM_TIMEOUT is set
    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "AUTOBOOK_LLM_TIMEOUT": "120"
    }):
        call_llm("prompt", "system")
        called_args, called_kwargs = mock_post.call_args
        assert called_kwargs["timeout"] == 120

    # Scenario 2: AUTOBOOK_LLM_TIMEOUT is empty/not set, falls back to AUTOBOOK_PIPELINE_TIMEOUT
    mock_post.reset_mock()
    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "AUTOBOOK_LLM_TIMEOUT": "",
        "AUTOBOOK_PIPELINE_TIMEOUT": "450"
    }):
        call_llm("prompt", "system")
        called_args, called_kwargs = mock_post.call_args
        assert called_kwargs["timeout"] == 450


@patch("httpx.Client.post")
def test_override_model(mock_post):
    """Ensures call_llm respects override_model when provided."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key"
    }):
        call_llm("prompt", "system", override_model="my-override-model")
        
        called_args, called_kwargs = mock_post.call_args
        payload = called_kwargs["json"]
        assert payload["model"] == "my-override-model"


@patch("httpx.Client.post")
@patch("time.sleep")
def test_rate_limit_retry_after(mock_sleep, mock_post):
    """Ensures call_llm sleeps for Retry-After duration when receiving HTTP 429."""
    # First request: 429, Second request: 200
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.headers = {"Retry-After": "15"}
    mock_resp_429.text = "Too many requests"
    
    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}]
    }
    
    mock_post.side_effect = [mock_resp_429, mock_resp_200]
    
    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key"
    }):
        call_llm("prompt", "system")
        
        # Verify sleep was called with 15.0
        mock_sleep.assert_any_call(15.0)
