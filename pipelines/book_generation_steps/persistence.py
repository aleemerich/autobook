import sys
import json
import shutil
import subprocess
from pathlib import Path

def clean_chapter_text(text: str) -> str:
    """Limpa títulos/metadados do texto final preservando a regra atual."""
    lines = text.split("\n")
    clean_lines = []
    title_kept = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            if stripped.startswith("# ") and not title_kept:
                clean_lines.append(line)
                title_kept = True
        else:
            clean_lines.append(line)
    return "\n".join(clean_lines).strip()

def save_chapter_draft(chapters_dir: Path, ch: int, text: str) -> Path:
    """Escreve o capítulo final em chapters/ch_XX.md."""
    ch_file = chapters_dir / f"ch_{ch:02d}.md"
    ch_file.parent.mkdir(exist_ok=True)
    ch_file.write_text(text, encoding="utf-8")
    return ch_file

def archive_generation_attempt(
    base_dir: Path,
    tmp_dir: Path,
    ch: int,
    attempt: int,
    final_chapter_text: str,
    eval_res: dict
) -> Path:
    """Arquiva a tentativa em logs/generation_attempts/chXX_attemptYY."""
    attempts_dir = base_dir / "logs" / "generation_attempts" / f"ch{ch:02d}_attempt{attempt:02d}"
    if attempts_dir.exists():
        shutil.rmtree(attempts_dir)
    attempts_dir.mkdir(parents=True, exist_ok=True)
    
    # Copia arquivos do tmp_dir para o diretório da tentativa
    for item in tmp_dir.glob("*"):
        if item.is_file():
            shutil.copy(item, attempts_dir / item.name)
            
    # Salva ch_XX_final_attempt.md
    (attempts_dir / f"ch_{ch:02d}_final_attempt.md").write_text(final_chapter_text, encoding="utf-8")
    
    # Salva evaluation.json
    (attempts_dir / "evaluation.json").write_text(
        json.dumps(eval_res, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return attempts_dir

def update_generation_state(state_file: Path, state: dict, ch: int) -> None:
    """Atualiza state["chapters_drafted"] e escreve book_data/state.json."""
    state["chapters_drafted"] = ch
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

def run_continuity_and_git_push(
    base_dir: Path,
    state_file: Path,
    state: dict,
    ch: int,
    score: float,
    attempt: int,
    is_fallback: bool = False,
    best_score: float = None
) -> bool:
    """Roda validação de continuidade e comandos Git."""
    if not is_fallback:
        print("[DraftChaptersStep] Running global continuity validation...")
        cont_res = subprocess.run(
            [sys.executable, "verify_continuity.py", "--strict", "--threshold", "7.0"],
            capture_output=True,
            text=True,
            cwd=str(base_dir)
        )
        if cont_res.returncode == 0:
            print(f"[DraftChaptersStep] Continuity passed for Chapter {ch}!")
            subprocess.run(["git", "add", f"chapters/ch_{ch:02d}.md"], cwd=str(base_dir))
            update_generation_state(state_file, state, ch)
            subprocess.run(["git", "add", "book_data/state.json"], cwd=str(base_dir))
            
            commit_msg = f"ch{ch:02d}: score {score} (attempt {attempt})"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(base_dir))
            
            print("[DraftChaptersStep] Pushing to remote...")
            subprocess.run(["git", "push"], cwd=str(base_dir))
            return True
        else:
            print(f"[DraftChaptersStep] Continuity failed (exit {cont_res.returncode}). Output: {cont_res.stdout}")
            return False
    else:
        # Fallback forced commit
        subprocess.run(["git", "add", f"chapters/ch_{ch:02d}.md"], cwd=str(base_dir))
        update_generation_state(state_file, state, ch)
        subprocess.run(["git", "add", "book_data/state.json"], cwd=str(base_dir))
        
        commit_msg = f"ch{ch:02d}: forced score {best_score} (fallback)"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(base_dir))
        subprocess.run(["git", "push"], cwd=str(base_dir))
        return True
