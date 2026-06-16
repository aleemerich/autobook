import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pipelines.book_generation_steps.drafting import (
    load_previous_beat_context,
    save_raw_beat,
    concatenate_raw_beats,
    run_beat_drafting,
    run_chapter_fallback_drafting
)

class FakeAgent:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.calls = []

    def execute(self, prompt: str) -> str:
        self.calls.append(prompt)
        if len(self.calls) <= len(self.responses):
            return self.responses[len(self.calls) - 1]
        return f"Response {len(self.calls)}"

def test_load_previous_beat_context_beat_1() -> None:
    """Valida que o contexto do beat anterior usa prev_tail no beat 1."""
    prev_tail = "This is previous tail."
    context = load_previous_beat_context(Path("/dummy"), 1, prev_tail)
    assert context == prev_tail

def test_load_previous_beat_context_beat_greater_than_1(tmp_path: Path) -> None:
    """Valida que o contexto do beat anterior usa últimos 3 parágrafos para beats >1."""
    # Caso 1: beat anterior não existe
    context_missing = load_previous_beat_context(tmp_path, 2, "ignored")
    assert context_missing == ""

    # Caso 2: beat anterior existe
    prev_beat_file = tmp_path / "beat_01_raw.md"
    paragraphs = [
        "Paragraph 1",
        "Paragraph 2",
        "Paragraph 3",
        "Paragraph 4",
        "Paragraph 5"
    ]
    prev_beat_file.write_text("\n\n".join(paragraphs), encoding="utf-8")
    
    context = load_previous_beat_context(tmp_path, 2, "ignored")
    # Deve conter os 3 últimos parágrafos
    assert "Paragraph 3\n\nParagraph 4\n\nParagraph 5" in context
    assert "Paragraph 2" not in context
    assert "Paragraph 1" not in context

def test_save_raw_beat(tmp_path: Path) -> None:
    """Valida que salvar beat bruto cria o arquivo no padrão beat_XX_raw.md."""
    content = "Beat content mock"
    path = save_raw_beat(tmp_path, 3, content)
    
    assert path.name == "beat_03_raw.md"
    assert path.exists()
    assert path.read_text(encoding="utf-8") == content

def test_concatenate_raw_beats(tmp_path: Path) -> None:
    """Valida que a concatenação de beats preserva ordem e separa por duas quebras de linha."""
    (tmp_path / "beat_01_raw.md").write_text("Beat One Content", encoding="utf-8")
    (tmp_path / "beat_02_raw.md").write_text("Beat Two Content", encoding="utf-8")
    (tmp_path / "beat_03_raw.md").write_text("Beat Three Content", encoding="utf-8")
    
    consolidated = concatenate_raw_beats(tmp_path, 3)
    
    # O conteúdo deve estar ordenado e separado por \n\n
    assert consolidated == "Beat One Content\n\nBeat Two Content\n\nBeat Three Content"
    
    # Deve criar o arquivo chapter_raw.md
    chapter_file = tmp_path / "chapter_raw.md"
    assert chapter_file.exists()
    assert chapter_file.read_text(encoding="utf-8") == consolidated

def test_run_beat_drafting(tmp_path: Path) -> None:
    """Valida que run_beat_drafting chama o agente uma vez por beat e gera chapter_raw.md."""
    agent = FakeAgent(["Written beat 1", "Written beat 2"])
    beats = ["Do step 1", "Do step 2"]
    
    consolidated = run_beat_drafting(
        tmp_dir=tmp_path,
        ch=2,
        ch_title="Test Chapter",
        beats=beats,
        prev_tail="chapter 1 tail",
        voice_text="voice instructions",
        world_text="world instructions",
        canon_text="canon instructions",
        characters_text="character registry",
        drafting_agent=agent
    )
    
    # Agente chamado exatamente 2 vezes (um para cada beat)
    assert len(agent.calls) == 2
    assert "Beat 1" in agent.calls[0]
    assert "Beat 2" in agent.calls[1]
    
    # Arquivos beat_XX_raw.md devem ter sido criados
    assert (tmp_path / "beat_01_raw.md").exists()
    assert (tmp_path / "beat_02_raw.md").exists()
    
    # O chapter_raw.md deve conter os beats concatenados
    chapter_file = tmp_path / "chapter_raw.md"
    assert chapter_file.exists()
    assert chapter_file.read_text(encoding="utf-8") == "Written beat 1\n\nWritten beat 2"
    assert consolidated == "Written beat 1\n\nWritten beat 2"

def test_run_chapter_fallback_drafting(tmp_path: Path) -> None:
    """Valida que run_chapter_fallback_drafting chama o agente uma vez e cria chapter_raw.md."""
    agent = FakeAgent(["Full Chapter Content"])
    
    consolidated = run_chapter_fallback_drafting(
        tmp_dir=tmp_path,
        ch=3,
        ch_outline="Chapter 3 outline instructions",
        prev_tail="previous tail instructions",
        characters_text="character instructions",
        drafting_agent=agent
    )
    
    # Agente deve ser chamado uma única vez
    assert len(agent.calls) == 1
    assert "Escreva o Capítulo 3 completo." in agent.calls[0]
    
    # O chapter_raw.md deve ter sido gerado
    chapter_file = tmp_path / "chapter_raw.md"
    assert chapter_file.exists()
    assert chapter_file.read_text(encoding="utf-8") == "Full Chapter Content"
    assert consolidated == "Full Chapter Content"
