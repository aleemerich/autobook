import os
import pytest
from pathlib import Path
import prompt_loader
from prompt_loader import load_agent_prompt

def test_load_agent_prompt_success(tmp_path: Path, monkeypatch) -> None:
    """Valida o carregamento básico de prompt no idioma solicitado."""
    # Configura um diretório temporário para os prompts
    tmp_prompts_dir = tmp_path / "prompts"
    pt_dir = tmp_prompts_dir / "PT-BR" / "agents"
    pt_dir.mkdir(parents=True)

    prompt_content = "Você é o DraftingAgent em português."
    (pt_dir / "drafting.txt").write_text(prompt_content, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)

    # Chama o loader com o idioma específico
    loaded = load_agent_prompt(role="drafting", lang="PT-BR")
    assert loaded == prompt_content

def test_load_agent_prompt_fallback_to_en(tmp_path: Path, monkeypatch) -> None:
    """Valida o fallback para EN quando o idioma solicitado não possui o arquivo."""
    tmp_prompts_dir = tmp_path / "prompts"

    # Cria apenas a pasta e o arquivo em EN
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)
    prompt_content_en = "You are the DraftingAgent in English."
    (en_dir / "drafting.txt").write_text(prompt_content_en, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)

    # Pede PT-BR, mas deve dar fallback para EN
    loaded = load_agent_prompt(role="drafting", lang="PT-BR")
    assert loaded == prompt_content_en

def test_load_agent_prompt_respects_fallback_false(tmp_path: Path, monkeypatch) -> None:
    """Valida que fallback_to_en=False impede a busca na pasta EN e lança FileNotFoundError."""
    tmp_prompts_dir = tmp_path / "prompts"

    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)
    (en_dir / "drafting.txt").write_text("English content", encoding="utf-8")

    # Cria pasta PT-BR vazia
    pt_dir = tmp_prompts_dir / "PT-BR" / "agents"
    pt_dir.mkdir(parents=True)

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)

    with pytest.raises(FileNotFoundError) as excinfo:
        load_agent_prompt(role="drafting", lang="PT-BR", fallback_to_en=False)
    assert "not found under active language 'PT-BR'" in str(excinfo.value)

def test_load_agent_prompt_uses_env_when_lang_none(tmp_path: Path, monkeypatch) -> None:
    """Valida que o loader respeita a variável de ambiente AUTOBOOK_LANGUAGE se lang for None."""
    tmp_prompts_dir = tmp_path / "prompts"
    pt_dir = tmp_prompts_dir / "PT-BR" / "agents"
    pt_dir.mkdir(parents=True)

    prompt_content = "Voz do Drafting em PT-BR"
    (pt_dir / "drafting.txt").write_text(prompt_content, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "PT-BR")

    loaded = load_agent_prompt(role="drafting", lang=None)
    assert loaded == prompt_content

def test_load_agent_prompt_raises_file_not_found(tmp_path: Path, monkeypatch) -> None:
    """Valida que é lançado um FileNotFoundError descritivo para prompts inexistentes."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)

    with pytest.raises(FileNotFoundError) as excinfo:
        load_agent_prompt(role="stylist", lang="EN")
    assert "stylist.txt" in str(excinfo.value)

def test_load_agent_prompt_invalid_role() -> None:
    """Valida que ValueError é lançado para papéis vazios."""
    with pytest.raises(ValueError) as excinfo:
        load_agent_prompt(role="")
    assert "não pode ser vazio" in str(excinfo.value)
