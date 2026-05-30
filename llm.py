#!/usr/bin/env python3
"""
llm.py — Unified LLM client client for the autonovel pipeline.

Provides a single function 'call_llm' to route requests to Anthropic, OpenAI,
Gemini, and OpenRouter based on configuration in the .env file.
"""

import os
import sys
import httpx
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Declarative Provider Profiles
# ---------------------------------------------------------------------------
PROVIDER_PROFILES = {
    "anthropic": {
        "env_key": "ANTHROPIC_API_KEY",
        "default_url": "https://api.anthropic.com",
        "endpoint_suffix": "/v1/messages",
        "default_model": "claude-sonnet-4-6",
        "env_writer_model": "ANTHROPIC_WRITER_MODEL",
        "env_judge_model": "ANTHROPIC_JUDGE_MODEL",
        "env_review_model": "ANTHROPIC_REVIEW_MODEL",
    },
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "default_url": "https://api.openai.com/v1",
        "endpoint_suffix": "/v1/chat/completions",
        "default_model": "gpt-4o",
        "env_writer_model": "OPENAI_WRITER_MODEL",
        "env_judge_model": "OPENAI_JUDGE_MODEL",
        "env_review_model": "OPENAI_REVIEW_MODEL",
    },
    "gemini": {
        "env_key": "GEMINI_API_KEY",
        "default_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "endpoint_suffix": "/chat/completions",
        "default_model": "gemini-1.5-pro",
        "env_writer_model": "GEMINI_WRITER_MODEL",
        "env_judge_model": "GEMINI_JUDGE_MODEL",
        "env_review_model": "GEMINI_REVIEW_MODEL",
    },
    "openrouter": {
        "env_key": "OPENROUTER_API_KEY",
        "default_url": "https://openrouter.ai/api/v1",
        "endpoint_suffix": "/chat/completions",
        "default_model": "google/gemini-flash-1.5",
        "env_writer_model": "OPENROUTER_WRITER_MODEL",
        "env_judge_model": "OPENROUTER_JUDGE_MODEL",
        "env_review_model": "OPENROUTER_REVIEW_MODEL",
    }
}


def call_llm(prompt: str, system_prompt: str, temperature: float = 0.8,
             is_judge: bool = False, is_review: bool = False) -> str:
    """
    Route prompt to the configured LLM provider and return response text.
    
    Args:
        prompt: The main user instructions/prose context.
        system_prompt: System-level role and style constraints.
        temperature: Creative temperature (defaults to 0.8 for writing).
        is_judge: If True, uses the AUTONOVEL_JUDGE_MODEL (or provider-specific env).
        is_review: If True, uses the AUTONOVEL_REVIEW_MODEL (or provider-specific env).
    """
    # Append dynamic base language directive if configured
    from prompt_loader import load_prompt, get_active_language
    lang = get_active_language()
    if lang:
        try:
            directive = load_prompt("directives.txt", fallback_to_en=False)
            system_prompt += f"\n\n{directive}"
        except FileNotFoundError:
            pass

    provider_name = os.environ.get("AUTOBOOK_PROVIDER", "anthropic").lower()
    
    if provider_name not in PROVIDER_PROFILES:
        print(f"ERROR: Unknown LLM provider '{provider_name}' configured in .env.\n"
              f"Supported providers: {', '.join(PROVIDER_PROFILES.keys())}", file=sys.stderr)
        sys.exit(1)
        
    profile = PROVIDER_PROFILES[provider_name]
    
    # 1. Resolve API Key
    api_key = os.environ.get(profile["env_key"], "")
    if not api_key:
        print(f"ERROR: API Key '{profile['env_key']}' for provider '{provider_name}' "
              f"is not set in your .env file.", file=sys.stderr)
        sys.exit(1)
        
    # 2. Resolve URL
    base_url = os.environ.get("AUTOBOOK_API_BASE_URL", "").strip()
    if not base_url:
        base_url = profile["default_url"]
    url = base_url.rstrip("/") + profile["endpoint_suffix"]
    
    # 3. Resolve Model (Specific Env -> Generic Env -> Curated Default)
    if is_review:
        model = os.environ.get(profile["env_review_model"], "")
        if not model:
            model = os.environ.get("AUTOBOOK_REVIEW_MODEL", "")
    elif is_judge:
        model = os.environ.get(profile["env_judge_model"], "")
        if not model:
            model = os.environ.get("AUTOBOOK_JUDGE_MODEL", "")
    else:
        model = os.environ.get(profile["env_writer_model"], "")
        if not model:
            model = os.environ.get("AUTOBOOK_WRITER_MODEL", "")
        
    if not model:
        model = profile["default_model"]
        
    # 4. Build Request Headers and Payload
    headers = {}
    payload = {}
    
    if provider_name == "anthropic":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "context-1m-2025-08-07",
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": 8000 if (is_judge or is_review) else 16000,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [{"role": "user", "content": prompt}],
        }
    else:
        # Standard OpenAI-Compatible payloads (OpenAI, Gemini, OpenRouter)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        
        # Add OpenRouter specific discovery headers
        if provider_name == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/aleemerich/autobook"
            headers["X-Title"] = "Autobook"
            
        payload = {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }
        
        # OpenRouter/Gemini/OpenAI limits handling
        # OpenRouter or Gemini may have varying default max_tokens, but let's let server decide
        # or supply standard sensible outputs
        if is_judge or is_review:
            payload["max_tokens"] = 4000
        else:
            payload["max_tokens"] = 8000
            
    # 5. Call API
    try:
        print(f"[LLM] Requesting model '{model}' from provider '{provider_name}'...", file=sys.stderr)
        print("[LLM] Waiting for API response (this may take up to 10 minutes for long generations)...", file=sys.stderr)
        # Timeout 600s is crucial for long writer generations
        with httpx.Client() as client:
            resp = client.post(url, headers=headers, json=payload, timeout=600)
            
            print(f"[LLM] Response received! Status: {resp.status_code}. Processing content...", file=sys.stderr)
            # Print helpful error details on failure
            if resp.status_code != 200:
                print(f"ERROR: API request failed with status code {resp.status_code}", file=sys.stderr)
                print(f"Response: {resp.text}", file=sys.stderr)
                resp.raise_for_status()
                
            data = resp.json()
            
            # 6. Extract Response
            if provider_name == "anthropic":
                return data["content"][0]["text"]
            else:
                return data["choices"][0]["message"]["content"]
                
    except Exception as e:
        print(f"FATAL ERROR during LLM API call: {e}", file=sys.stderr)
        raise
