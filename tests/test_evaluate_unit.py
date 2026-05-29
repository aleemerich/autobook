#!/usr/bin/env python3
"""
tests/test_evaluate_unit.py — Unit tests for the evaluate.py mechanical slop checker.
"""

import pytest
from evaluate import slop_score


def test_clean_text():
    """Ensures natural, well-varied human prose has a 0.0 slop penalty."""
    text = (
        "The wind was cold. It carried the smell of wet earth from the valley below, "
        "whipping through the tall pines. Cass pulled his woolen cloak tighter around "
        "his shoulders and stepped forward. The path was narrow. One slip, and he would "
        "tumble into the dark canyon. He had to reach the village before nightfall."
    )
    result = slop_score(text)
    assert result["slop_penalty"] == 0.0
    assert len(result["tier1_hits"]) == 0
    assert result["telling_violations"] == 0


def test_tier1_banned_words():
    """Ensures typical AI words like 'delve' or 'tapestry' trigger appropriate penalties."""
    text = "We need to delve into the tapestry of this multifaceted project and utilize our synergy."
    result = slop_score(text)
    
    # Check that the banned words were caught
    caught_words = [word for word, count in result["tier1_hits"]]
    assert "delve" in caught_words
    assert "tapestry" in caught_words
    assert "multifaceted" in caught_words
    assert "utilize" in caught_words
    assert result["slop_penalty"] > 0.0


def test_fiction_ai_tells():
    """Ensures AI prose clichés like 'let out a breath' or 'couldn't help but feel' are caught."""
    text = (
        "He let out a breath he didn't realize he was holding. "
        "She couldn't help but feel a wave of fear wash over her."
    )
    result = slop_score(text)
    
    assert result["slop_penalty"] > 0.0
    caught_tells = [pattern for pattern, count in result["fiction_ai_tells"]]
    # The patterns are matched as substrings
    assert any("breath" in p or "holding" in p for p in caught_tells)
    assert any("help but feel" in p for p in caught_tells)


def test_em_dash_overuse():
    """Ensures excessive em dashes trigger a penalty."""
    # A short text with excessive em-dashes to inflate density
    text = "This — is — a — very — fragmented — sentence — indeed."
    result = slop_score(text)
    
    assert result["em_dash_density"] > 15
    assert result["slop_penalty"] > 0.0


def test_sentence_uniformity():
    """Ensures uniform sentence lengths (monotone rhythm) trigger a penalty."""
    # Every sentence is exactly 4 words long (perfectly uniform, coefficient of variation = 0)
    text = "This is a book. That is a cat. She is very sad. He is very mad."
    result = slop_score(text)
    
    assert result["sentence_length_cv"] < 0.3
    assert result["slop_penalty"] > 0.0
