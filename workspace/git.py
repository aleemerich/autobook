import subprocess
from pathlib import Path
from typing import Sequence


class GitCommandError(RuntimeError):
    """Erro padronizado para falhas em comandos Git."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
        cause: BaseException | None = None
    ) -> None:
        self.command = list(command)
        self.cwd = cwd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        details = " ".join(self.command)
        if cwd is not None:
            details = f"{details} (cwd={cwd})"
        if returncode is not None:
            details = f"{details} exited with code {returncode}"
        if stderr:
            details = f"{details}: {stderr.strip()}"
        elif cause is not None:
            details = f"{details}: {cause}"
        super().__init__(details)


def run_git(args: Sequence[str], base_dir: Path | str | None = None, *, check: bool = True) -> subprocess.CompletedProcess:
    """Executa um comando Git com captura padronizada de stdout/stderr."""
    cwd = Path(base_dir) if base_dir is not None else None
    command = ["git", *args]
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            check=False
        )
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        raise GitCommandError(command, cwd=cwd, cause=e) from e

    if check and result.returncode != 0:
        raise GitCommandError(
            command,
            cwd=cwd,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr
        )
    return result


def git_add(path: str | Path, base_dir: Path | str | None = None, *, force: bool = False) -> subprocess.CompletedProcess:
    """Executa git add para um caminho relativo ou absoluto."""
    args = ["add"]
    if force:
        args.append("--force")
    args.append(str(path))
    return run_git(args, base_dir=base_dir)


def git_commit(
    message: str,
    base_dir: Path | str | None = None,
    *,
    allow_no_changes: bool = True
) -> subprocess.CompletedProcess:
    """Executa git commit, permitindo tratar commits sem mudanças como no-op controlado."""
    result = run_git(["commit", "-m", message], base_dir=base_dir, check=False)
    if result.returncode == 0:
        return result

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    no_change_markers = (
        "nothing to commit",
        "no changes added to commit",
        "working tree clean",
    )
    if allow_no_changes and any(marker in combined_output for marker in no_change_markers):
        return result

    raise GitCommandError(
        ["git", "commit", "-m", message],
        cwd=Path(base_dir) if base_dir is not None else None,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr
    )


def git_push(base_dir: Path | str | None = None) -> subprocess.CompletedProcess:
    """Executa git push, tratando branch local sem upstream como no-op."""
    result = run_git(["push"], base_dir=base_dir, check=False)
    if result.returncode == 0:
        return result

    combined_output = f"{result.stdout}\n{result.stderr}".lower()
    no_upstream_markers = (
        "has no upstream branch",
        "no upstream branch",
        "set-upstream",
    )
    if any(marker in combined_output for marker in no_upstream_markers):
        return result

    raise GitCommandError(
        ["git", "push"],
        cwd=Path(base_dir) if base_dir is not None else None,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr
    )


def git_current_branch(base_dir: Path | str | None = None) -> str:
    """Retorna o nome da branch ativa."""
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"], base_dir=base_dir).stdout.strip()


def git_worktree_status(base_dir: Path | str | None = None) -> str:
    """Retorna a saída limpa de git status --porcelain."""
    return run_git(["status", "--porcelain"], base_dir=base_dir).stdout.strip()


def git_switch_new_branch(branch_name: str, base_dir: Path | str | None = None) -> subprocess.CompletedProcess:
    """Cria e muda para uma nova branch."""
    return run_git(["switch", "-c", branch_name], base_dir=base_dir)
