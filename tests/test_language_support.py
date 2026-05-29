#!/usr/bin/env python3
"""
tests/test_language_support.py — Unit tests for the bilingual support (PT-BR / EN).
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from llm import call_llm
from evaluate import slop_score


# ---------------------------------------------------------------------------
# 1. LLM Language Directive Injection Tests
# ---------------------------------------------------------------------------

@patch("httpx.Client.post")
def test_llm_directive_portuguese(mock_post):
    """Ensures call_llm injects the Portuguese directive when AUTOBOOK_LANGUAGE=PT-BR."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Simulação de resposta em português."}}]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "AUTOBOOK_LANGUAGE": "PT-BR"
    }):
        call_llm("Olá!", "Aja como um escritor de romance.")
        
        # Check that the system prompt payload has the PT-BR language directive
        called_args, called_kwargs = mock_post.call_args
        payload = called_kwargs["json"]
        system_msg = payload["messages"][0]["content"]
        
        assert "[CRITICAL LANGUAGE DIRECTIVE]" in system_msg
        assert "Portuguese (PT-BR)" in system_msg


@patch("httpx.Client.post")
def test_llm_directive_english(mock_post):
    """Ensures call_llm injects the English directive when AUTOBOOK_LANGUAGE=EN."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Simulation of response in English."}}]
    }
    mock_post.return_value = mock_resp

    with patch.dict(os.environ, {
        "AUTOBOOK_PROVIDER": "openai",
        "OPENAI_API_KEY": "test-key",
        "AUTOBOOK_LANGUAGE": "EN"
    }):
        call_llm("Hello!", "Act as a novel writer.")
        
        called_args, called_kwargs = mock_post.call_args
        payload = called_kwargs["json"]
        system_msg = payload["messages"][0]["content"]
        
        assert "[CRITICAL LANGUAGE DIRECTIVE]" in system_msg
        assert "English (EN)" in system_msg


# ---------------------------------------------------------------------------
# 2. Slop & Cliché Mechanical Detection Tests (PT-BR / EN)
# ---------------------------------------------------------------------------

def test_slop_score_portuguese_detection():
    """Ensures evaluate.slop_score detects Portuguese-specific slop and clichés when PT-BR is set."""
    # Clean text in Portuguese
    clean_text = (
        "O vento estava frio. Carregava o cheiro de terra molhada do vale abaixo, "
        "soprando por entre os pinheiros altos. Cass puxou seu manto de lã para mais "
        "perto dos ombros e deu um passo à frente. O caminho era estreito. Um deslize, "
        "e ele cairia no desfiladeiro escuro. Ele precisava chegar à vila antes do anoitecer."
    )
    
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "PT-BR"}):
        clean_result = slop_score(clean_text)
        assert clean_result["slop_penalty"] == 0.0

    # Sloppy text in Portuguese containing typical GPT clichés and banned words
    sloppy_text = (
        "Ele soltou um suspiro que não sabia que estava segurando. "
        "Nós precisamos utilizar e alavancar a tapeçaria deste projeto. "
        "Ela sentiu um vislumbre de medo com o coração martelando no peito."
    )
    
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "PT-BR"}):
        sloppy_result = slop_score(sloppy_text)
        
        # Check that slop penalty is high and correct hits are recorded
        assert sloppy_result["slop_penalty"] > 0.0
        
        # Banned words caught
        caught_banned = [w for w, _ in sloppy_result["tier1_hits"]]
        assert "utilizar" in caught_banned or "alavancar" in caught_banned or "tapeçaria" in caught_banned
        
        # Fiction tells caught (e.g. breath holding or heart pounding)
        fiction_tells = [pattern for pattern, _ in sloppy_result["fiction_ai_tells"]]
        assert any("suspiro" in p or "segurando" in p or "coração" in p or "martelando" in p for p in fiction_tells)


def test_slop_score_cross_language_isolation():
    """Ensures Portuguese clichês are NOT penalized under English mode and vice versa."""
    portuguese_slop_text = "Ele soltou um suspiro que não sabia que estava segurando."
    
    # 1. Under EN mode, Portuguese clichés shouldn't trigger fiction tells
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "EN"}):
        en_result = slop_score(portuguese_slop_text)
        assert len(en_result["fiction_ai_tells"]) == 0
        
    # 2. Under PT-BR mode, it should be detected
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "PT-BR"}):
        pt_result = slop_score(portuguese_slop_text)
        assert len(pt_result["fiction_ai_tells"]) > 0


# ---------------------------------------------------------------------------
# 3. Prompt Loader & i18n Fallback Tests
# ---------------------------------------------------------------------------

def test_prompt_loader_resolution():
    """Ensures prompt_loader loads directives and slop correctly from the new folder structure."""
    from prompt_loader import load_prompt, load_slop_config
    
    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "PT-BR"}):
        directive = load_prompt("directives.txt")
        assert "Portuguese (PT-BR)" in directive
        
        slop = load_slop_config()
        assert "utilizar" in slop["tier1_banned"]

    with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "EN"}):
        directive = load_prompt("directives.txt")
        assert "English (EN)" in directive
        
        slop = load_slop_config()
        assert "delve" in slop["tier1_banned"]


def test_prompt_loader_fallback():
    """Ensures prompt_loader falls back to EN when a specific file is missing from PT-BR folder."""
    from prompt_loader import load_prompt
    import shutil
    from pathlib import Path
    
    # 1. Create a dummy file only in prompts/EN/ folder
    dummy_file_en = Path("prompts/EN/dummy_test_fallback.txt")
    dummy_file_en.write_text("Hello Fallback World!", encoding="utf-8")
    
    try:
        # 2. Under PT-BR environment, try loading the dummy file. It should fall back to EN.
        with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "PT-BR"}):
            loaded_content = load_prompt("dummy_test_fallback.txt")
            assert loaded_content == "Hello Fallback World!"
            
        # 3. Try to load with fallback disabled. It should raise FileNotFoundError.
        with patch.dict(os.environ, {"AUTOBOOK_LANGUAGE": "PT-BR"}):
            with pytest.raises(FileNotFoundError):
                load_prompt("dummy_test_fallback.txt", fallback_to_en=False)
                
    finally:
        # Cleanup
        if dummy_file_en.exists():
            dummy_file_en.unlink()

