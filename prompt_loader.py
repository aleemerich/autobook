#!/usr/bin/env python3
"""
prompt_loader.py — Central utility to load localized prompt templates and configuration files.

Provides robust fallback mechanism to "EN" if the active language file is missing.
"""

import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
PROMPTS_DIR = BASE_DIR / "prompts"


def get_active_language() -> str:
    """Returns the configured AUTOBOOK_LANGUAGE (PT-BR, EN, etc.), normalized to uppercase."""
    return os.environ.get("AUTOBOOK_LANGUAGE", "EN").upper()


def load_prompt(prompt_name: str, fallback_to_en: bool = True) -> str:
    """
    Load a text prompt from prompts/{LANG}/{prompt_name}.
    Falls back gracefully to prompts/EN/{prompt_name} if missing.
    """
    lang = get_active_language()
    
    # Clean file path resolution
    prompt_file = PROMPTS_DIR / lang / prompt_name
    
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
        
    if fallback_to_en and lang != "EN":
        fallback_file = PROMPTS_DIR / "EN" / prompt_name
        if fallback_file.exists():
            return fallback_file.read_text(encoding="utf-8")
            
    raise FileNotFoundError(
        f"Prompt file '{prompt_name}' not found under active language '{lang}' "
        f"nor English fallback 'EN' in directory: {PROMPTS_DIR}"
    )


def load_slop_config() -> dict:
    """
    Load the slop detection JSON configuration for the active language.
    Falls back gracefully to EN if missing.
    """
    lang = get_active_language()
    slop_file = PROMPTS_DIR / lang / "slop.json"
    
    if not slop_file.exists() and lang != "EN":
        slop_file = PROMPTS_DIR / "EN" / "slop.json"
        
    if not slop_file.exists():
        raise FileNotFoundError(f"Slop configuration 'slop.json' not found in EN fallback or {lang}")
        
    with open(slop_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_genre_rules() -> str:
    """
    Load the genre-specific rules and instructions from genres/{LANG}/{genre}.txt.
    Falls back to EN if active language is missing.
    Falls back to 'drama' if the selected genre is missing or invalid.
    """
    lang = get_active_language()
    genre = os.environ.get("AUTOBOOK_GENRE", "drama").lower().strip()
    
    genres_dir = BASE_DIR / "genres"
    
    # 1. Try localizing the requested genre
    genre_file = genres_dir / lang / f"{genre}.txt"
    if genre_file.exists():
        return genre_file.read_text(encoding="utf-8")
        
    # 2. Try falling back to English for the requested genre
    if lang != "EN":
        fallback_genre_file = genres_dir / "EN" / f"{genre}.txt"
        if fallback_genre_file.exists():
            return fallback_genre_file.read_text(encoding="utf-8")
            
    # 3. Fallback to default 'drama' in active language
    default_file = genres_dir / lang / "drama.txt"
    if default_file.exists():
        return default_file.read_text(encoding="utf-8")
        
    # 4. Final emergency fallback to 'drama' in English
    final_file = genres_dir / "EN" / "drama.txt"
    if final_file.exists():
        return final_file.read_text(encoding="utf-8")
        
    raise FileNotFoundError("Critical default genre file 'drama.txt' not found under EN fallback.")

