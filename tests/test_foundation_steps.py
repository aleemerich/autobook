import pytest
from unittest.mock import patch
from pathlib import Path
from pipelines.foundation_steps import (
    load_text_file,
    extract_voice_part2,
    build_foundation_writing_state,
    foundation_git_paths,
    load_seed_and_voice,
    load_world_inputs,
    load_characters_inputs,
    load_outline_inputs,
    load_canon_inputs,
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


def test_load_seed_and_voice(tmp_path) -> None:
    """Valida o carregamento dos insumos de semente e voz."""
    seed_path = tmp_path / "seed.txt"
    voice_path = tmp_path / "voice.md"

    # Caso 1: Arquivos existem
    seed_path.write_text("Minha semente", encoding="utf-8")
    voice_path.write_text("Part 1: Intro\nPart 2: Estilo e voz", encoding="utf-8")
    res = load_seed_and_voice(seed_path, voice_path)
    assert res["seed"] == "Minha semente"
    assert "Part 2: Estilo e voz" in res["voice"]
    assert "Part 2: Estilo e voz" in res["voice_part2"]
    assert "Part 1: Intro" not in res["voice_part2"]

    # Caso 2: Arquivos ausentes
    seed_path.unlink()
    voice_path.unlink()
    res_empty = load_seed_and_voice(seed_path, voice_path)
    assert res_empty["seed"] == ""
    assert res_empty["voice"] == ""
    assert res_empty["voice_part2"] == ""


def test_load_world_inputs(tmp_path) -> None:
    """Valida o carregamento dos insumos do world.md."""
    seed_path = tmp_path / "seed.txt"
    voice_path = tmp_path / "voice.md"
    seed_path.write_text("Semente", encoding="utf-8")
    voice_path.write_text("Voz", encoding="utf-8")

    res = load_world_inputs(seed_path, voice_path)
    assert res["seed"] == "Semente"
    assert res["voice_part2"] == "Voz"


def test_load_characters_inputs(tmp_path) -> None:
    """Valida o carregamento dos insumos do characters.md."""
    seed_path = tmp_path / "seed.txt"
    world_path = tmp_path / "world.md"
    voice_path = tmp_path / "voice.md"

    seed_path.write_text("Semente", encoding="utf-8")
    world_path.write_text("Mundo", encoding="utf-8")
    voice_path.write_text("Part 2\nVoz", encoding="utf-8")

    res = load_characters_inputs(seed_path, world_path, voice_path)
    assert res["seed"] == "Semente"
    assert res["world"] == "Mundo"
    assert res["voice_part2"] == "Part 2\nVoz"


def test_load_outline_inputs(tmp_path) -> None:
    """Valida o carregamento dos insumos do outline.md."""
    seed_path = tmp_path / "seed.txt"
    world_path = tmp_path / "world.md"
    characters_path = tmp_path / "characters.md"
    mystery_path = tmp_path / "mystery.md"
    craft_path = tmp_path / "craft.md"
    voice_path = tmp_path / "voice.md"

    seed_path.write_text("S", encoding="utf-8")
    world_path.write_text("W", encoding="utf-8")
    characters_path.write_text("C", encoding="utf-8")
    mystery_path.write_text("M", encoding="utf-8")
    craft_path.write_text("Cr", encoding="utf-8")
    voice_path.write_text("V", encoding="utf-8")

    res = load_outline_inputs(
        seed_path, world_path, characters_path, mystery_path, craft_path, voice_path
    )
    assert res["seed"] == "S"
    assert res["world"] == "W"
    assert res["characters"] == "C"
    assert res["mystery"] == "M"
    assert res["craft"] == "Cr"
    assert res["voice_part2"] == "V"


def test_load_outline_inputs_missing_craft(tmp_path) -> None:
    """Valida que load_outline_inputs lança FileNotFoundError quando craft.md está ausente."""
    seed_path = tmp_path / "seed.txt"
    world_path = tmp_path / "world.md"
    characters_path = tmp_path / "characters.md"
    mystery_path = tmp_path / "mystery.md"
    craft_path = tmp_path / "craft.md"
    voice_path = tmp_path / "voice.md"

    seed_path.write_text("S", encoding="utf-8")
    world_path.write_text("W", encoding="utf-8")
    characters_path.write_text("C", encoding="utf-8")
    mystery_path.write_text("M", encoding="utf-8")
    # craft_path não é criado
    voice_path.write_text("V", encoding="utf-8")

    with pytest.raises(FileNotFoundError) as exc_info:
        load_outline_inputs(
            seed_path, world_path, characters_path, mystery_path, craft_path, voice_path
        )
    assert "CRAFT.md não encontrado" in str(exc_info.value)



def test_load_canon_inputs(tmp_path) -> None:
    """Valida o carregamento dos insumos do canon.md."""
    seed_path = tmp_path / "seed.txt"
    world_path = tmp_path / "world.md"
    characters_path = tmp_path / "characters.md"

    seed_path.write_text("S", encoding="utf-8")
    world_path.write_text("W", encoding="utf-8")
    characters_path.write_text("C", encoding="utf-8")

    res = load_canon_inputs(seed_path, world_path, characters_path)
    assert res["seed"] == "S"
    assert res["world"] == "W"
    assert res["characters"] == "C"


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


@patch("pipelines.foundation_steps.persistence.git_commit")
@patch("pipelines.foundation_steps.persistence.git_add")
def test_commit_foundation_artifacts_exclude_mystery(mock_git_add, mock_git_commit) -> None:
    """Valida que commit_foundation_artifacts executa git add e commit na ordem certa excluindo o mistério."""
    base_dir = Path("/test/dir")
    commit_foundation_artifacts(base_dir, include_mystery=False)
    assert mock_git_add.call_count == 5

    expected_adds = [
        "seed.txt",
        "book_data/world.md",
        "book_data/characters.md",
        "book_data/outline.md",
        "book_data/canon.md",
    ]
    for idx, path in enumerate(expected_adds):
        assert mock_git_add.call_args_list[idx].args == (path,)
        assert mock_git_add.call_args_list[idx].kwargs == {"base_dir": base_dir, "force": True}

    mock_git_commit.assert_called_once_with(
        "planning: initialize foundational story bibles and outline",
        base_dir=base_dir
    )


@patch("pipelines.foundation_steps.persistence.git_commit")
@patch("pipelines.foundation_steps.persistence.git_add")
def test_commit_foundation_artifacts_include_mystery(mock_git_add, mock_git_commit) -> None:
    """Valida que commit_foundation_artifacts inclui book_data/MYSTERY.md quando include_mystery é True."""
    base_dir = Path("/test/dir")
    commit_foundation_artifacts(base_dir, include_mystery=True)
    assert mock_git_add.call_count == 6
    assert mock_git_add.call_args_list[5].args == ("book_data/MYSTERY.md",)
    mock_git_commit.assert_called_once_with(
        "planning: initialize foundational story bibles and outline",
        base_dir=base_dir
    )

@patch("pipelines.foundation_steps.persistence.git_commit")
@patch("pipelines.foundation_steps.persistence.git_add")
def test_commit_foundation_artifacts_includes_existing_workspace_files(mock_git_add, mock_git_commit, tmp_path) -> None:
    """Valida que arquivos locais ignorados sao adicionados explicitamente quando existem."""
    book_data = tmp_path / "book_data"
    book_data.mkdir()
    for name in ["state.json", "voice.md", "workspace.json"]:
        (book_data / name).write_text("data", encoding="utf-8")

    commit_foundation_artifacts(tmp_path, include_mystery=False)

    mock_git_add.assert_any_call("book_data/state.json", base_dir=tmp_path, force=True)
    mock_git_add.assert_any_call("book_data/voice.md", base_dir=tmp_path, force=True)
    mock_git_add.assert_any_call("book_data/workspace.json", base_dir=tmp_path, force=True)
    mock_git_commit.assert_called_once()


@patch("pipelines.foundation_steps.persistence.git_add")
def test_commit_foundation_artifacts_error_propagation(mock_git_add) -> None:
    """Valida que erros de subprocess propagam a partir do helper."""
    from workspace.git import GitCommandError
    mock_git_add.side_effect = GitCommandError(["git", "add", "seed.txt"])
    with pytest.raises(GitCommandError):
        commit_foundation_artifacts(Path("/test/dir"), include_mystery=False)
