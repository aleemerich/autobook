import pytest
from pathlib import Path
from pipelines.book_generation_steps.context import (
    load_state,
    load_outline,
    count_total_chapters,
    extract_chapter_outline,
    extract_chapter_title,
    extract_next_chapter_outline,
    extract_chapter_beats,
    load_previous_chapter_tail,
    load_lore_files,
    build_lore_data
)

def test_load_state_missing(tmp_path: Path) -> None:
    """Valida que estado ausente retorna um dicionário com chapters_drafted = 0."""
    state = load_state(tmp_path)
    assert state == {"chapters_drafted": 0}

def test_load_state_invalid_json(tmp_path: Path) -> None:
    """Valida que JSON inválido não quebra o carregador de estado e retorna inicializado."""
    state_file = tmp_path / "state.json"
    state_file.write_text("invalid json", encoding="utf-8")
    state = load_state(tmp_path)
    assert state == {"chapters_drafted": 0}

def test_load_state_not_dict(tmp_path: Path) -> None:
    """Valida que JSON que não é um dict no estado retorna inicializado."""
    state_file = tmp_path / "state.json"
    state_file.write_text("[]", encoding="utf-8")
    state = load_state(tmp_path)
    assert state == {"chapters_drafted": 0}

def test_load_outline_missing(tmp_path: Path) -> None:
    """Valida que outline.md ausente levanta FileNotFoundError."""
    with pytest.raises(FileNotFoundError) as excinfo:
        load_outline(tmp_path)
    assert "Outline file outline.md not found" in str(excinfo.value)

def test_count_total_chapters() -> None:
    """Valida a contagem de capítulos usando regex e fallback de 22."""
    outline_text = (
        "## Act I\n"
        "### Chapter 1: The Beginning\n"
        "### Chapter 2: The Middle\n"
        "### Ch 3: The End\n"
    )
    assert count_total_chapters(outline_text) == 3

    # Fallback caso não encontre nenhum match
    assert count_total_chapters("No chapters here") == 22

def test_extract_chapter_outline_and_next() -> None:
    """Valida a extração de outline do capítulo atual e do próximo."""
    outline_text = (
        "## Act I\n"
        "### Chapter 1: The Beginning\n"
        "Beats: 1. start\n"
        "### Chapter 2: The Middle\n"
        "Beats: 2. middle\n"
        "## Act II\n"
        "### Chapter 3: The End\n"
    )
    ch1_out = extract_chapter_outline(outline_text, 1)
    assert "Chapter 1: The Beginning" in ch1_out
    assert "Chapter 2: The Middle" not in ch1_out

    ch2_out = extract_chapter_outline(outline_text, 2)
    assert "Chapter 2: The Middle" in ch2_out
    assert "Chapter 3: The End" not in ch2_out

    # Próximo capítulo
    next_out = extract_next_chapter_outline(outline_text, 1)
    assert "Chapter 2: The Middle" in next_out

    # Fim do romance
    next_out_end = extract_next_chapter_outline(outline_text, 3)
    assert next_out_end == "(Fim do romance)"

def test_extract_chapter_title() -> None:
    """Valida a extração do título do capítulo."""
    ch_outline = "### Chapter 1: The Beginning\nBeats: start"
    assert extract_chapter_title(ch_outline, 1) == "The Beginning"

    # Fallback se não bater a regex
    assert extract_chapter_title("invalid title format", 5) == "Capítulo 5"

def test_extract_chapter_beats() -> None:
    """Valida a extração de beats limpando numeração e hífens."""
    ch_outline = (
        "### Chapter 1\n"
        "**Beats:**\n"
        "1. First beat detail\n"
        "- Second beat detail\n"
        "   3. Third beat detail\n"
    )
    beats = extract_chapter_beats(ch_outline)
    assert beats == [
        "First beat detail",
        "Second beat detail",
        "Third beat detail"
    ]

def test_load_previous_chapter_tail(tmp_path: Path) -> None:
    """Valida o carregamento da cauda do capítulo anterior limitado a 1000 palavras e o fallback para o primeiro."""
    # Capítulo 1 (não há anterior)
    tail1 = load_previous_chapter_tail(tmp_path, 1)
    assert "não há contexto anterior" in tail1

    # Capítulo 2 (com anterior longo)
    prev_chapter_file = tmp_path / "ch_01.md"
    long_text = "word " * 1200
    prev_chapter_file.write_text(long_text, encoding="utf-8")

    tail2 = load_previous_chapter_tail(tmp_path, 2)
    word_count = len(tail2.split())
    assert word_count == 1000

def test_load_lore_files_and_build(tmp_path: Path) -> None:
    """Valida o carregamento e montagem de lore_data."""
    (tmp_path / "world.md").write_text("world context", encoding="utf-8")
    (tmp_path / "canon.md").write_text("canon context", encoding="utf-8")
    (tmp_path / "characters.md").write_text("chars context", encoding="utf-8")
    (tmp_path / "voice.md").write_text("voice context", encoding="utf-8")

    lore = load_lore_files(tmp_path)
    assert lore["world"] == "world context"
    assert lore["canon"] == "canon context"
    assert lore["characters"] == "chars context"
    assert lore["voice"] == "voice context"

    lore_data = build_lore_data(lore["world"], lore["canon"], lore["characters"])
    assert "=== WORLD BIBLE ===" in lore_data
    assert "=== ESTABLISHED CANON ===" in lore_data
    assert "=== CHARACTER REGISTRY ===" in lore_data
    assert "world context" in lore_data
    assert "canon context" in lore_data
    assert "chars context" in lore_data
