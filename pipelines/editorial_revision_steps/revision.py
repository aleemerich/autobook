import sys
import subprocess
from pathlib import Path
from workspace.git import git_add, git_commit, git_push

def build_initial_brief(brief: str, general_notes: str) -> str:
    """Monta o brief editorial inicial combinando o brief do capitulo e as diretrizes gerais."""
    return f"# DIRETIVAS EDITORIAIS\n\n{brief}\n\n## DIRETIVAS GERAIS\n{general_notes}"

def build_corrective_brief(ch_num: int, retry_idx: int, feedback_str: str, brief: str, general_notes: str) -> str:
    """Monta o brief corretivo para retentativa com base nos feedbacks de avaliacao."""
    corrective_brief_lines = [
        f"# DIRETIVAS DE RECORREÇÃO - CAPÍTULO {ch_num} (TENTATIVA {retry_idx + 1})",
        "",
        "O rascunho anterior falhou nos critérios de qualidade. Siga estritamente os feedbacks abaixo:",
        "",
        feedback_str,
        "",
        "## DIRETRIZES DA RE-EXECUÇÃO:",
        "Use como ponto de partida a versão anterior e modifique-a para incorporar todos os feedbacks acima, preservando a lógica correta.",
        "",
        "## DIRETIVAS ORIGINAIS:",
        brief,
        "",
        "## DIRETIVAS GERAIS:",
        general_notes
    ]
    return "\n".join(corrective_brief_lines)

def write_temp_brief(brief_path: Path, content: str) -> None:
    """Escreve o conteudo do brief em um arquivo temporario."""
    brief_path.write_text(content, encoding="utf-8")

def remove_temp_brief(brief_path: Path) -> None:
    """Remove o arquivo temporario do brief se ele existir."""
    if brief_path.exists():
        brief_path.unlink()

def execute_gen_revision(ch_num: int, brief_path: Path, temperature: float, base_dir: Path) -> None:
    """Executa a revisao chamando gen_revision.py via subprocess."""
    subprocess.run(
        [sys.executable, "gen_revision.py", str(ch_num), str(brief_path), "--temperature", str(temperature)],
        cwd=str(base_dir),
        check=True
    )

def is_quality_target_reached(post_score: float, pre_score: float, slop_penalty: float) -> bool:
    """Decide se uma tentativa atingiu os criterios minimos de qualidade."""
    return post_score >= pre_score and post_score >= 7.0 and slop_penalty == 0.0

def is_better_than_fallback(post_score: float, best_score: float, slop_penalty: float, best_slop: float) -> bool:
    """Decide se a tentativa atual tem qualidade superior ao melhor fallback ate entao."""
    if post_score > best_score:
        return True
    elif post_score == best_score:
        if slop_penalty < best_slop:
            return True
    return False

def commit_revised_chapter(ch_num: int, pre_score: float, final_score: float, base_dir: Path) -> None:
    """Executa os comandos git para commitar e dar push no capitulo revisado."""
    print(f"[ExecuteEditorialStep] Committing changes for Chapter {ch_num} (Score: {final_score})...")
    git_add(f"chapters/ch_{ch_num:02d}.md", base_dir=base_dir, force=True)
    commit_msg = f"editorial: revised ch{ch_num:02d} ({pre_score} -> {final_score})"
    git_commit(commit_msg, base_dir=base_dir)
    git_push(base_dir=base_dir)

def run_final_maintenance(base_dir: Path) -> None:
    """Consolida manuscrito e outlines executando os scripts auxiliares caso existam."""
    print("[ExecuteEditorialStep] Consolidating manuscript and outlines...")
    if (base_dir / "legacy" / "build_outline.py").exists():
        subprocess.run(["uv", "run", "python", "legacy/build_outline.py"], cwd=str(base_dir))
    if (base_dir / "verify_continuity.py").exists():
        subprocess.run(["uv", "run", "python", "verify_continuity.py"], cwd=str(base_dir))
