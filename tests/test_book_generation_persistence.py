import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from pipelines.book_generation_steps.persistence import (
    clean_chapter_text,
    save_chapter_draft,
    archive_generation_attempt,
    update_generation_state,
    run_continuity_and_git_push
)
from pipelines.book_generation import BookGenerationPipeline, ResetStep, DraftChaptersStep

def test_clean_chapter_text_headings() -> None:
    """Valida que o cleanup de capítulo mantém o primeiro heading # Título e remove headings seguintes."""
    raw_text = (
        "# O Começo da Aventura\n"
        "Helena olhou pela janela.\n"
        "## Detalhes\n"
        "# Outro Heading Redundante\n"
        "Mais prosa de Helena."
    )
    cleaned = clean_chapter_text(raw_text)
    
    assert "# O Começo da Aventura" in cleaned
    assert "Helena olhou pela janela." in cleaned
    assert "Mais prosa de Helena." in cleaned
    # Deve ter removido headings posteriores que começam com #
    assert "## Detalhes" not in cleaned
    assert "# Outro Heading Redundante" not in cleaned

def test_clean_chapter_text_common_prose() -> None:
    """Valida que o cleanup de capítulo preserva textos e parágrafos normais."""
    raw_text = "Esta é uma linha.\n\nEsta é outra linha."
    cleaned = clean_chapter_text(raw_text)
    assert cleaned == raw_text

def test_save_chapter_draft(tmp_path: Path) -> None:
    """Valida que save_chapter_draft cria o arquivo correto em ch_XX.md."""
    chapters_dir = tmp_path / "chapters"
    text = "Prosa completa do capítulo."
    
    saved_path = save_chapter_draft(chapters_dir, 3, text)
    
    assert saved_path == chapters_dir / "ch_03.md"
    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8") == text

def test_archive_generation_attempt(tmp_path: Path) -> None:
    """Valida o arquivamento de tentativa copiando arquivos temporários, salvando a tentativa final e a avaliação."""
    base_dir = tmp_path / "project"
    tmp_dir = tmp_path / "tmp_draft"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    
    (tmp_dir / "beat_01_raw.md").write_text("Beat One Prosa", encoding="utf-8")
    (tmp_dir / "critique_canon.md").write_text("Canon critique content", encoding="utf-8")
    
    final_text = "Final chapter prose"
    eval_res = {"overall_score": 8.5, "comments": "good"}
    
    attempts_dir = archive_generation_attempt(
        base_dir=base_dir,
        tmp_dir=tmp_dir,
        ch=2,
        attempt=1,
        final_chapter_text=final_text,
        eval_res=eval_res
    )
    
    assert attempts_dir == base_dir / "logs" / "generation_attempts" / "ch02_attempt01"
    assert attempts_dir.exists()
    
    # Copiou os arquivos originais
    assert (attempts_dir / "beat_01_raw.md").exists()
    assert (attempts_dir / "beat_01_raw.md").read_text(encoding="utf-8") == "Beat One Prosa"
    assert (attempts_dir / "critique_canon.md").exists()
    
    # Gravou a tentativa final
    final_file = attempts_dir / "ch_02_final_attempt.md"
    assert final_file.exists()
    assert final_file.read_text(encoding="utf-8") == final_text
    
    # Gravou evaluation.json indentado
    eval_file = attempts_dir / "evaluation.json"
    assert eval_file.exists()
    saved_eval = json.loads(eval_file.read_text(encoding="utf-8"))
    assert saved_eval == eval_res

def test_update_generation_state(tmp_path: Path) -> None:
    """Valida que o estado de geração atualiza chapters_drafted e grava o JSON."""
    state_file = tmp_path / "state.json"
    state = {"chapters_drafted": 2, "other": "value"}
    
    update_generation_state(state_file, state, 3)
    
    assert state["chapters_drafted"] == 3
    assert state_file.exists()
    
    saved_state = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved_state["chapters_drafted"] == 3
    assert saved_state["other"] == "value"

@patch("pipelines.book_generation_steps.persistence.git_push")
@patch("pipelines.book_generation_steps.persistence.git_commit")
@patch("pipelines.book_generation_steps.persistence.git_add")
@patch("pipelines.book_generation_steps.persistence.subprocess.run")
def test_run_continuity_and_git_push_success(
    mock_run: MagicMock,
    mock_git_add: MagicMock,
    mock_git_commit: MagicMock,
    mock_git_push: MagicMock,
    tmp_path: Path
) -> None:
    """Valida que continuidade com returncode 0 executa add, commit e push com mocks."""
    # Mock do verify_continuity subprocess
    mock_run.return_value = MagicMock(returncode=0, stdout="success output")
    
    state_file = tmp_path / "state.json"
    state = {"chapters_drafted": 0}
    state_file.write_text(json.dumps(state), encoding="utf-8")
    
    res = run_continuity_and_git_push(
        base_dir=tmp_path,
        state_file=state_file,
        state=state,
        ch=1,
        score=8.5,
        attempt=2,
        is_fallback=False
    )
    
    assert res is True
    assert mock_run.call_count == 1
    
    # Primeiro comando de todos deve ser verify_continuity
    first_cmd = mock_run.call_args_list[0][0][0]
    assert "verify_continuity.py" in first_cmd[1]
    assert "--threshold" in first_cmd
    assert "7.0" in first_cmd
    
    mock_git_add.assert_any_call("chapters/ch_01.md", base_dir=tmp_path, force=True)
    mock_git_add.assert_any_call("book_data/state.json", base_dir=tmp_path, force=True)
    mock_git_commit.assert_called_once_with("ch01: score 8.5 (attempt 2)", base_dir=tmp_path)
    mock_git_push.assert_called_once_with(base_dir=tmp_path)


