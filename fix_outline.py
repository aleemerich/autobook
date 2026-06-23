#!/usr/bin/env python3
import os
import sys
import re
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")

sys.path.insert(0, str(BASE_DIR))
from llm import call_llm
from prompt_loader import load_continuity_config


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


def fix_outline_chunk(chunk_content: str, report_content: str, writer_model: str) -> str:
    fix_config = load_continuity_config().get("fix_outline", {})
    system_prompt = fix_config["system_prompt"]
    user_prompt = fix_config["user_prompt"].format(
        report_content=report_content,
        chunk_content=chunk_content,
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
) -> str:
    preamble, chunks = split_outline_chunks(outline_content, chunk_size)
    if not chunks:
        return outline_content

    fixed_chunks = []
    for idx, chunk in enumerate(chunks, start=1):
        chapter_nums = {num for num, _block in chunk if num > 0}
        chunk_content = "".join(block for _num, block in chunk)
        chunk_report = filter_report_for_chapters(report_content, chapter_nums)
        print(
            f"[INFO] Fixing outline chunk {idx}/{len(chunks)} "
            f"(chapters {min(chapter_nums) if chapter_nums else '?'}-"
            f"{max(chapter_nums) if chapter_nums else '?'})..."
        )
        fixed_chunks.append(fix_outline_chunk(chunk_content, chunk_report, writer_model))

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

    try:
        resolved_outline = fix_outline_content(
            outline_content=outline_content,
            report_content=report_content,
            writer_model=writer_model,
            chunk_size=chunk_size,
        )
        outline_path.write_text(resolved_outline, encoding="utf-8")
        print("[SUCCESS] outline.md has been rewritten with continuity fixes!")
    except Exception as e:
        print(f"[ERROR] Failed to fix outline via LLM: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
