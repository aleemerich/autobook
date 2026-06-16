from pathlib import Path
from typing import List, Any
from pipelines.book_generation_steps.planning import (
    build_roadmap_text,
    build_title_instruction,
    build_beat_draft_prompt,
    build_chapter_draft_prompt
)

def load_previous_beat_context(tmp_dir: Path, b_idx: int, prev_tail: str) -> str:
    """Retorna a cauda do beat anterior (últimos 3 parágrafos) ou prev_tail se for o beat 1 (1-indexed)."""
    if b_idx > 1:
        prev_beat_file = tmp_dir / f"beat_{b_idx-1:02d}_raw.md"
        if prev_beat_file.exists():
            last_beat_text = prev_beat_file.read_text(encoding="utf-8").strip()
            paragraphs = [p.strip() for p in last_beat_text.split('\n\n') if p.strip()]
            last_paragraphs = paragraphs[-3:] if len(paragraphs) > 3 else paragraphs
            return "\n\n".join(last_paragraphs)
        return ""
    return prev_tail

def save_raw_beat(tmp_dir: Path, b_idx: int, content: str) -> Path:
    """Salva o texto do beat bruto em beat_XX_raw.md."""
    beat_file = tmp_dir / f"beat_{b_idx:02d}_raw.md"
    beat_file.write_text(content, encoding="utf-8")
    return beat_file

def concatenate_raw_beats(tmp_dir: Path, total_beats: int) -> str:
    """Concatena todos os beats brutos e salva em chapter_raw.md."""
    chapter_raw_file = tmp_dir / "chapter_raw.md"
    beats_content = []
    for b_idx in range(1, total_beats + 1):
        beat_file = tmp_dir / f"beat_{b_idx:02d}_raw.md"
        if beat_file.exists():
            beats_content.append(beat_file.read_text(encoding="utf-8").strip())
    chapter_raw_text = "\n\n".join(beats_content)
    chapter_raw_file.write_text(chapter_raw_text, encoding="utf-8")
    return chapter_raw_text

def run_beat_drafting(
    tmp_dir: Path,
    ch: int,
    ch_title: str,
    beats: List[str],
    prev_tail: str,
    voice_text: str,
    world_text: str,
    canon_text: str,
    characters_text: str,
    drafting_agent: Any
) -> str:
    """Gera o capítulo beat a beat usando o agente de escrita."""
    print(f"[DraftChaptersStep] Found {len(beats)} beats in outline. Generating raw beats.")
    for b_idx, beat_text in enumerate(beats, 1):
        print(f"  [Beat {b_idx}/{len(beats)}] Drafting raw beat...")
        previous_beat_context = load_previous_beat_context(tmp_dir, b_idx, prev_tail)
        roadmap_text = build_roadmap_text(beats, b_idx)
        title_instruction = build_title_instruction(ch_title, b_idx)
        
        draft_prompt = build_beat_draft_prompt(
            b_idx=b_idx,
            ch=ch,
            title_instruction=title_instruction,
            voice_text=voice_text,
            world_text=world_text,
            canon_text=canon_text,
            roadmap_text=roadmap_text,
            beat_text=beat_text,
            previous_beat_context=previous_beat_context,
            characters_text=characters_text
        )
        raw_beat = drafting_agent.execute(draft_prompt)
        save_raw_beat(tmp_dir, b_idx, raw_beat)
        
    return concatenate_raw_beats(tmp_dir, len(beats))

def run_chapter_fallback_drafting(
    tmp_dir: Path,
    ch: int,
    ch_outline: str,
    prev_tail: str,
    characters_text: str,
    drafting_agent: Any
) -> str:
    """Gera o capítulo completo de uma vez (fallback quando não há beats)."""
    print("[DraftChaptersStep] No beats found. Writing the entire chapter in one go.")
    draft_prompt = build_chapter_draft_prompt(
        ch=ch,
        ch_outline=ch_outline,
        prev_tail=prev_tail,
        characters_text=characters_text
    )
    chapter_raw_text = drafting_agent.execute(draft_prompt)
    chapter_raw_file = tmp_dir / "chapter_raw.md"
    chapter_raw_file.write_text(chapter_raw_text, encoding="utf-8")
    return chapter_raw_text
