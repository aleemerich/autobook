#!/usr/bin/env python3
"""
tests/test_typeset.py — Unit tests for the LaTeX typesetting and conversion helper functions inside typeset/build_tex.py.
"""

import sys
import json
from pathlib import Path
import pytest

# Add the project root to python path to import typeset.build_tex
sys.path.insert(0, str(Path(__file__).parent.parent))

from typeset import build_tex
from typeset import build_epub
from typeset import build_final
from typeset.build_tex import latex_escape, md_to_latex, make_drop_cap

BASE_DIR = Path(__file__).parent.parent
TYPESET_ENV_KEYS = [
    "AUTOBOOK_TITLE",
    "AUTOBOOK_AUTHOR",
    "AUTOBOOK_SUBTITLE",
    "AUTOBOOK_PDF_SUBJECT",
    "AUTOBOOK_EPIGRAPH",
    "AUTOBOOK_COLOPHON",
    "AUTOBOOK_END_MATTER",
    "AUTOBOOK_MAIN_FONT",
    "AUTOBOOK_FALLBACK_FONT",
]

def test_latex_escape():
    # Verify special characters are escaped correctly
    assert latex_escape("Research & Development") == "Research \\& Development"
    assert latex_escape("100% Cotton") == "100\\% Cotton"
    assert latex_escape("Price $10") == "Price \\$10"
    assert latex_escape("Task #1") == "Task \\#1"
    assert latex_escape("file_name") == "file\\_name"

def test_md_to_latex_italic_conversion():
    # Verify single asterisks translate to \textit{}
    assert md_to_latex("This is *italic* text.") == "This is \\textit{italic} text."
    
def test_md_to_latex_dashes_and_quotes():
    # Verify smart punctuation conversion
    # em-dashes and en-dashes
    assert md_to_latex("Yes\u2014indeed.") == "Yes---indeed."
    assert md_to_latex("Pages 5\u201310") == "Pages 5--10"
    
    # smart quotes
    assert md_to_latex("\u201cHello\u201d") == "``Hello''"
    assert md_to_latex("\u2018World\u2019") == "`World'"
    
    # scene break
    assert md_to_latex("---") == "\n\\scenebreak\n"

def test_make_drop_cap():
    # Verify lettrine formatting on the first letter of the first paragraph
    body = "Protagonist was looking at the terminal screen.\n\nThey clicked repeat."
    result = make_drop_cap(body)

    # "Protagonist" should be formatted as \lettrine[...]{P}{rotagonist}
    assert "\\lettrine" in result
    assert "{P}" in result
    assert "{rotagonist}" in result
    assert "They clicked repeat." in result


def test_make_drop_cap_handles_one_letter_first_word():
    result = make_drop_cap("O laboratorio estava silencioso.\n\nDepois mudou.")

    assert "\\lettrine" in result
    assert "{O}{} laboratorio estava silencioso." in result
    assert "Depois mudou." in result


def test_novel_template_declares_xelatex_for_fontspec():
    novel_template = BASE_DIR / "typeset" / "novel.tex"
    latexmk_config = BASE_DIR / "typeset" / "latexmkrc"

    template_text = novel_template.read_text(encoding="utf-8")
    latexmk_text = latexmk_config.read_text(encoding="utf-8")

    assert template_text.startswith("% !TEX program = xelatex")
    assert "\\usepackage{fontspec}" in template_text
    assert "\\usepackage{etoolbox}" in template_text
    assert "\\IfFontExistsTF{\\BookMainFont}" in template_text
    assert "\\BookFallbackFont" in template_text
    assert "\\ifdefempty{\\BookColophon}" in template_text
    assert "\\renewcommand*{\\LettrineTextFont}{\\relax}" in template_text
    assert "$pdf_mode = 5;" in latexmk_text
    assert "xelatex" in latexmk_text


def test_novel_template_uses_generated_book_metadata():
    novel_template = BASE_DIR / "typeset" / "novel.tex"
    template_text = novel_template.read_text(encoding="utf-8")

    assert "The Second Son of the House of Bells" not in template_text
    assert "Claude Hermes" not in template_text
    assert "Hermes Agent" not in template_text
    assert "\\input{book_meta.tex}" in template_text
    assert "\\BookTitle" in template_text


def test_book_metadata_uses_workspace_title_and_environment(tmp_path, monkeypatch):
    book_data_dir = tmp_path / "book_data"
    out_dir = tmp_path / "typeset"
    book_data_dir.mkdir()
    out_dir.mkdir()
    (book_data_dir / "workspace.json").write_text(
        json.dumps({"schema_version": 1, "title": "Entropia Zero"}),
        encoding="utf-8",
    )
    (book_data_dir / "epigraph.md").write_text("Uma frase de abertura.", encoding="utf-8")

    monkeypatch.setattr(build_tex, "BOOK_DATA_DIR", str(book_data_dir))
    monkeypatch.setattr(build_tex, "ENV_PATH", str(tmp_path / ".env.missing"))
    for key in TYPESET_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AUTOBOOK_AUTHOR", "Autor Teste")
    monkeypatch.setenv("AUTOBOOK_SUBTITLE", "Romance")

    metadata = build_tex.load_book_metadata()
    assert metadata["title"] == "Entropia Zero"
    assert metadata["author"] == "Autor Teste"
    assert metadata["subtitle"] == "Romance"
    assert metadata["epigraph"] == "Uma frase de abertura."
    assert metadata["fallback_font"] == "DejaVu Serif"

    build_tex.write_book_metadata_tex(metadata, out_dir=str(out_dir))
    meta_tex = (out_dir / "book_meta.tex").read_text(encoding="utf-8")

    assert "\\renewcommand{\\BookTitle}{Entropia Zero}" in meta_tex
    assert "\\renewcommand{\\BookAuthor}{Autor Teste}" in meta_tex
    assert "\\renewcommand{\\BookSubtitle}{Romance}" in meta_tex
    assert "\\renewcommand{\\BookFallbackFont}{DejaVu Serif}" in meta_tex


