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

    def fake_fix_outline_chunk(
        chunk_content,
        report_content,
        writer_model,
        global_plan="",
        previous_context="",
        next_context="",
    ):
        calls.append(
            (
                chunk_content,
                report_content,
                writer_model,
                global_plan,
                previous_context,
                next_context,
            )
        )
        return chunk_content.replace("Texto", "Corrigido")

    monkeypatch.setattr(fix_outline, "fix_outline_chunk", fake_fix_outline_chunk)

    fixed = fix_outline.fix_outline_content(
        outline_content=outline,
        report_content=report,
        writer_model="test-model",
        chunk_size=2,
        global_plan="Plano global",
    )

    assert len(calls) == 2
    assert calls[0][2] == "test-model"
    assert calls[0][3] == "Plano global"
    assert "Corrigido 1." in fixed
    assert "Corrigido 2." in fixed
    assert "Corrigido 3." in fixed


def test_build_compact_outline_map_truncates_each_chapter() -> None:
    chapter_blocks = [
        (1, "### Capítulo 1 - Um\n" + "A" * 20),
        (2, "### Capítulo 2 - Dois\n" + "B" * 20),
    ]

    outline_map = fix_outline.build_compact_outline_map(
        chapter_blocks,
        max_chars_per_chapter=12,
    )

    assert "### 1" in outline_map
    assert "### 2" in outline_map
    assert "[...]" in outline_map
    assert "A" * 20 not in outline_map
    assert "B" * 20 not in outline_map


def test_create_global_plan_from_map_uses_continuity_config(monkeypatch) -> None:
    calls = []

    def fake_call_llm(prompt, system_prompt, temperature, override_model):
        calls.append((prompt, system_prompt, temperature, override_model))
        return "Plano global"

    monkeypatch.setattr(fix_outline, "call_llm", fake_call_llm)

    plan = fix_outline.create_global_plan_from_map(
        compact_outline_map="Mapa",
        report_content="Relatório",
        writer_model="test-model",
    )

    assert plan == "Plano global"
    assert calls[0][0]
    assert "Mapa" in calls[0][0]
    assert "Relatório" in calls[0][0]
    assert calls[0][2] == 0.2
    assert calls[0][3] == "test-model"


def test_fix_outline_content_builds_global_plan_and_passes_neighbor_context(monkeypatch) -> None:
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "PT-BR")
    outline = """# Outline

### Capítulo 1 — Um
Texto 1.

### Capítulo 2 — Dois
Texto 2.

### Capítulo 3 — Três
Texto 3.

### Capítulo 4 — Quatro
Texto 4.
"""
    report = json.dumps({"continuity_score": 5.6, "inconsistencies": []})
    calls = []

    def fake_create_global_outline_plan(**kwargs):
        assert kwargs["writer_model"] == "test-model"
        assert kwargs["chunk_size"] == 2
        return "Plano global"

    def fake_fix_outline_chunk(
        chunk_content,
        report_content,
        writer_model,
        global_plan="",
        previous_context="",
        next_context="",
    ):
        calls.append(
            {
                "chunk_content": chunk_content,
                "writer_model": writer_model,
                "global_plan": global_plan,
                "previous_context": previous_context,
                "next_context": next_context,
            }
        )
        return chunk_content

    monkeypatch.setattr(fix_outline, "create_global_outline_plan", fake_create_global_outline_plan)
    monkeypatch.setattr(fix_outline, "fix_outline_chunk", fake_fix_outline_chunk)

    fixed = fix_outline.fix_outline_content(
        outline_content=outline,
        report_content=report,
        writer_model="test-model",
        chunk_size=2,
        overlap_chapters=1,
    )

    assert "Texto 4." in fixed
    assert len(calls) == 2
    assert calls[0]["global_plan"] == "Plano global"
    assert calls[0]["previous_context"] == ""
    assert "Texto 3." in calls[0]["next_context"]
    assert "Texto 2." in calls[1]["previous_context"]
    assert calls[1]["next_context"] == ""
