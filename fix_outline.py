#!/usr/bin/env python3
import os
import sys
import re
import json
from pathlib import Path
from dotenv import load_dotenv

from llm import call_llm
from prompt_loader import load_continuity_config

BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")


def _chapter_heading_re():
    parser_config = load_continuity_config().get("outline_parser", {})
    terms = parser_config.get("chapter_heading_terms", ["Chapter", "Ch"])
    separators = parser_config.get("chapter_heading_separators", [":", "-", "–", "—"])
    term_pattern = "|".join(re.escape(term) for term in terms)
    separator_pattern = "".join(re.escape(separator) for separator in separators)
    return re.compile(
        rf'^###\s+(?:{term_pattern})\s+(\d+)\s*[{separator_pattern}]\s*(.*)$',
        flags=re.MULTILINE | re.IGNORECASE,
    )


def _strip_markdown_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r'^```(?:markdown)?\s*', '', cleaned)
    if cleaned.endswith("```"):
        cleaned = re.sub(r'\s*```$', '', cleaned)
    return cleaned.strip()


def split_outline_chunks(outline_content: str, chunk_size: int) -> tuple[str, list[list[tuple[int, str]]]]:
    """Split outline into a preamble and chapter chunks preserving markdown blocks."""
    matches = list(_chapter_heading_re().finditer(outline_content))
    if not matches:
        return "", [[(0, outline_content)]]

    preamble = outline_content[:matches[0].start()]
    chapter_blocks = []
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(outline_content)
        chapter_blocks.append((int(match.group(1)), outline_content[match.start():end]))

    chunks = [
        chapter_blocks[idx:idx + chunk_size]
        for idx in range(0, len(chapter_blocks), chunk_size)
    ]
    return preamble, chunks


def filter_report_for_chapters(report_content: str, chapter_nums: set[int]) -> str:
    """Keep only continuity report issues that touch the chunk's chapters."""
    try:
        report = json.loads(report_content)
    except json.JSONDecodeError:
        return report_content

    filtered = dict(report)
    inconsistencies = report.get("inconsistencies", [])
    filtered["inconsistencies"] = [
        inc for inc in inconsistencies
        if chapter_nums.intersection(set(inc.get("chapters", [])))
    ]
    return json.dumps(filtered, indent=2, ensure_ascii=False)


def _env_flag(name: str, default: bool = True) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() not in {"0", "false", "no", "n", "off"}


def _truncate_for_prompt(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text.strip()
    return text[:max_chars].rstrip() + "\n[...]"


def build_compact_outline_map(
    chapter_blocks: list[tuple[int, str]],
    max_chars_per_chapter: int = 900,
) -> str:
    """Build a compact global map that preserves original chapter headings."""
    parts = []
    for chapter_num, block in chapter_blocks:
        parts.append(f"### {chapter_num}\n{_truncate_for_prompt(block, max_chars_per_chapter)}")
    return "\n\n".join(parts).strip()


def _flatten_chunks(chunks: list[list[tuple[int, str]]]) -> list[tuple[int, str]]:
    return [chapter_block for chunk in chunks for chapter_block in chunk]


def _neighbor_context(
    chunks: list[list[tuple[int, str]]],
    chunk_index: int,
    overlap_chapters: int,
) -> tuple[str, str]:
    if overlap_chapters <= 0:
        return "", ""

    previous_blocks = chunks[chunk_index - 1][-overlap_chapters:] if chunk_index > 0 else []
    next_blocks = chunks[chunk_index + 1][:overlap_chapters] if chunk_index + 1 < len(chunks) else []
    previous_context = "".join(block for _num, block in previous_blocks).strip()
    next_context = "".join(block for _num, block in next_blocks).strip()
    return previous_context, next_context


def create_global_outline_plan(
    outline_content: str,
    report_content: str,
    writer_model: str,
    chunk_size: int = 4,
    max_chars_per_chapter: int = 900,
) -> str:
    """Create a compact cross-chapter repair plan before chunk-level rewrites."""
    _preamble, chunks = split_outline_chunks(outline_content, chunk_size)
    chapter_blocks = _flatten_chunks(chunks)
    compact_outline_map = build_compact_outline_map(
        chapter_blocks,
        max_chars_per_chapter=max_chars_per_chapter,
    )
    return create_global_plan_from_map(compact_outline_map, report_content, writer_model)


def create_global_plan_from_map(
    compact_outline_map: str,
    report_content: str,
    writer_model: str,
) -> str:
    fix_config = load_continuity_config().get("fix_outline", {})
    system_prompt = fix_config["global_plan_system_prompt"]
    user_prompt = fix_config["global_plan_user_prompt"].format(
        report_content=report_content,
        compact_outline_map=compact_outline_map,
    )

    global_plan = call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.2,
        override_model=writer_model,
    )
    return _strip_markdown_fences(global_plan)


