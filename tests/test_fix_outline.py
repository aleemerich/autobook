import json

import fix_outline


def test_split_outline_chunks_preserves_preamble_and_groups_chapters(monkeypatch) -> None:
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "PT-BR")
    outline = """# Outline

Intro text.

### Capítulo 1 — Um
Texto 1.

### Capítulo 2 — Dois
Texto 2.

### Capítulo 3 — Três
Texto 3.
"""

    preamble, chunks = fix_outline.split_outline_chunks(outline, chunk_size=2)

    assert "Intro text." in preamble
    assert len(chunks) == 2
    assert [num for num, _block in chunks[0]] == [1, 2]
    assert [num for num, _block in chunks[1]] == [3]


def test_filter_report_for_chapters_keeps_related_issues_only() -> None:
    report = {
        "continuity_score": 6.8,
        "inconsistencies": [
            {"chapters": [1, 2], "severity": "medium"},
            {"chapters": [4], "severity": "high"},
        ],
    }

    filtered = json.loads(
        fix_outline.filter_report_for_chapters(json.dumps(report), {2, 3})
    )

    assert filtered["inconsistencies"] == [{"chapters": [1, 2], "severity": "medium"}]


def test_fix_outline_content_calls_llm_by_chunk(monkeypatch) -> None:
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "PT-BR")
    outline = """# Outline

### Capítulo 1 — Um
Texto 1.

### Capítulo 2 — Dois
Texto 2.

### Capítulo 3 — Três
Texto 3.
"""
    report = json.dumps({"continuity_score": 6.8, "inconsistencies": []})
    calls = []

    def fake_fix_outline_chunk(chunk_content, report_content, writer_model):
        calls.append((chunk_content, report_content, writer_model))
        return chunk_content.replace("Texto", "Corrigido")

    monkeypatch.setattr(fix_outline, "fix_outline_chunk", fake_fix_outline_chunk)

    fixed = fix_outline.fix_outline_content(
        outline_content=outline,
        report_content=report,
        writer_model="test-model",
        chunk_size=2,
    )

    assert len(calls) == 2
    assert calls[0][2] == "test-model"
    assert "Corrigido 1." in fixed
    assert "Corrigido 2." in fixed
    assert "Corrigido 3." in fixed
