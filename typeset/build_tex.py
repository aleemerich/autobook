#!/usr/bin/env python3
"""Build LaTeX source from chapter files."""
import json
import re
import os
from dotenv import dotenv_values

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS_DIR = os.path.join(BASE_DIR, "chapters")
BOOK_DATA_DIR = os.path.join(BASE_DIR, "book_data")
OUT_DIR = os.path.join(BASE_DIR, "typeset")
ENV_PATH = os.path.join(BASE_DIR, ".env")

def latex_escape(t):
    t = t.replace('&', '\\&')
    t = t.replace('%', '\\%')
    t = t.replace('$', '\\$')
    t = t.replace('#', '\\#')
    t = t.replace('_', '\\_')
    return t

def md_to_latex(body):
    result = []
    for line in body.split('\n'):
        s = line.strip()
        if s == '---':
            result.append('\n\\scenebreak\n')
        elif s == '':
            result.append('')
        else:
            s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'\\textit{\1}', s)
            s = latex_escape(s)
            s = s.replace('\u2014', '---')
            s = s.replace('\u2013', '--')
            s = s.replace('\u201c', '``')
            s = s.replace('\u201d', "''")
            s = s.replace('\u2018', '`')
            s = s.replace('\u2019', "'")
            s = s.replace('\u2026', '\\ldots{}')
            # Convert straight ASCII quotes to LaTeX open/close
            # " at start of line or after space/punctuation = open (``)
            # " elsewhere = close ('')
            s = re.sub(r'(?<=\s)"(?=\w)', '``', s)    # space then "word
            s = re.sub(r'^"(?=\w)', '``', s)            # line-start "word
            s = re.sub(r'(?<=\w)"(?=[\s.,;:!?\-])', "''", s)  # word" then punct/space
            s = re.sub(r'(?<=\w)"$', "''", s)           # word" at line-end
            s = re.sub(r'(?<=[\.\?\!])"', "''", s)      # punctuation" 
            # Catch any remaining straight quotes (open if after space, close otherwise)
            s = re.sub(r'(?<=\s)"', '``', s)
            s = re.sub(r'"(?=\s)', "''", s)
            s = re.sub(r'^"', '``', s)
            result.append(s)
    return '\n'.join(result)

def make_drop_cap(latex_body):
    """Extract first paragraph and wrap first letter in lettrine."""
    lines = latex_body.split('\n')
    first_para = []
    rest_start = 0
    found = False
    
    for i, line in enumerate(lines):
        if not found and line.strip():
            found = True
        if found:
            if line.strip() == '' or line.strip().startswith('\\scenebreak'):
                rest_start = i
                break
            first_para.append(line)
        else:
            rest_start = i + 1
    
    if not first_para:
        return latex_body
    
    para_text = ' '.join(first_para)
    rest = '\n'.join(lines[rest_start:])
    
    if len(para_text) < 2:
        return latex_body
    
    first_letter = para_text[0]
    after_first = para_text[1:]
    
    # Find the rest of the first word to put in the lettrine second arg
    # e.g. "Cass was awake" -> lettrine{C}{ass} was awake
    space_idx = after_first.find(' ')
    if space_idx >= 0:
        word_rest = after_first[:space_idx]
        para_rest = after_first[space_idx:]
    else:
        word_rest = after_first
        para_rest = ""
    
    drop = f"\\lettrine[lines=2, lhang=0.1, nindent=0.2em]{{{first_letter}}}{{{word_rest}}}{para_rest}"
    return drop + '\n\n' + rest

