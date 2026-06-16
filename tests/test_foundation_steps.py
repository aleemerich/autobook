import pytest
from unittest.mock import patch
from pathlib import Path
from pipelines.foundation_steps.context import (
    load_text_file,
    extract_voice_part2,
    build_foundation_writing_state,
    foundation_git_paths
)
from pipelines.foundation_steps.persistence import (
    write_foundation_state,
    commit_foundation_artifacts
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


# --- Testes de persistência de fundação ---

def test_write_foundation_state(tmp_path) -> None:
    """Valida que write_foundation_state cria o arquivo state.json de escrita no local correto."""
    import json
    state_file = tmp_path / "book_data" / "state.json"
    write_foundation_state(state_file)
    assert state_file.exists()
    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state == {
        "chapters_drafted": 0,
        "phase": "writing",
        "current_focus": "chapters"
    }


@patch("subprocess.run")
def test_commit_foundation_artifacts_exclude_mystery(mock_sub_run) -> None:
    """Valida que commit_foundation_artifacts executa git add e commit na ordem certa excluindo o mistério."""
    commit_foundation_artifacts(Path("/test/dir"), include_mystery=False)
    assert mock_sub_run.call_count == 6  # 5 git adds + 1 git commit
    calls = mock_sub_run.call_args_list

    expected_adds = [
        "seed.txt",
        "book_data/world.md",
        "book_data/characters.md",
        "book_data/outline.md",
        "book_data/canon.md",
    ]
    for idx, path in enumerate(expected_adds):
        assert calls[idx][0][0] == ["git", "add", path]
        assert calls[idx][1]["cwd"] == "/test/dir"
        assert calls[idx][1]["check"] is True

    assert calls[5][0][0] == [
        "git", "commit", "-m", "planning: initialize foundational story bibles and outline"
    ]
    assert calls[5][1]["cwd"] == "/test/dir"
    assert calls[5][1]["check"] is True


@patch("subprocess.run")
def test_commit_foundation_artifacts_include_mystery(mock_sub_run) -> None:
    """Valida que commit_foundation_artifacts inclui book_data/MYSTERY.md quando include_mystery é True."""
    commit_foundation_artifacts(Path("/test/dir"), include_mystery=True)
    assert mock_sub_run.call_count == 7  # 6 git adds + 1 git commit
    calls = mock_sub_run.call_args_list
    assert calls[5][0][0] == ["git", "add", "book_data/MYSTERY.md"]
    assert calls[6][0][0] == [
        "git", "commit", "-m", "planning: initialize foundational story bibles and outline"
    ]


@patch("subprocess.run")
def test_commit_foundation_artifacts_error_propagation(mock_sub_run) -> None:
    """Valida que erros de subprocess propagam a partir do helper."""
    import subprocess
    mock_sub_run.side_effect = subprocess.CalledProcessError(1, "git")
    with pytest.raises(subprocess.CalledProcessError):
        commit_foundation_artifacts(Path("/test/dir"), include_mystery=False)
