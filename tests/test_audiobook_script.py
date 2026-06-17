import json
from pathlib import Path

import pytest

import gen_audiobook_script


def test_load_character_cast_uses_generic_default_when_absent(tmp_path: Path) -> None:
    cast = gen_audiobook_script.load_character_cast(tmp_path)

    assert cast == gen_audiobook_script.DEFAULT_CHARACTERS
    assert "NARRATOR" in cast
    assert "CASS" not in cast


def test_load_character_cast_reads_project_cast(tmp_path: Path) -> None:
    cast_path = tmp_path / "book_data" / "audiobook_cast.json"
    cast_path.parent.mkdir(parents=True)
    cast_path.write_text(
        json.dumps({
            "ana": "Investigadora, fala baixa e objetiva.",
            "MIGUEL": "Professor aposentado, hesita antes de responder.",
        }),
        encoding="utf-8",
    )

    cast = gen_audiobook_script.load_character_cast(tmp_path)

    assert cast["ANA"] == "Investigadora, fala baixa e objetiva."
    assert cast["MIGUEL"] == "Professor aposentado, hesita antes de responder."
    assert "NARRATOR" in cast


def test_load_character_cast_rejects_invalid_shapes(tmp_path: Path) -> None:
    cast_path = tmp_path / "book_data" / "audiobook_cast.json"
    cast_path.parent.mkdir(parents=True)

    cast_path.write_text(json.dumps(["ANA"]), encoding="utf-8")
    with pytest.raises(ValueError, match="JSON object"):
        gen_audiobook_script.load_character_cast(tmp_path)

    cast_path.write_text(json.dumps({"": "sem nome"}), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty strings"):
        gen_audiobook_script.load_character_cast(tmp_path)

    cast_path.write_text(json.dumps({"ANA": ""}), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty string"):
        gen_audiobook_script.load_character_cast(tmp_path)
