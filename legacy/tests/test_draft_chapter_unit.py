#!/usr/bin/env python3
"""
tests/test_draft_chapter_unit.py — Unit tests for the draft_chapter.py parser helper functions.
"""

import pytest
from draft_chapter import extract_chapter_outline, extract_next_chapter_outline


@pytest.fixture
def fake_outline():
    return (
        "## Act I: The Awakening\n\n"
        "### Ch 1: The Hearth of Bells\n"
        "1. Cass wakes up early to stoke the bronze furnaces.\n"
        "2. His father warns him about the under-note in the air.\n"
        "3. Beat three of chapter one.\n\n"
        "### Ch 2: The Silent Woods\n"
        "1. Cass ventures into the forbidden woods.\n"
        "2. He encounters an echo of magic.\n"
        "3. Beat three of chapter two.\n\n"
        "## Foreshadowing Ledger\n"
        "- Plant: the lost medallion in Ch 1.\n"
    )


def test_extract_chapter_outline_middle(fake_outline):
    """Ensures chapter outlines are sliced correctly from outline.md."""
    outline_ch1 = extract_chapter_outline(fake_outline, 1)
    
    assert "### Ch 1: The Hearth of Bells" in outline_ch1
    assert "His father warns him" in outline_ch1
    assert "### Ch 2: The Silent Woods" not in outline_ch1


def test_extract_chapter_outline_final(fake_outline):
    """Ensures final chapter outlines are sliced correctly up to the next structural section or EOF."""
    outline_ch2 = extract_chapter_outline(fake_outline, 2)
    
    assert "### Ch 2: The Silent Woods" in outline_ch2
    assert "He encounters an echo" in outline_ch2
    assert "## Foreshadowing Ledger" not in outline_ch2


def test_extract_chapter_outline_missing(fake_outline):
    """Ensures missing chapters return clean fallback indicator."""
    outline_ch3 = extract_chapter_outline(fake_outline, 3)
    assert outline_ch3 == "(not found)"


def test_extract_next_chapter_outline_exists(fake_outline):
    """Ensures next chapter's outline is extracted correctly for continuity."""
    next_outline = extract_next_chapter_outline(fake_outline, 1)
    
    assert "### Ch 2: The Silent Woods" in next_outline
    assert "He encounters an echo" in next_outline


def test_extract_next_chapter_outline_eof(fake_outline):
    """Ensures calling next chapter on final chapter returns 'final chapter' indicator."""
    next_outline = extract_next_chapter_outline(fake_outline, 2)
    assert next_outline == "(final chapter)"
