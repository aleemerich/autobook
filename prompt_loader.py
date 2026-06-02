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
        
    lang = get_active_language()
    is_pt = (lang == "PT-BR")
    
    lines = []
    if is_pt:
        lines.append("- CRÍTICO: Não use NENHUMA das seguintes palavras banidas (Tier 1 Banned): " + ", ".join(config.get("tier1_banned", [])))
        lines.append("- CRÍTICO: Evite ao máximo usar palavras suspeitas de IA (Tier 2 Suspicious): " + ", ".join(config.get("tier2_suspicious", [])))
        if config.get("tier3_filler"):
            lines.append("- Evite expressões de preenchimento redundantes (Tier 3 Filler): " + ", ".join(config.get("tier3_filler", [])))
        if config.get("transition_openers"):
            lines.append("- Evite iniciar parágrafos com conectivos de transição abusivos: " + ", ".join(config.get("transition_openers", [])))
        if config.get("fiction_ai_tells"):
            lines.append("- Proibido usar clichês literários de IA (Fiction AI Tells): " + ", ".join(config.get("fiction_ai_tells", [])))
        if config.get("structural_ai_tics"):
            lines.append("- Proibido usar estruturas e tiques retóricos típicos de IA (Structural AI Tics): " + ", ".join(config.get("structural_ai_tics", [])))
        lines.append("- PONTUAÇÃO E ESTILO (CRÍTICO): Limite severamente o uso de travessões (—) e hifens duplos. A densidade de travessões deve ser MENOR que 15 a cada 1000 palavras (use-os apenas para falas reais e interrupções dramáticas de diálogos, NUNCA para introduzir explicações ou apostos na narração).")
        lines.append("- VARIAÇÃO SINTÁTICA: Varie deliberadamente o comprimento das sentenças. Evite sentenças consecutivas com a mesma estrutura sintática ou quantidade similar de palavras.")
        lines.append("- SHOW, DON'T TELL: Mostre reações físicas e sensoriais em vez de apenas nomear/rotular as emoções dos personagens (evite 'sentiu medo', 'parecia triste').")
    else:
        lines.append("- CRITICAL: Do NOT use ANY of the following banned words (Tier 1 Banned): " + ", ".join(config.get("tier1_banned", [])))
        lines.append("- CRITICAL: Avoid using AI-associated suspicious words (Tier 2 Suspicious): " + ", ".join(config.get("tier2_suspicious", [])))
        if config.get("tier3_filler"):
            lines.append("- Avoid redundant filler phrases (Tier 3 Filler): " + ", ".join(config.get("tier3_filler", [])))
        if config.get("transition_openers"):
            lines.append("- Avoid opening paragraphs with transition words: " + ", ".join(config.get("transition_openers", [])))
        if config.get("fiction_ai_tells"):
            lines.append("- Avoid typical AI fiction tropes and tells: " + ", ".join(config.get("fiction_ai_tells", [])))
        if config.get("structural_ai_tics"):
            lines.append("- Forbidden structural and rhetorical AI tics: " + ", ".join(config.get("structural_ai_tics", [])))
        lines.append("- PUNCTUATION & STYLE (CRITICAL): Limit the use of em-dashes (—). The density of em-dashes must be LESS than 15 per 1000 words (use them only for actual dialogue and real interruptions, not for explanatory side-notes in narration).")
        lines.append("- SENTENCE VARIATION: Deliberately vary sentence lengths. Avoid consecutive sentences of the same length.")
        lines.append("- SHOW, DON'T TELL: Show physical/sensory reactions rather than naming/telling emotions (e.g. avoid 'he felt sad', 'she looked nervous').")
        
    return "\n".join(lines)


