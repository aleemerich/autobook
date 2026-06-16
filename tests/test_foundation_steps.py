from pathlib import Path
from pipelines.foundation_steps.context import (
    load_text_file,
    extract_voice_part2,
    build_foundation_writing_state,
    foundation_git_paths
)

def test_load_text_file_exists(tmp_path) -> None:
    """Valida que load_text_file lê o conteúdo de um arquivo existente."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello World", encoding="utf-8")
    assert load_text_file(test_file) == "Hello World"

def test_load_text_file_absent(tmp_path) -> None:
    """Valida que load_text_file retorna string vazia se o arquivo não existir."""
    test_file = tmp_path / "non_existent.txt"
    assert load_text_file(test_file) == ""

def test_extract_voice_part2_with_part2() -> None:
    """Valida que extract_voice_part2 extrai o conteúdo a partir da Part 2."""
    voice_text = (
        "Part 1: Tone Guidelines\n"
        "Keep it mysterious and detailed.\n"
        "Part 2: Specific Voice Details\n"
        "Always use active verbs and short sentences."
    )
    part2 = extract_voice_part2(voice_text)
    assert "Part 2: Specific Voice Details" in part2
    assert "Always use active verbs" in part2
    assert "Part 1: Tone Guidelines" not in part2

def test_extract_voice_part2_without_part2() -> None:
    """Valida que extract_voice_part2 retorna o texto inteiro se 'Part 2' não for encontrado."""
    voice_text = "Just some tone guidelines here."
    part2 = extract_voice_part2(voice_text)
    assert part2 == voice_text

def test_extract_voice_part2_empty() -> None:
    """Valida que extract_voice_part2 retorna vazio para entrada vazia."""
    assert extract_voice_part2("") == ""
    assert extract_voice_part2(None) == ""

def test_build_foundation_writing_state() -> None:
    """Valida que build_foundation_writing_state retorna os campos e valores corretos."""
    assert build_foundation_writing_state() == {
        "chapters_drafted": 0,
        "phase": "writing",
        "current_focus": "chapters"
    }

def test_foundation_git_paths_exclude_mystery() -> None:
    """Valida os caminhos de git add retornados sem incluir o mistério central."""
    paths = foundation_git_paths(include_mystery=False)
    assert "seed.txt" in paths
    assert "book_data/world.md" in paths
    assert "book_data/characters.md" in paths
    assert "book_data/outline.md" in paths
    assert "book_data/canon.md" in paths
    assert "book_data/MYSTERY.md" not in paths
    assert len(paths) == 5

def test_foundation_git_paths_include_mystery() -> None:
    """Valida os caminhos de git add retornados incluindo o mistério central."""
    paths = foundation_git_paths(include_mystery=True)
    assert "seed.txt" in paths
    assert "book_data/world.md" in paths
    assert "book_data/characters.md" in paths
    assert "book_data/outline.md" in paths
    assert "book_data/canon.md" in paths
    assert "book_data/MYSTERY.md" in paths
    assert len(paths) == 6