def _read_optional(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read().strip()

def _load_workspace_title():
    workspace_path = os.path.join(BOOK_DATA_DIR, "workspace.json")
    if not os.path.exists(workspace_path):
        return ""
    try:
        with open(workspace_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return ""
    title = data.get("title", "")
    return title.strip() if isinstance(title, str) else ""

def _load_env_config():
    if not os.path.exists(ENV_PATH):
        return {}
    return dotenv_values(ENV_PATH)

def _env_value(name, env_config):
    value = os.environ.get(name)
    if value is None:
        value = env_config.get(name, "")
    return value.strip() if isinstance(value, str) else ""

def _front_matter_lines(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\\\\\n".join(latex_escape(line) for line in lines)

def load_book_metadata():
    """Load current book metadata for the LaTeX wrapper without pinning a specific book."""
    env_config = _load_env_config()
    title = _env_value("AUTOBOOK_TITLE", env_config) or _load_workspace_title()
    if not title:
        raise ValueError(
            "Book title is required for typesetting. Define AUTOBOOK_TITLE or create "
            "book_data/workspace.json through the Autobook wizard."
        )
    return {
        "title": title,
        "author": _env_value("AUTOBOOK_AUTHOR", env_config)
        or _read_optional(os.path.join(BOOK_DATA_DIR, "author.md")),
        "subtitle": _env_value("AUTOBOOK_SUBTITLE", env_config),
        "subject": _env_value("AUTOBOOK_PDF_SUBJECT", env_config),
        "epigraph": _env_value("AUTOBOOK_EPIGRAPH", env_config)
        or _read_optional(os.path.join(BOOK_DATA_DIR, "epigraph.md")),
        "colophon": _env_value("AUTOBOOK_COLOPHON", env_config)
        or _read_optional(os.path.join(BOOK_DATA_DIR, "colophon.md")),
        "end_matter": _env_value("AUTOBOOK_END_MATTER", env_config)
        or _read_optional(os.path.join(BOOK_DATA_DIR, "end_matter.md")),
        "main_font": _env_value("AUTOBOOK_MAIN_FONT", env_config)
        or _read_optional(os.path.join(BOOK_DATA_DIR, "main_font.md")),
        "fallback_font": _env_value("AUTOBOOK_FALLBACK_FONT", env_config)
        or _read_optional(os.path.join(BOOK_DATA_DIR, "fallback_font.md"))
        or "DejaVu Serif",
    }

def _tex_command(name, value, multiline=False):
    content = _front_matter_lines(value) if multiline else latex_escape(value)
    return f"\\renewcommand{{\\{name}}}{{{content}}}"

def write_book_metadata_tex(metadata, out_dir=OUT_DIR):
    lines = [
        "% Auto-generated by typeset/build_tex.py. Do not edit manually.",
        _tex_command("BookTitle", metadata["title"]),
        _tex_command("BookAuthor", metadata["author"]),
        _tex_command("BookSubtitle", metadata["subtitle"]),
        _tex_command("BookSubject", metadata["subject"]),
        _tex_command("BookEpigraph", metadata["epigraph"], multiline=True),
        _tex_command("BookColophon", metadata["colophon"], multiline=True),
        _tex_command("BookEndMatter", metadata["end_matter"], multiline=True),
        _tex_command("BookMainFont", metadata["main_font"]),
        _tex_command("BookFallbackFont", metadata["fallback_font"]),
        "",
    ]
    with open(os.path.join(out_dir, "book_meta.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main():
    # Discover chapters dynamically
    chapter_numbers = []
    if os.path.exists(CHAPTERS_DIR):
        for filename in os.listdir(CHAPTERS_DIR):
            match = re.match(r"^ch_(\d+)\.md$", filename)
            if match:
                chapter_numbers.append(int(match.group(1)))
    chapter_numbers.sort()

    chapters_tex = []
    for n in chapter_numbers:
        path = os.path.join(CHAPTERS_DIR, f"ch_{n:02d}.md")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        
        lines = text.strip().split('\n')
        title_line = lines[0].lstrip('# ').strip()
        body = '\n'.join(lines[1:]).strip()
        
        if ': ' in title_line:
            label, subtitle = title_line.split(': ', 1)
        else:
            label, subtitle = title_line, ""
        
        chapter_name = subtitle if subtitle else label
        latex_body = md_to_latex(body)
        latex_body = make_drop_cap(latex_body)
        
        # Check for chapter ornament (prefer vector PDF over raster PNG)
        art_base = os.path.dirname(CHAPTERS_DIR)
        pdf_path = os.path.join(art_base, "art", "pdf", f"ornament_ch{n:02d}.pdf")
        png_path = os.path.join(art_base, "art", f"ornament_ch{n:02d}.png")
        ornament_tex = ""
        ornament_file = None
        if os.path.exists(pdf_path):
            ornament_file = pdf_path
        elif os.path.exists(png_path):
            ornament_file = png_path
        if ornament_file:
            ornament_tex = (
                f"\\begin{{center}}\n"
                f"\\includegraphics[width=0.8in]{{{ornament_file}}}\n"
                f"\\end{{center}}\n"
                f"\\vspace{{0.15in}}\n"
            )
        
        chapters_tex.append(f"\\chapter{{{latex_escape(chapter_name)}}}\n\n{ornament_tex}{latex_body}\n")
        print(f"  {n:2d}. {title_line}")

    content = '\n\\clearpage\n\n'.join(chapters_tex)

    with open(os.path.join(OUT_DIR, "chapters_content.tex"), 'w', encoding="utf-8") as f:
        f.write(content)

    metadata = load_book_metadata()
    write_book_metadata_tex(metadata)

    print(f"\nWrote {len(chapters_tex)} chapters to typeset/chapters_content.tex")
    print("Wrote book metadata to typeset/book_meta.tex")

if __name__ == '__main__':
    main()
