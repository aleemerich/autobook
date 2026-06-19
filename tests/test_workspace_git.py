import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from workspace.git import (
    GitCommandError,
    git_add,
    git_commit,
    git_current_branch,
    git_push,
    git_switch_new_branch,
    git_worktree_status,
    run_git
)


@patch("workspace.git.subprocess.run")
def test_run_git_uses_cwd_and_captures_output(mock_run: MagicMock, tmp_path: Path) -> None:
    """Valida o contrato comum de execução de comandos Git."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["git", "status"],
        returncode=0,
        stdout="ok",
        stderr=""
    )

    result = run_git(["status"], base_dir=tmp_path)

    assert result.stdout == "ok"
    mock_run.assert_called_once_with(
        ["git", "status"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False
    )


@patch("workspace.git.subprocess.run")
def test_run_git_raises_typed_error_on_failure(mock_run: MagicMock, tmp_path: Path) -> None:
    """Valida que falhas de Git viram GitCommandError com contexto."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["git", "push"],
        returncode=128,
        stdout="",
        stderr="fatal: no remote"
    )

    with pytest.raises(GitCommandError) as excinfo:
        run_git(["push"], base_dir=tmp_path)

    assert "git push" in str(excinfo.value)
    assert "fatal: no remote" in str(excinfo.value)
    assert excinfo.value.returncode == 128


@patch("workspace.git.subprocess.run")
def test_git_helpers_build_expected_commands(mock_run: MagicMock, tmp_path: Path) -> None:
    """Valida os wrappers públicos do adaptador Git."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["git"],
        returncode=0,
        stdout="autobook/test\n",
        stderr=""
    )

    git_add("file.md", base_dir=tmp_path)
    git_add("ignored.md", base_dir=tmp_path, force=True)
    git_push(base_dir=tmp_path)
    assert git_current_branch(base_dir=tmp_path) == "autobook/test"
    assert git_worktree_status(base_dir=tmp_path) == "autobook/test"
    git_switch_new_branch("autobook/new", base_dir=tmp_path)

    commands = [call.args[0] for call in mock_run.call_args_list]
    assert ["git", "add", "file.md"] in commands
    assert ["git", "add", "--force", "ignored.md"] in commands
    assert ["git", "push"] in commands
    assert ["git", "rev-parse", "--abbrev-ref", "HEAD"] in commands
    assert ["git", "status", "--porcelain"] in commands
    assert ["git", "switch", "-c", "autobook/new"] in commands


@patch("workspace.git.subprocess.run")
def test_git_push_allows_missing_upstream(mock_run: MagicMock, tmp_path: Path) -> None:
    """Valida que branch local sem upstream nao quebra pipelines de obra locais."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["git", "push"],
        returncode=128,
        stdout="",
        stderr=(
            "fatal: The current branch autobook/test has no upstream branch.\n"
            "To push the current branch and set the remote as upstream, use git push --set-upstream origin autobook/test"
        )
    )

    result = git_push(base_dir=tmp_path)

    assert result.returncode == 128


@patch("workspace.git.subprocess.run")
def test_git_commit_allows_no_changes_when_configured(mock_run: MagicMock, tmp_path: Path) -> None:
    """Valida que commit sem mudanças pode ser tratado como no-op controlado."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["git", "commit"],
        returncode=1,
        stdout="On branch main\nnothing to commit, working tree clean",
        stderr=""
    )

    result = git_commit("msg", base_dir=tmp_path)

    assert result.returncode == 1


@patch("workspace.git.subprocess.run")
def test_git_commit_raises_for_real_failure(mock_run: MagicMock, tmp_path: Path) -> None:
    """Valida que falha real no commit continua explícita."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["git", "commit"],
        returncode=128,
        stdout="",
        stderr="fatal: unable to auto-detect email address"
    )

    with pytest.raises(GitCommandError) as excinfo:
        git_commit("msg", base_dir=tmp_path)

    assert "auto-detect email" in str(excinfo.value)