@patch("pipelines.book_generation_steps.persistence.git_push")
@patch("pipelines.book_generation_steps.persistence.git_commit")
@patch("pipelines.book_generation_steps.persistence.git_add")
@patch("pipelines.book_generation_steps.persistence.subprocess.run")
def test_run_continuity_and_git_push_uses_configurable_threshold(
    mock_run: MagicMock,
    mock_git_add: MagicMock,
    mock_git_commit: MagicMock,
    mock_git_push: MagicMock,
    tmp_path: Path,
    monkeypatch,
) -> None:
    mock_run.return_value = MagicMock(returncode=0, stdout="success output")
    monkeypatch.setenv("CONTINUITY_THRESHOLD", "6.5")

    state_file = tmp_path / "state.json"
    state = {"chapters_drafted": 0}
    state_file.write_text(json.dumps(state), encoding="utf-8")

    assert run_continuity_and_git_push(
        base_dir=tmp_path,
        state_file=state_file,
        state=state,
        ch=1,
        score=7.0,
        attempt=1,
        is_fallback=False,
    )

    cmd = mock_run.call_args[0][0]
    threshold_index = cmd.index("--threshold")
    assert cmd[threshold_index + 1] == "6.5"

@patch("pipelines.book_generation_steps.persistence.subprocess.run")
def test_run_continuity_and_git_push_fail(mock_run: MagicMock, tmp_path: Path) -> None:
    """Valida que continuidade com returncode != 0 não executa commit e push e retorna False."""
    mock_run.return_value = MagicMock(returncode=1, stdout="failed continuity")
    
    state_file = tmp_path / "state.json"
    state = {"chapters_drafted": 0}
    
    res = run_continuity_and_git_push(
        base_dir=tmp_path,
        state_file=state_file,
        state=state,
        ch=1,
        score=5.0,
        attempt=1,
        is_fallback=False
    )
    
    assert res is False
    # Só roda o continuity
    assert mock_run.call_count == 1
    assert "verify_continuity.py" in mock_run.call_args[0][0]

@patch("pipelines.book_generation_steps.persistence.git_push")
@patch("pipelines.book_generation_steps.persistence.git_commit")
@patch("pipelines.book_generation_steps.persistence.git_add")
@patch("pipelines.book_generation_steps.persistence.subprocess.run")
def test_run_continuity_and_git_push_fallback(
    mock_run: MagicMock,
    mock_git_add: MagicMock,
    mock_git_commit: MagicMock,
    mock_git_push: MagicMock,
    tmp_path: Path
) -> None:
    """Valida que a execução em modo fallback executa commit/push forçados sem rodar o continuity."""
    state_file = tmp_path / "state.json"
    state = {"chapters_drafted": 0}
    state_file.write_text(json.dumps(state), encoding="utf-8")
    
    res = run_continuity_and_git_push(
        base_dir=tmp_path,
        state_file=state_file,
        state=state,
        ch=1,
        score=0.0,
        attempt=0,
        is_fallback=True,
        best_score=6.2
    )
    
    assert res is True
    # Não deve ter chamado verify_continuity, mas sim os comandos git diretamente
    mock_run.assert_not_called()
    
    # Chamou add, commit, push
    mock_git_add.assert_any_call("chapters/ch_01.md", base_dir=tmp_path, force=True)
    mock_git_add.assert_any_call("book_data/state.json", base_dir=tmp_path, force=True)
    mock_git_commit.assert_called_once_with("ch01: forced score 6.2 (fallback)", base_dir=tmp_path)
    mock_git_push.assert_called_once_with(base_dir=tmp_path)

def test_book_generation_pipeline_structure() -> None:
    """Valida que o BookGenerationPipeline ainda contém ResetStep e DraftChaptersStep."""
    pipeline = BookGenerationPipeline()
    steps = pipeline.steps
    assert len(steps) == 2
    assert isinstance(steps[0], ResetStep)
    assert isinstance(steps[1], DraftChaptersStep)

def test_save_revision_plan(tmp_path: Path) -> None:
    """Valida que save_revision_plan persiste o plano com findings e metadados no arquivo correto."""
    from pipelines.book_generation_steps.persistence import save_revision_plan
    from writing.feedback import RevisionPlan, CriticFinding

    tmp_dir = tmp_path / "tmp_draft"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    finding = CriticFinding(
        source="canon_critic",
        instruction="Fix lore error",
        quote="Helena",
        severity="high"
    )
    plan = RevisionPlan(findings=[finding], metadata={"key": "value"})

    plan_file = save_revision_plan(tmp_dir, plan)

    assert plan_file == tmp_dir / "revision_plan.json"
    assert plan_file.exists()

    saved_data = json.loads(plan_file.read_text(encoding="utf-8"))
    assert len(saved_data["findings"]) == 1
    assert saved_data["findings"][0]["source"] == "canon_critic"
    assert saved_data["findings"][0]["instruction"] == "Fix lore error"
    assert saved_data["findings"][0]["quote"] == "Helena"
    assert saved_data["findings"][0]["severity"] == "high"
    assert saved_data["metadata"] == {"key": "value"}

def test_save_attempt_evaluation(tmp_path: Path) -> None:
    """Valida que save_attempt_evaluation cria e popula evaluation.json."""
    from pipelines.book_generation_steps.persistence import save_attempt_evaluation
    attempts_dir = tmp_path / "attempt_dir"
    attempts_dir.mkdir(parents=True, exist_ok=True)

    eval_res = {"score": 9.9, "details": "excellent"}
    save_attempt_evaluation(attempts_dir, eval_res)

    eval_file = attempts_dir / "evaluation.json"
    assert eval_file.exists()

    saved_data = json.loads(eval_file.read_text(encoding="utf-8"))
    assert saved_data == eval_res
