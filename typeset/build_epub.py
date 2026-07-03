#!/usr/bin/env python3
"""Build an EPUB file from generated chapter Markdown files."""
import os
import re
import shutil
import subprocess
from pathlib import Path

try:
    from typeset.build_tex import _env_value, _load_env_config, load_book_metadata
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from build_tex import _env_value, _load_env_config, load_book_metadata

BASE_DIR = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = BASE_DIR / "chapters"
OUT_DIR = BASE_DIR / "typeset"
EPUB_STYLE = OUT_DIR / "epub_style.css"
DEFAULT_OUTPUT = OUT_DIR / "novel.epub"
COVER_IMAGE = BASE_DIR / "art" / "epub_front_cover.png"


def list_chapter_files(chapters_dir: Path = CHAPTERS_DIR) -> list[Path]:
    chapter_files: list[tuple[int, Path]] = []
    if not chapters_dir.exists():
        return []
    for path in chapters_dir.iterdir():
        match = re.match(r"^ch_(\d+)\.md$", path.name)
        if match:
            chapter_files.append((int(match.group(1)), path))
    return [path for _, path in sorted(chapter_files)]


def load_epub_language() -> str:
    env_config = _load_env_config()
    return _env_value("AUTOBOOK_EPUB_LANG", env_config) or _env_value("AUTOBOOK_LANGUAGE", env_config) or "en"


def require_pandoc() -> str:
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("Pandoc is required to build EPUB. Install it or run typeset/build_final.py interactively.")
    return pandoc


def build_pandoc_command(output_path: Path = DEFAULT_OUTPUT, chapters_dir: Path = CHAPTERS_DIR) -> list[str]:
    metadata = load_book_metadata()
    chapter_files = list_chapter_files(chapters_dir)
    if not chapter_files:
        raise FileNotFoundError(f"No chapter files found in {chapters_dir}")

    command = [
        require_pandoc(),
        *[str(path) for path in chapter_files],
        "--metadata",
        f"title={metadata['title']}",
        "--metadata",
        f"lang={load_epub_language()}",
        "--css",
        str(EPUB_STYLE),
        "--toc",
        "-o",
        str(output_path),
    ]
    if metadata["author"]:
        command.extend(["--metadata", f"author={metadata['author']}"])
    if metadata["subtitle"]:
        command.extend(["--metadata", f"subtitle={metadata['subtitle']}"])
    if metadata["subject"]:
        command.extend(["--metadata", f"description={metadata['subject']}"])
    if COVER_IMAGE.exists():
        command.append(f"--epub-cover-image={COVER_IMAGE}")
    return command


def build_epub(output_path: Path = DEFAULT_OUTPUT) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    command = build_pandoc_command(output_path=output_path)
    subprocess.run(command, cwd=BASE_DIR, check=True)
    return output_path


def main() -> None:
    output_path = build_epub()
    print(f"Wrote EPUB to {os.path.relpath(output_path, BASE_DIR)}")


if __name__ == "__main__":
    main()
