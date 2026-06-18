from pathlib import Path
from pipelines.book_generation_steps.critique import (
    build_critic_filename,
    build_critic_prompt,
    run_critic_agents,
    convert_critique_file_to_report,
    convert_critique_text_to_report
)
from writing.feedback import CriticReport, CriticFinding

class FakeAgent:
    def __init__(self, name, response):
        self.name = name
        self.response = response
        self.calls = []

    def execute(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response

class FakeFactory:
    def __init__(self):
        self.agents = {}
        self.calls = []

    def get_agent(self, role: str, **kwargs) -> FakeAgent:
        self.calls.append((role, kwargs))
        if role not in self.agents:
            self.agents[role] = FakeAgent(role.upper(), f"Feedback for {role}")
        return self.agents[role]

def test_build_critic_filename() -> None:
    """Valida que o filename para os críticos segue o padrão esperado."""
    assert build_critic_filename("canon_critic") == "critique_canon.md"
    assert build_critic_filename("style_critic") == "critique_style.md"
    assert build_critic_filename("flow_critic") == "critique_flow.md"
    assert build_critic_filename("technical_editor") == "critique_technical_editor.md"
    assert build_critic_filename("some_other_agent") == "critique_some_other_agent.md"

def test_resolve_role_from_file() -> None:
    """Valida a resolução reversa do papel do crítico a partir do nome de arquivo."""
    from pipelines.book_generation_steps.critique import resolve_role_from_file

    assert resolve_role_from_file("critique_canon.md") == "canon_critic"
    assert resolve_role_from_file("critique_style.md") == "style_critic"
    assert resolve_role_from_file("critique_flow.md") == "flow_critic"
    assert resolve_role_from_file("critique_technical_editor.md") == "technical_editor"

    # Com lista customizada
    custom_roles = ["canon_critic", "technical_editor"]
    assert resolve_role_from_file("critique_canon.md", critics_roles=custom_roles) == "canon_critic"
    assert resolve_role_from_file("critique_technical_editor.md", critics_roles=custom_roles) == "technical_editor"

def test_build_critic_prompt() -> None:
    """Valida que o prompt de crítica inclui o nome do agente, o rascunho bruto e as instruções."""
    agent_name = "CanonCriticAgent"
    chapter_text = "Era uma vez uma cabana no bosque..."
    
    prompt = build_critic_prompt(agent_name, chapter_text)
    
    assert f"Você é o {agent_name}." in prompt
    assert chapter_text in prompt
    assert "Siga as suas instruções de persona e as regras do sistema." in prompt

def test_run_critic_agents(tmp_path: Path) -> None:
    """Valida a execução de múltiplos críticos, a gravação de arquivos e o retorno da lista de caminhos."""
    factory = FakeFactory()
    roles = ["canon_critic", "style_critic"]
    chapter_text = "Rascunho do capítulo"
    lore_data = "Lore mock"
    slop_rules = "Slop mock"
    
    created_files = run_critic_agents(
        tmp_dir=tmp_path,
        critics_roles=roles,
        chapter_raw_text=chapter_text,
        lore_data=lore_data,
        slop_rules=slop_rules,
        factory=factory
    )
    
    # 2 agentes devem ter sido requisitados à factory
    assert len(factory.calls) == 2
    assert factory.calls[0] == ("canon_critic", {"lore_data": lore_data, "slop_rules": slop_rules})
    assert factory.calls[1] == ("style_critic", {"lore_data": lore_data, "slop_rules": slop_rules})
    
    # 2 arquivos devem ter sido retornados e gravados
    assert len(created_files) == 2
    assert created_files[0] == tmp_path / "critique_canon.md"
    assert created_files[1] == tmp_path / "critique_style.md"
    
    assert (tmp_path / "critique_canon.md").exists()
    assert (tmp_path / "critique_style.md").exists()
    
    assert (tmp_path / "critique_canon.md").read_text(encoding="utf-8") == "Feedback for canon_critic"
    assert (tmp_path / "critique_style.md").read_text(encoding="utf-8") == "Feedback for style_critic"

def test_convert_critique_file_to_report(tmp_path: Path) -> None:
    """Valida a conversão simples de arquivo de crítica para CriticReport."""
    critique_content = "Vários clichês encontrados na prosa."
    file_path = tmp_path / "critique_style.md"
    file_path.write_text(critique_content, encoding="utf-8")
    
    report = convert_critique_file_to_report(file_path, "style_critic")
    
    assert isinstance(report, CriticReport)
    assert report.critic_role == "style_critic"
    assert len(report.findings) == 1
    
    finding = report.findings[0]
    assert isinstance(finding, CriticFinding)
    assert finding.source == "style_critic"
    assert finding.instruction == critique_content
    assert finding.quote == ""
    assert finding.severity == "medium"


def test_convert_json_critique_to_structured_report() -> None:
    """Valida conversao de criticas JSON para achados estruturados reais."""
    content = """
    {
      "critic_role": "style_critic",
      "findings": [
        {
          "quote": "frase generica",
          "instruction": "Substituir por imagem concreta.",
          "severity": "high"
        },
        {
          "quote": "ritmo plano",
          "fix": "Variar tamanho das frases.",
          "severity": "unknown"
        }
      ]
    }
    """

    report = convert_critique_text_to_report(content, "style_critic")

    assert report.critic_role == "style_critic"
    assert len(report.findings) == 2
    assert report.findings[0].quote == "frase generica"
    assert report.findings[0].instruction == "Substituir por imagem concreta."
    assert report.findings[0].severity == "high"
    assert report.findings[1].instruction == "Variar tamanho das frases."
    assert report.findings[1].severity == "medium"


def test_convert_markdown_critique_to_multiple_findings() -> None:
    """Valida que listas markdown viram varios achados separados."""
    content = (
        "- Critical: reescrever \"frase quebrada\" para respeitar o canon.\n"
        "- Minor: cortar redundancia no paragrafo final.\n"
    )

    report = convert_critique_text_to_report(content, "canon_critic")

    assert len(report.findings) == 2
    assert report.findings[0].quote == "frase quebrada"
    assert report.findings[0].severity == "high"
    assert report.findings[1].severity == "low"


def test_convert_no_issues_critique_to_empty_report() -> None:
    """Valida que respostas explicitas sem achados nao geram instrucao artificial."""
    report = convert_critique_text_to_report("No style issues found.", "style_critic")

    assert report.critic_role == "style_critic"
    assert report.findings == []