def test_book_metadata_requires_title(tmp_path, monkeypatch):
    book_data_dir = tmp_path / "book_data"
    book_data_dir.mkdir()

    monkeypatch.setattr(build_tex, "BOOK_DATA_DIR", str(book_data_dir))
    monkeypatch.setattr(build_tex, "ENV_PATH", str(tmp_path / ".env.missing"))
    for key in TYPESET_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValueError, match="Book title is required"):
        build_tex.load_book_metadata()


def test_book_metadata_loads_dotenv_file(tmp_path, monkeypatch):
    book_data_dir = tmp_path / "book_data"
    book_data_dir.mkdir()
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                'AUTOBOOK_TITLE="Titulo Pelo Env"',
                'AUTOBOOK_AUTHOR="Autora Pelo Env"',
                'AUTOBOOK_SUBTITLE="Subtitulo Pelo Env"',
                'AUTOBOOK_COLOPHON="Colofao Pelo Env"',
            ]
        ),
        encoding="utf-8",
    )

    for key in TYPESET_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(build_tex, "BOOK_DATA_DIR", str(book_data_dir))
    monkeypatch.setattr(build_tex, "ENV_PATH", str(env_path))

    metadata = build_tex.load_book_metadata()

    assert metadata["title"] == "Titulo Pelo Env"
    assert metadata["author"] == "Autora Pelo Env"
    assert metadata["subtitle"] == "Subtitulo Pelo Env"
    assert metadata["colophon"] == "Colofao Pelo Env"


def test_process_environment_overrides_dotenv_file(tmp_path, monkeypatch):
    book_data_dir = tmp_path / "book_data"
    book_data_dir.mkdir()
    env_path = tmp_path / ".env"
    env_path.write_text('AUTOBOOK_TITLE="Titulo Pelo Arquivo"\n', encoding="utf-8")

    monkeypatch.setattr(build_tex, "BOOK_DATA_DIR", str(book_data_dir))
    monkeypatch.setattr(build_tex, "ENV_PATH", str(env_path))
    monkeypatch.setenv("AUTOBOOK_TITLE", "Titulo Pelo Processo")

    metadata = build_tex.load_book_metadata()

    assert metadata["title"] == "Titulo Pelo Processo"


def test_epub_command_uses_metadata_and_chapters(tmp_path, monkeypatch):
    book_data_dir = tmp_path / "book_data"
    chapters_dir = tmp_path / "chapters"
    book_data_dir.mkdir()
    chapters_dir.mkdir()
    (chapters_dir / "ch_02.md").write_text("# Segundo\n\nTexto 2", encoding="utf-8")
    (chapters_dir / "ch_01.md").write_text("# Primeiro\n\nTexto 1", encoding="utf-8")
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                'AUTOBOOK_TITLE="Livro EPUB"',
                'AUTOBOOK_AUTHOR="Autora EPUB"',
                'AUTOBOOK_LANGUAGE="PT-BR"',
            ]
        ),
        encoding="utf-8",
    )

    for key in TYPESET_ENV_KEYS + ["AUTOBOOK_LANGUAGE", "AUTOBOOK_EPUB_LANG"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(build_tex, "BOOK_DATA_DIR", str(book_data_dir))
    monkeypatch.setattr(build_tex, "ENV_PATH", str(env_path))
    monkeypatch.setattr(build_epub, "CHAPTERS_DIR", chapters_dir)
    monkeypatch.setattr(build_epub, "COVER_IMAGE", tmp_path / "missing-cover.png")
    monkeypatch.setattr(build_epub.shutil, "which", lambda tool: "/usr/bin/pandoc" if tool == "pandoc" else None)

    command = build_epub.build_pandoc_command(output_path=tmp_path / "novel.epub", chapters_dir=chapters_dir)

    assert command[0] == "/usr/bin/pandoc"
    assert str(chapters_dir / "ch_01.md") in command
    assert str(chapters_dir / "ch_02.md") in command
    assert command.index(str(chapters_dir / "ch_01.md")) < command.index(str(chapters_dir / "ch_02.md"))
    assert "title=Livro EPUB" in command
    assert "author=Autora EPUB" in command
    assert "lang=PT-BR" in command


def test_epub_requires_pandoc(monkeypatch):
    monkeypatch.setattr(build_epub.shutil, "which", lambda tool: None)

    with pytest.raises(RuntimeError, match="Pandoc is required"):
        build_epub.require_pandoc()


def test_final_build_install_prompt_accepts_missing_tools(monkeypatch):
    calls = []

    def fake_which(tool):
        return None if tool in {"pandoc", "xelatex"} else f"/usr/bin/{tool}"

    monkeypatch.setattr(build_final.shutil, "which", fake_which)
    monkeypatch.setattr(build_final.subprocess, "run", lambda command, check: calls.append((command, check)))

    build_final.ensure_tools(["pandoc", "xelatex"], install="ask", input_func=lambda _: "s")

    assert calls == [(["sudo", "apt", "install", "-y", "pandoc", "texlive-xetex"], True)]


def test_final_build_can_refuse_install(monkeypatch):
    monkeypatch.setattr(build_final.shutil, "which", lambda tool: None)

    with pytest.raises(RuntimeError, match="Missing required external tool"):
        build_final.ensure_tools(["pandoc"], install="ask", input_func=lambda _: "n")
