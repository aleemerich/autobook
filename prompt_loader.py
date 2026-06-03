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


def load_slop_rules_instruction() -> str:
    """
    Load the slop configuration and format it as clear, readable constraints
    for the LLM writer prompt to avoid slop penalties.
    """
    try:
        config = load_slop_config()
    except Exception as e:
        return f"Warning: could not load slop config: {e}"
        
    templates = config.get("instruction_templates", {})
    if not templates:
        # Fallback to English defaults for backward compatibility or missing templates
        templates = {
            "tier1_banned": "CRITICAL: Do NOT use ANY of the following banned words (Tier 1 Banned): {words}",
            "tier2_suspicious": "CRITICAL: Avoid using AI-associated suspicious words (Tier 2 Suspicious): {words}",
            "tier3_filler": "Avoid redundant filler phrases (Tier 3 Filler): {words}",
            "transition_openers": "Avoid opening paragraphs with transition words: {words}",
            "fiction_ai_tells": "Avoid typical AI fiction tropes and tells: {words}",
            "structural_ai_tics": "Forbidden structural and rhetorical AI tics: {words}",
            "punctuation_style": "PUNCTUATION & STYLE (CRITICAL): Limit the use of em-dashes (—). The density of em-dashes must be LESS than 15 per 1000 words (use them only for actual dialogue and real interruptions, not for explanatory side-notes in narration).",
            "sentence_variation": "SENTENCE VARIATION: Deliberately vary sentence lengths. Avoid consecutive sentences of the same length.",
            "show_dont_tell": "SHOW, DON'T TELL: Show physical/sensory reactions rather than naming/telling emotions (e.g. avoid 'he felt sad', 'she looked nervous')."
        }
        
    lines = []
    
    if "tier1_banned" in templates and config.get("tier1_banned"):
        lines.append("- " + templates["tier1_banned"].format(words=", ".join(config["tier1_banned"])))
        
    if "tier2_suspicious" in templates and config.get("tier2_suspicious"):
        lines.append("- " + templates["tier2_suspicious"].format(words=", ".join(config["tier2_suspicious"])))
        
    if "tier3_filler" in templates and config.get("tier3_filler"):
        lines.append("- " + templates["tier3_filler"].format(words=", ".join(config["tier3_filler"])))
        
    if "transition_openers" in templates and config.get("transition_openers"):
        lines.append("- " + templates["transition_openers"].format(words=", ".join(config["transition_openers"])))
        
    if "fiction_ai_tells" in templates and config.get("fiction_ai_tells"):
        lines.append("- " + templates["fiction_ai_tells"].format(words=", ".join(config["fiction_ai_tells"])))
        
    if "structural_ai_tics" in templates and config.get("structural_ai_tics"):
        lines.append("- " + templates["structural_ai_tics"].format(words=", ".join(config["structural_ai_tics"])))
        
    if "punctuation_style" in templates:
        lines.append("- " + templates["punctuation_style"])
        
    if "sentence_variation" in templates:
        lines.append("- " + templates["sentence_variation"])
        
    if "show_dont_tell" in templates:
        lines.append("- " + templates["show_dont_tell"])
        
    return "\n".join(lines)



