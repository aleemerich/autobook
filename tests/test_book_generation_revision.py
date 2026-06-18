from pathlib import Path
from pipelines.book_generation_steps.revision import (
    list_critique_files,
    build_revision_plan,
    build_synthesis_prompt,
    run_sequential_synthesis
)
from writing.feedback import RevisionPlan

class FakeAgent:
    def __init__(self, name):
        self.name = name
        self.calls = []

    def execute(self, prompt: str) -> str:
        self.calls.append(prompt)
        # Retorna o prompt processado/alterado para que possamos validar o fluxo em cascata
        return f"Synthesized: {prompt[:30]}..."

class FakeFactory:
    def __init__(self):
        self.agents = {}
        self.calls = []

    def get_agent(self, role: str, **kwargs) -> FakeAgent:
        self.calls.append((role, kwargs))
        if role not in self.agents:
            self.agents[role] = FakeAgent(role.upper())
        return self.agents[role]

def test_list_critique_files_sorted(tmp_path: Path) -> None:
    """Valida que a lista de arquivos de crítica é retornada ordenada."""
    (tmp_path / "critique_style.md").write_text("style critique", encoding="utf-8")
    (tmp_path / "critique_canon.md").write_text("canon critique", encoding="utf-8")
    (tmp_path / "critique_flow.md").write_text("flow critique", encoding="utf-8")
    
    files = list_critique_files(tmp_path)
    
    assert len(files) == 3
    assert files[0].name == "critique_canon.md"
    assert files[1].name == "critique_flow.md"
    assert files[2].name == "critique_style.md"


def test_list_critique_files_uses_configured_critic_order(tmp_path: Path) -> None:
    """Valida que a ordem declarada em critics_roles prevalece sobre a ordem alfabetica."""
    (tmp_path / "critique_style.md").write_text("style critique", encoding="utf-8")
    (tmp_path / "critique_canon.md").write_text("canon critique", encoding="utf-8")
    (tmp_path / "critique_flow.md").write_text("flow critique", encoding="utf-8")

    files = list_critique_files(
        tmp_path,
        critics_roles=["style_critic", "canon_critic", "flow_critic"]
    )

    assert [f.name for f in files] == [
        "critique_style.md",
        "critique_canon.md",
        "critique_flow.md",
    ]

def test_build_revision_plan_findings(tmp_path: Path) -> None:
    """Valida que o RevisionPlan contém um finding por crítica com mapeamento correto para todos os críticos."""
    f1 = tmp_path / "critique_canon.md"
    f1.write_text("canon error text", encoding="utf-8")
    f2 = tmp_path / "critique_style.md"
    f2.write_text("style issue text", encoding="utf-8")
    f3 = tmp_path / "critique_flow.md"
    f3.write_text("flow issue text", encoding="utf-8")
    f4 = tmp_path / "critique_technical_editor.md"
    f4.write_text("tech issue text", encoding="utf-8")
    
    plan = build_revision_plan([f1, f2, f3, f4])
    
    assert isinstance(plan, RevisionPlan)
    assert len(plan.findings) == 4
    assert plan.findings[0].source == "canon_critic"
    assert plan.findings[0].instruction == "canon error text"
    assert plan.findings[1].source == "style_critic"
    assert plan.findings[1].instruction == "style issue text"
    assert plan.findings[2].source == "flow_critic"
    assert plan.findings[2].instruction == "flow issue text"
    assert plan.findings[3].source == "technical_editor"
    assert plan.findings[3].instruction == "tech issue text"

def test_build_synthesis_prompt() -> None:
    """Valida que o prompt de síntese inclui o texto atual, conteúdo da crítica e o nome do arquivo."""
    critic_name = "critique_style.md"
    chapter_text = "Texto do capítulo inicial..."
    critique_content = "Melhorar a voz do narrador."
    
    prompt = build_synthesis_prompt(critic_name, chapter_text, critique_content)
    
    assert "Você é o SynthesisAgent." in prompt
    assert chapter_text in prompt
    assert critique_content in prompt
    assert f"RELATÓRIO DE CRÍTICA APLICADA ({critic_name}):" in prompt

def test_run_sequential_synthesis_cascade(tmp_path: Path) -> None:
    """Valida que a síntese sequencial chama o agente uma vez por crítica, em cascata, e grava intermediários."""
    (tmp_path / "critique_canon.md").write_text("canon issue", encoding="utf-8")
    (tmp_path / "critique_style.md").write_text("style issue", encoding="utf-8")
    
    factory = FakeFactory()
    original_text = "Original chapter text"
    
    final_text, plan = run_sequential_synthesis(
        tmp_path,
        original_text,
        factory,
        critics_roles=["style_critic", "canon_critic"]
    )
    
    # Synthesis agent deve ser recuperado
    assert len(factory.calls) == 1
    assert factory.calls[0][0] == "synthesis"
    synthesis_agent = factory.agents["synthesis"]
    
    # Chamado exatamente 2 vezes (uma por arquivo)
    assert len(synthesis_agent.calls) == 2
    
    # A primeira chamada recebe o texto original
    assert original_text in synthesis_agent.calls[0]
    # A segunda chamada deve receber o resultado da primeira chamada
    expected_cascade_text = "Synthesized: Você é o SynthesisAgent. Seu o..."
    assert expected_cascade_text in synthesis_agent.calls[1]
    
    # Valida que run_sequential_synthesis retorna o RevisionPlan contendo os findings esperados das críticas
    assert isinstance(plan, RevisionPlan)
    assert len(plan.findings) == 2
    assert plan.findings[0].source == "style_critic"
    assert plan.findings[0].instruction == "style issue"
    assert plan.findings[1].source == "canon_critic"
    assert plan.findings[1].instruction == "canon issue"

    # Deve gravar os arquivos intermediários chapter_step_XX_critique_*.md
    step1_file = tmp_path / "chapter_step_01_critique_style.md"
    step2_file = tmp_path / "chapter_step_02_critique_canon.md"
    
    assert step1_file.exists()
    assert step2_file.exists()
    
    assert step1_file.read_text(encoding="utf-8").startswith("Synthesized:")
    assert step2_file.read_text(encoding="utf-8").startswith("Synthesized:")

def test_run_sequential_synthesis_no_critiques(tmp_path: Path) -> None:
    """Valida que, sem arquivos de crítica, retorna o texto original e plano vazio."""
    factory = FakeFactory()
    original_text = "No critique text"
    
    final_text, plan = run_sequential_synthesis(tmp_path, original_text, factory)
    
    assert final_text == original_text
    assert plan.is_empty is True
    assert len(factory.calls) == 0
