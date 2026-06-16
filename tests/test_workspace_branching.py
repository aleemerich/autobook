import pytest
import subprocess
from unittest.mock import patch, MagicMock
from workspace.branching import (
    slugify_work_title,
    book_branch_name,
    is_main_branch,
    current_branch,
    ensure_not_main_for_generation
)

def test_slugify_work_title() -> None:
    """Valida a conversão de títulos complexos em slugs ASCII seguros para Git."""
    assert slugify_work_title("O Mistério da Floresta Azul!") == "o-misterio-da-floresta-azul"
    assert slugify_work_title("Aventuras no Espaço-Tempo 2026") == "aventuras-no-espaco-tempo-2026"
    assert slugify_work_title("Título com Ç e acentuação") == "titulo-com-c-e-acentuacao"
    assert slugify_work_title("---strip-hyphens---") == "strip-hyphens"

def test_book_branch_name() -> None:
    """Valida a geração do nome de branch padronizado autobook/<slug>."""
    assert book_branch_name("Meu Livro") == "autobook/meu-livro"
    assert book_branch_name("autobook/meu-livro") == "autobook/meu-livro"

    # Casos de erro da Fase 5.1 Hardening
    with pytest.raises(ValueError) as excinfo:
        book_branch_name("")
    assert "não pode ser vazio" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        book_branch_name("   ")
    assert "não pode ser vazio" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        book_branch_name("???")
    assert "nome de branch vazio inválido" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        book_branch_name("autobook/")
    assert "nome de branch vazio inválido" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        book_branch_name("autobook/???")
    assert "nome de branch vazio inválido" in str(excinfo.value)

def test_is_main_branch() -> None:
    """Valida que main e master são consideradas branches principais."""
    assert is_main_branch("main") is True
    assert is_main_branch("master") is True
    assert is_main_branch("autobook/meu-livro") is False
    assert is_main_branch("feature/branch") is False

def test_current_branch_mocked() -> None:
    """Valida que current_branch lê a branch ativa chamando git de forma mockada."""
    with patch("subprocess.run") as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = "autobook/livro-misterioso\n"
        mock_run.return_value = mock_result
        
        branch = current_branch()
        assert branch == "autobook/livro-misterioso"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )

def test_current_branch_error() -> None:
    """Valida que erros do subprocess no git propagam como RuntimeError."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        with pytest.raises(RuntimeError) as excinfo:
            current_branch()
        assert "Erro ao ler a branch Git ativa" in str(excinfo.value)

def test_ensure_not_main_for_generation_blocking() -> None:
    """Valida o bloqueio estrito de geração de livros nas branches main/master."""
    with pytest.raises(ValueError) as excinfo:
        ensure_not_main_for_generation("main")
    assert "branch principal do projeto" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        ensure_not_main_for_generation("master")
    assert "branch principal do projeto" in str(excinfo.value)

    with patch("workspace.branching.current_branch", return_value="main"):
        with pytest.raises(ValueError) as excinfo:
            ensure_not_main_for_generation()
        assert "branch principal do projeto" in str(excinfo.value)

def test_ensure_not_main_for_generation_accepting() -> None:
    """Valida a aceitação de branches de obra sem levantar exceções."""
    ensure_not_main_for_generation("autobook/meu-livro")
    
    with patch("workspace.branching.current_branch", return_value="autobook/meu-livro"):
        ensure_not_main_for_generation()
