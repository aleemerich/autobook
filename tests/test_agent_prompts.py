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

def test_load_agent_prompt_spaces_only_role() -> None:
    """Valida que ValueError é lançado para papéis contendo apenas espaços."""
    with pytest.raises(ValueError) as excinfo:
        load_agent_prompt(role="   ")
    assert "não pode ser vazio" in str(excinfo.value)

def test_drafting_agent_uses_external_prompt(tmp_path: Path, monkeypatch) -> None:
    """Valida que o DraftingAgent usa o prompt externo quando disponível."""
    tmp_prompts_dir = tmp_path / "prompts"
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)

    external_content = "Elite novelist drafting test content."
    (en_dir / "drafting.txt").write_text(external_content, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import DraftingAgent
    agent = DraftingAgent()
    assert agent.system_prompt == external_content

def test_drafting_agent_fallback_to_hardcoded(tmp_path: Path, monkeypatch) -> None:
    """Valida que o DraftingAgent usa o prompt hardcoded quando o arquivo externo está ausente."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import DraftingAgent
    agent = DraftingAgent()
    assert "You are an elite novelist drafting" in agent.system_prompt

def test_stylist_agent_uses_external_prompt(tmp_path: Path, monkeypatch) -> None:
    """Valida que o StylistAgent usa o prompt externo e interpola genre_rules."""
    tmp_prompts_dir = tmp_path / "prompts"
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)

    external_template = "Master stylist template.\nGENRE RULES:\n{genre_rules}"
    (en_dir / "stylist.txt").write_text(external_template, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import StylistAgent
    agent = StylistAgent(genre_rules="Sci-Fi Action")
    assert agent.system_prompt == "Master stylist template.\nGENRE RULES:\nSci-Fi Action"

def test_stylist_agent_fallback_to_hardcoded(tmp_path: Path, monkeypatch) -> None:
    """Valida que o StylistAgent usa o prompt hardcoded e interpola genre_rules se arquivo externo ausente."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import StylistAgent
    agent = StylistAgent(genre_rules="Medieval Fantasy")
    assert "You are a master stylist" in agent.system_prompt
    assert "Medieval Fantasy" in agent.system_prompt

def test_technical_editor_agent_uses_external_prompt(tmp_path: Path, monkeypatch) -> None:
    """Valida que o TechnicalEditorAgent usa o prompt externo e interpola lore_data e slop_rules."""
    tmp_prompts_dir = tmp_path / "prompts"
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)

    external_template = "Editor.\nLORE:\n{lore_data}\nSLOP:\n{slop_rules}"
    (en_dir / "technical_editor.txt").write_text(external_template, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import TechnicalEditorAgent
    agent = TechnicalEditorAgent(lore_data="Lore content", slop_rules="Slop rules")
    assert agent.system_prompt == "Editor.\nLORE:\nLore content\nSLOP:\nSlop rules"

def test_technical_editor_agent_fallback(tmp_path: Path, monkeypatch) -> None:
    """Valida que o TechnicalEditorAgent cai no fallback hardcoded se arquivo externo ausente."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import TechnicalEditorAgent
    agent = TechnicalEditorAgent(lore_data="Lore content", slop_rules="Slop rules")
    assert "You are a meticulous technical editor" in agent.system_prompt
    assert "Lore content" in agent.system_prompt
    assert "Slop rules" in agent.system_prompt

def test_canon_critic_agent_uses_external_prompt(tmp_path: Path, monkeypatch) -> None:
    """Valida que o CanonCriticAgent usa o prompt externo e interpola lore_data."""
    tmp_prompts_dir = tmp_path / "prompts"
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)

    external_template = "Canon critic.\nLORE:\n{lore_data}"
    (en_dir / "canon_critic.txt").write_text(external_template, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import CanonCriticAgent
    agent = CanonCriticAgent(lore_data="Canon lore")
    assert agent.system_prompt == "Canon critic.\nLORE:\nCanon lore"

def test_canon_critic_agent_fallback(tmp_path: Path, monkeypatch) -> None:
    """Valida que o CanonCriticAgent cai no fallback hardcoded se arquivo externo ausente."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import CanonCriticAgent
    agent = CanonCriticAgent(lore_data="Canon lore")
    assert "You are a rigorous canon and lore critic" in agent.system_prompt
    assert "Canon lore" in agent.system_prompt

def test_style_critic_agent_uses_external_prompt(tmp_path: Path, monkeypatch) -> None:
    """Valida que o StyleCriticAgent usa o prompt externo e interpola slop_rules."""
    tmp_prompts_dir = tmp_path / "prompts"
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)

    external_template = "Style critic.\nSLOP:\n{slop_rules}"
    (en_dir / "style_critic.txt").write_text(external_template, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import StyleCriticAgent
    agent = StyleCriticAgent(slop_rules="No slop allowed")
    assert agent.system_prompt == "Style critic.\nSLOP:\nNo slop allowed"

def test_style_critic_agent_fallback(tmp_path: Path, monkeypatch) -> None:
    """Valida que o StyleCriticAgent cai no fallback hardcoded se arquivo externo ausente."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import StyleCriticAgent
    agent = StyleCriticAgent(slop_rules="No slop allowed")
    assert "You are a sharp stylistic editor" in agent.system_prompt
    assert "No slop allowed" in agent.system_prompt

def test_flow_critic_agent_uses_external_prompt(tmp_path: Path, monkeypatch) -> None:
    """Valida que o FlowCriticAgent usa o prompt externo quando disponível."""
    tmp_prompts_dir = tmp_path / "prompts"
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)

    external_content = "Flow structure test content."
    (en_dir / "flow_critic.txt").write_text(external_content, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import FlowCriticAgent
    agent = FlowCriticAgent()
    assert agent.system_prompt == external_content

def test_flow_critic_agent_fallback(tmp_path: Path, monkeypatch) -> None:
    """Valida que o FlowCriticAgent cai no fallback hardcoded se arquivo externo ausente."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import FlowCriticAgent
    agent = FlowCriticAgent()
    assert "You are a story structure and flow critic" in agent.system_prompt

def test_synthesis_agent_uses_external_prompt(tmp_path: Path, monkeypatch) -> None:
    """Valida que o SynthesisAgent usa o prompt externo quando disponível."""
    tmp_prompts_dir = tmp_path / "prompts"
    en_dir = tmp_prompts_dir / "EN" / "agents"
    en_dir.mkdir(parents=True)

    external_content = "Synthesis test prompt content."
    (en_dir / "synthesis.txt").write_text(external_content, encoding="utf-8")

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import SynthesisAgent
    agent = SynthesisAgent()
    assert agent.system_prompt == external_content

def test_synthesis_agent_fallback(tmp_path: Path, monkeypatch) -> None:
    """Valida que o SynthesisAgent cai no fallback hardcoded se arquivo externo ausente."""
    tmp_prompts_dir = tmp_path / "prompts"
    tmp_prompts_dir.mkdir()

    monkeypatch.setattr(prompt_loader, "PROMPTS_DIR", tmp_prompts_dir)
    monkeypatch.setenv("AUTOBOOK_LANGUAGE", "EN")

    from agents import SynthesisAgent
    agent = SynthesisAgent()
    assert "You are an elite manuscript rewriter" in agent.system_prompt
