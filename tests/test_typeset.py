#!/usr/bin/env python3
"""
tests/test_typeset.py — Unit tests for the LaTeX typesetting and conversion helper functions inside typeset/build_tex.py.
"""

import sys
from pathlib import Path
import pytest

# Add the project root to python path to import typeset.build_tex
sys.path.insert(0, str(Path(__file__).parent.parent))

from typeset.build_tex import latex_escape, md_to_latex, make_drop_cap

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
