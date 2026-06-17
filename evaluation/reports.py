import json
from datetime import datetime
from pathlib import Path
from typing import Any


def build_chapter_edit_log(chapter_num: int, result: dict[str, Any], timestamp: str) -> dict[str, Any]:
    """Monta o payload de diretivas editoriais extraído da avaliação de capítulo."""
    prose_quality = result.get("prose_quality", {})
    canon_compliance = result.get("canon_compliance", {})
    return {
        "chapter": chapter_num,
        "timestamp": timestamp,
        "overall_score": result.get("overall_score"),
        "top_3_revisions": result.get("top_3_revisions", []),
        "weakest_moment": result.get("weakest_moment") or (
            prose_quality.get("weakest_moment") if isinstance(prose_quality, dict) else None
        ),
        "prose_quality_fix": prose_quality.get("fix") if isinstance(prose_quality, dict) else None,
        "canon_violations": canon_compliance.get("violations", []) if isinstance(canon_compliance, dict) else [],
    }


def save_chapter_evaluation_logs(
    base_dir: Path,
    chapter_num: int,
    result: dict[str, Any],
    timestamp: str | None = None
) -> tuple[Path, Path]:
    """Salva logs programáticos de avaliação e edição para um capítulo."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    eval_log_dir = base_dir / "logs" / "eval_logs"
    eval_log_dir.mkdir(parents=True, exist_ok=True)
    eval_log_path = eval_log_dir / f"{timestamp}_ch{chapter_num:02d}.json"
    eval_log_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    edit_log_dir = base_dir / "logs" / "edit_logs"
    edit_log_dir.mkdir(parents=True, exist_ok=True)
    edit_log_path = edit_log_dir / f"{timestamp}_ch{chapter_num:02d}_edits.json"
    edit_data = build_chapter_edit_log(chapter_num, result, timestamp)
    edit_log_path.write_text(json.dumps(edit_data, indent=2, ensure_ascii=False), encoding="utf-8")

    return eval_log_path, edit_log_path
