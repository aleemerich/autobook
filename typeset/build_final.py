#!/usr/bin/env python3
"""Build final distributable book artifacts."""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from typeset import build_epub, build_tex
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    import build_epub
    import build_tex

BASE_DIR = Path(__file__).resolve().parent.parent
TYPESET_DIR = BASE_DIR / "typeset"
PDF_OUTPUT = TYPESET_DIR / "novel.pdf"
EPUB_OUTPUT = TYPESET_DIR / "novel.epub"

TOOL_PACKAGES = {
    "pandoc": "pandoc",
    "xelatex": "texlive-xetex",
}


def required_tools(output_format: str) -> list[str]:
    tools: list[str] = []
    if output_format in {"pdf", "all"}:
        tools.append("xelatex")
    if output_format in {"epub", "all"}:
        tools.append("pandoc")
    return tools


def missing_tools(tools: list[str]) -> list[str]:
    return [tool for tool in tools if shutil.which(tool) is None]


def install_command_for(tools: list[str]) -> list[str]:
    packages = [TOOL_PACKAGES[tool] for tool in tools]
    return ["sudo", "apt", "install", "-y", *packages]


def ensure_tools(tools: list[str], install: str = "ask", input_func=None, stdout=sys.stdout) -> None:
    if input_func is None:
        input_func = input

    missing = missing_tools(tools)
    if not missing:
        return

    command = install_command_for(missing)
    command_text = " ".join(command)
    print(f"Missing external tool(s): {', '.join(missing)}", file=stdout)
    print(f"Suggested install command: {command_text}", file=stdout)

    if install == "never":
        raise RuntimeError(f"Missing required external tool(s): {', '.join(missing)}")

    should_install = install == "yes"
    if install == "ask":
        response = input_func("Install missing tools now? [s/N]: ").strip().lower()
        should_install = response in {"s", "sim", "y", "yes"}

    if not should_install:
        raise RuntimeError(f"Missing required external tool(s): {', '.join(missing)}")

    if shutil.which("sudo") is None or shutil.which("apt") is None:
        raise RuntimeError("Automatic installation requires sudo and apt. Install the missing tools manually.")
    subprocess.run(command, check=True)


def build_pdf() -> Path:
    build_tex.main()
    for _ in range(2):
        subprocess.run(["xelatex", "-interaction=nonstopmode", "novel.tex"], cwd=TYPESET_DIR, check=True)
    return PDF_OUTPUT


def build_final(output_format: str = "all", install: str = "ask", input_func=None, stdout=sys.stdout) -> dict[str, Path]:
    ensure_tools(required_tools(output_format), install=install, input_func=input_func, stdout=stdout)
    outputs: dict[str, Path] = {}
    if output_format in {"pdf", "all"}:
        outputs["pdf"] = build_pdf()
    if output_format in {"epub", "all"}:
        outputs["epub"] = build_epub.build_epub(EPUB_OUTPUT)
    return outputs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build final Autobook artifacts.")
    parser.add_argument("--format", choices=["pdf", "epub", "all"], default="all")
    parser.add_argument("--yes", action="store_true", help="Install missing external dependencies without prompting.")
    parser.add_argument("--no-install", action="store_true", help="Do not install missing external dependencies.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    install = "yes" if args.yes else "never" if args.no_install else "ask"
    outputs = build_final(output_format=args.format, install=install)
    for kind, path in outputs.items():
        print(f"Wrote {kind.upper()} to {os.path.relpath(path, BASE_DIR)}")


if __name__ == "__main__":
    main()
