import pytest
from pathlib import Path
from unittest.mock import patch
from cli.discovery import discover_project_state, ProjectState

def test_discovery_empty_project(tmp_path: Path) -> None:
    """Valida o mapeamento de um projeto vazio, indicando 'ideation' como próximo passo."""
    with patch("cli.discovery.current_branch", return_value="feature/empty"):
        state = discover_project_state(tmp_path)
        
        assert state.current_branch == "feature/empty"
        assert state.has_seed is False
        assert state.book_data_files == []
        assert state.foundation_complete is False
        assert state.chapter_numbers == []
        assert state.logs_present == []
        assert state.production_artifacts_present == []
        assert state.recommended_next_steps == ["ideation"]

def test_discovery_with_seed(tmp_path: Path) -> None:
    """Valida que um projeto com apenas seed.txt sugere 'foundation' como próximo passo."""
    (tmp_path / "seed.txt").write_text("mystery seed")
    
    with patch("cli.discovery.current_branch", return_value="feature/seed"):
        state = discover_project_state(tmp_path)
        assert state.has_seed is True
        assert state.foundation_complete is False
        assert state.recommended_next_steps == ["foundation"]

def test_discovery_with_foundation_complete(tmp_path: Path) -> None:
    """Valida a detecção de fundação completa baseado nos 4 arquivos md obrigatórios."""
    (tmp_path / "seed.txt").write_text("mystery seed")
    book_data = tmp_path / "book_data"
    book_data.mkdir()
    (book_data / "world.md").write_text("world")
    (book_data / "characters.md").write_text("chars")
    (book_data / "outline.md").write_text("outline")
    (book_data / "canon.md").write_text("canon")
    
    with patch("cli.discovery.current_branch", return_value="feature/foundation"):
        state = discover_project_state(tmp_path)
        assert state.has_seed is True
        assert state.foundation_complete is True
        assert "book_generation" in state.recommended_next_steps

def test_discovery_chapters_sorted(tmp_path: Path) -> None:
    """Valida que capítulos ch_XX.md são catalogados e ordenados numericamente."""
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    (chapters / "ch_03.md").write_text("ch3")
    (chapters / "ch_01.md").write_text("ch1")
    (chapters / "ch_12.md").write_text("ch12")
    
    (tmp_path / "seed.txt").write_text("seed")
    book_data = tmp_path / "book_data"
    book_data.mkdir()
    for f in ["world.md", "characters.md", "outline.md", "canon.md"]:
        (book_data / f).write_text("data")

    with patch("cli.discovery.current_branch", return_value="feature/chapters"):
        state = discover_project_state(tmp_path)
        assert state.chapter_numbers == [1, 3, 12]
        assert "editorial_revision" in state.recommended_next_steps
        assert "verify_continuity" in state.recommended_next_steps

def test_discovery_prompts_and_genres(tmp_path: Path) -> None:
    """Valida a detecção de idiomas e gêneros sob prompts/ e genres/."""
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "PT-BR").mkdir()
    (prompts / "EN").mkdir()
    
    genres = tmp_path / "genres"
    genres.mkdir()
    pt_genres = genres / "PT-BR"
    pt_genres.mkdir()
    (pt_genres / "mystery.txt").write_text("mystery")
    (pt_genres / "fantasy.txt").write_text("fantasy")
    
    state = discover_project_state(tmp_path)
    assert "EN" in state.available_languages
    assert "PT-BR" in state.available_languages
    assert state.available_genres == {"PT-BR": ["fantasy", "mystery"]}
