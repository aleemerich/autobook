import json
from pathlib import Path

from evaluation.reports import build_chapter_edit_log, save_chapter_evaluation_logs


def test_build_chapter_edit_log_extracts_editorial_payload() -> None:
    """Valida a montagem do payload de edição a partir da avaliação."""
    result = {
        "overall_score": 7.5,
        "top_3_revisions": ["cut summary", "sharpen dialogue"],
        "prose_quality": {"weakest_moment": "flat sentence", "fix": "make it concrete"},
        "canon_compliance": {"violations": ["wrong location"]},
    }

    data = build_chapter_edit_log(3, result, "20260101_010101")

    assert data["chapter"] == 3
    assert data["timestamp"] == "20260101_010101"
    assert data["overall_score"] == 7.5
    assert data["top_3_revisions"] == ["cut summary", "sharpen dialogue"]
    assert data["weakest_moment"] == "flat sentence"
    assert data["prose_quality_fix"] == "make it concrete"
    assert data["canon_violations"] == ["wrong location"]


def test_save_chapter_evaluation_logs(tmp_path: Path) -> None:
    """Valida escrita dos logs de avaliação e edição em diretórios separados."""
    result = {
        "overall_score": 8.0,
        "top_3_revisions": ["revise ending"],
        "prose_quality": {"fix": "tighten"},
        "canon_compliance": {"violations": []},
    }

    eval_path, edit_path = save_chapter_evaluation_logs(
        tmp_path,
        chapter_num=4,
        result=result,
        timestamp="20260101_010101"
    )

    assert eval_path == tmp_path / "logs" / "eval_logs" / "20260101_010101_ch04.json"
    assert edit_path == tmp_path / "logs" / "edit_logs" / "20260101_010101_ch04_edits.json"
    assert json.loads(eval_path.read_text(encoding="utf-8")) == result

    edit_data = json.loads(edit_path.read_text(encoding="utf-8"))
    assert edit_data["chapter"] == 4
    assert edit_data["overall_score"] == 8.0
    assert edit_data["top_3_revisions"] == ["revise ending"]
