#!/usr/bin/env python3
"""
Revision chapter generator. Rewrites a chapter from a specific revision brief.
Usage: python gen_revision.py <chapter_num> <brief_file>
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

def _load_book_title(base_dir: Path = BASE_DIR) -> str:
    """Load the current workspace title, falling back when no workspace exists."""
    from workspace.project import load_workspace_metadata

    metadata = load_workspace_metadata(base_dir)
    if metadata is None:
        return "Untitled Book"
    return metadata["title"]


def _build_word_budget(old_text: str) -> str:
    """Build a conservative word budget instruction from the existing draft."""
    old_word_count = len(old_text.split())
    if old_word_count <= 0:
        return (
            "No existing draft word count is available. Keep the revised chapter "
            "concise and proportional to the requested changes."
        )

    min_words = max(1, int(round(old_word_count * 0.85)))
    max_words = max(min_words, int(round(old_word_count * 1.15)))
    return (
        f"The existing draft has {old_word_count} words. Keep the revised chapter "
        f"between {min_words} and {max_words} words unless the revision brief "
        "explicitly asks for major expansion or cuts."
    )


def _validate_revision_result(result: object, chapter_num: int) -> str:
    """Return valid revision text or raise a clear error before writing files."""
    if not isinstance(result, str):
        raise ValueError(
            f"Revision model returned no text for chapter {chapter_num}. "
            f"Expected str, got {type(result).__name__}."
        )
    if not result.strip():
        raise ValueError(f"Revision model returned empty text for chapter {chapter_num}.")
    return result


def call_writer(prompt, temperature=0.8, max_tokens=16000):
    """Call the unified writer LLM via llm.py and return response text."""
    from llm import call_llm
    from prompt_loader import load_prompt
    try:
        system = load_prompt("gen_revision_system.txt")
    except FileNotFoundError:
        system = (
            "You are rewriting a fantasy novel chapter based on a specific revision brief. "
            "You follow the brief exactly. You preserve the voice, world, and characters "
            "from the existing draft while making the structural changes specified. "
            "You write the FULL chapter. Do not truncate or summarize."
        )
    return call_llm(prompt=prompt, system_prompt=system, temperature=temperature, is_judge=False)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Revision chapter generator.")
    parser.add_argument("chapter_num", type=int, help="Chapter number")
    parser.add_argument("brief_file", type=str, help="Path to brief file")
    parser.add_argument("--temperature", type=float, default=0.8, help="Creative temperature")
    args = parser.parse_args()
    
    ch_num = args.chapter_num
    brief_file = args.brief_file
    temperature = args.temperature
    
    voice = (BASE_DIR / "book_data" / "voice.md").read_text(encoding="utf-8")
    characters = (BASE_DIR / "book_data" / "characters.md").read_text(encoding="utf-8")
    world = (BASE_DIR / "book_data" / "world.md").read_text(encoding="utf-8")
    brief = Path(brief_file).read_text(encoding="utf-8")
    
    # Load adjacent chapters for continuity
    prev_path = BASE_DIR / "chapters" / f"ch_{ch_num - 1:02d}.md"
    next_path = BASE_DIR / "chapters" / f"ch_{ch_num + 1:02d}.md"
    prev_tail = prev_path.read_text(encoding="utf-8")[-2000:] if prev_path.exists() else "(first chapter)"
    next_head = next_path.read_text(encoding="utf-8")[:1500] if next_path.exists() else "(last chapter)"
    
    # Load old version if exists
    old_path = BASE_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    old_text = old_path.read_text(encoding="utf-8") if old_path.exists() else "(no existing draft)"
    word_budget = _build_word_budget(old_text if old_path.exists() else "")
    book_title = _load_book_title(BASE_DIR)
    
    from prompt_loader import load_prompt, load_genre_rules, load_slop_rules_instruction
    try:
        prompt_template = load_prompt("gen_revision_user.txt")
        genre_rules = load_genre_rules()
        slop_rules = load_slop_rules_instruction()
        prompt = prompt_template.format(
            ch_num=ch_num,
            book_title=book_title,
            brief=brief,
            voice=voice,
            characters=characters,
            world=world,
            prev_tail=prev_tail,
            next_head=next_head,
            old_text=old_text,
            word_budget=word_budget,
            genre_rules=genre_rules,
            slop_rules=slop_rules
        )
    except Exception as e:
        print(f"WARNING: failed to load user prompt template: {e}, falling back to hardcoded template", file=sys.stderr)
        prompt = f"""Rewrite Chapter {ch_num} of "{book_title}".

REVISION BRIEF (follow this exactly):
{brief}

VOICE DEFINITION:
{voice}

CHARACTER REGISTRY:
{characters}

WORLD BIBLE:
{world}

PREVIOUS CHAPTER ENDING (maintain continuity):
{prev_tail}

NEXT CHAPTER OPENING (end so this flows into it):
{next_head}

THE EXISTING DRAFT (use as raw material -- keep what works, cut what doesn't):
{old_text}

WORD BUDGET:
{word_budget}

ANTI-PATTERN RULES:
- NO triadic sensory lists (X. Y. Z.)
- NO "He did not [verb]" more than once
- NO "He thought about [X]" constructions
- NO "the way [X] did [Y]" more than twice
- NO "not X, but Y" formula in narration
- NO over-explaining after showing
- MAX 2 section breaks
- At least one moment that genuinely surprises
- 70%+ in-scene (dialogue and action, not summary)
- Dialogue should sound like speech, not prose

Write the FULL revised chapter now."""

    print(f"Rewriting Chapter {ch_num}...", file=sys.stderr)
    result = _validate_revision_result(call_writer(prompt, temperature=temperature), ch_num)
    
    out_path = BASE_DIR / "chapters" / f"ch_{ch_num:02d}.md"
    out_path.write_text(result, encoding="utf-8")
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)

if __name__ == "__main__":
    main()