def fix_outline_chunk(
    chunk_content: str,
    report_content: str,
    writer_model: str,
    global_plan: str = "",
    previous_context: str = "",
    next_context: str = "",
) -> str:
    fix_config = load_continuity_config().get("fix_outline", {})
    system_prompt = fix_config["system_prompt"]
    prompt_template = fix_config["user_prompt"]
    if global_plan:
        prompt_template = fix_config.get("chunk_with_plan_user_prompt", prompt_template)

    user_prompt = prompt_template.format(
        report_content=report_content,
        chunk_content=chunk_content,
        global_plan=global_plan,
        previous_context=previous_context,
        next_context=next_context,
    )

    resolved_chunk = call_llm(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.3,
        override_model=writer_model
    )
    return _strip_markdown_fences(resolved_chunk)


def fix_outline_content(
    outline_content: str,
    report_content: str,
    writer_model: str,
    chunk_size: int = 4,
    global_plan: str | None = None,
    overlap_chapters: int = 1,
    max_chars_per_chapter: int = 900,
) -> str:
    preamble, chunks = split_outline_chunks(outline_content, chunk_size)
    if not chunks:
        return outline_content

    if global_plan is None and _env_flag("FIX_OUTLINE_GLOBAL_PLAN", default=True):
        print("[INFO] Creating global outline repair plan...")
        global_plan = create_global_outline_plan(
            outline_content=outline_content,
            report_content=report_content,
            writer_model=writer_model,
            chunk_size=chunk_size,
            max_chars_per_chapter=max_chars_per_chapter,
        )
    elif global_plan is None:
        global_plan = ""

    fixed_chunks = []
    for chunk_idx, chunk in enumerate(chunks):
        chapter_nums = {num for num, _block in chunk if num > 0}
        chunk_content = "".join(block for _num, block in chunk)
        chunk_report = filter_report_for_chapters(report_content, chapter_nums)
        previous_context, next_context = _neighbor_context(
            chunks,
            chunk_idx,
            overlap_chapters,
        )
        print(
            f"[INFO] Fixing outline chunk {chunk_idx + 1}/{len(chunks)} "
            f"(chapters {min(chapter_nums) if chapter_nums else '?'}-"
            f"{max(chapter_nums) if chapter_nums else '?'})..."
        )
        fixed_chunks.append(
            fix_outline_chunk(
                chunk_content=chunk_content,
                report_content=chunk_report,
                writer_model=writer_model,
                global_plan=global_plan,
                previous_context=previous_context,
                next_context=next_context,
            )
        )

    return (preamble + "\n\n".join(fixed_chunks)).strip() + "\n"


def main():
    outline_path = BASE_DIR / "book_data" / "outline.md"
    report_path = BASE_DIR / "logs" / "eval_logs" / "continuity_report.json"

    if not outline_path.exists():
        print(f"[ERROR] outline.md not found at {outline_path}")
        sys.exit(1)
    if not report_path.exists():
        print(f"[ERROR] continuity_report.json not found at {report_path}")
        sys.exit(1)

    outline_content = outline_path.read_text(encoding="utf-8")
    report_content = report_path.read_text(encoding="utf-8")

    print("[INFO] Calling LLM to resolve continuity inconsistencies in outline.md by chunks...")
    writer_model = os.environ.get("AUTOBOOK_WRITER_MODEL", "openrouter/owl-alpha")
    chunk_size = int(os.environ.get("FIX_OUTLINE_CHUNK_CHAPTERS", "4"))
    overlap_chapters = int(os.environ.get("FIX_OUTLINE_CONTEXT_CHAPTERS", "1"))
    max_chars_per_chapter = int(os.environ.get("FIX_OUTLINE_MAP_CHARS_PER_CHAPTER", "900"))

    try:
        resolved_outline = fix_outline_content(
            outline_content=outline_content,
            report_content=report_content,
            writer_model=writer_model,
            chunk_size=chunk_size,
            overlap_chapters=overlap_chapters,
            max_chars_per_chapter=max_chars_per_chapter,
        )
        outline_path.write_text(resolved_outline, encoding="utf-8")
        print("[SUCCESS] outline.md has been rewritten with continuity fixes!")
    except Exception as e:
        print(f"[ERROR] Failed to fix outline via LLM: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
