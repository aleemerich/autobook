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
        "O rascunho anterior falhou nos critérios de qualidade. Siga estritamente os feedbacks abaixo, mas preserve o escopo da revisão:",
        "",
        feedback_str,
        "",
        "## DIRETRIZES DA RE-EXECUÇÃO:",
        "Use como ponto de partida a versão anterior e modifique apenas os trechos necessários para incorporar os feedbacks acima.",
        "Não expanda o capítulo de forma substancial. Mantenha a ordem das cenas, os eventos, personagens, locais, desfecho e extensão aproximada da versão anterior.",
        "Não crie novas cenas, subtramas, personagens, revelações, flashbacks ou explicações de mundo, a menos que as diretivas originais peçam explicitamente.",
        "Se o feedback for de idioma, gramática, continuidade local ou higiene textual, faça correções locais e preserve todo o restante.",
        "",
        "## DIRETIVAS ORIGINAIS:",
        brief,
        "",
        "## DIRETIVAS GERAIS:",
        general_notes
    ]
    return "\n".join(corrective_brief_lines)

def count_words(text: str) -> int:
    """Conta palavras usando o mesmo criterio simples dos logs de geracao."""
    return len(text.split())

def is_revision_size_acceptable(
    original_text: str,
    candidate_text: str,
    min_ratio: float = 0.45,
    max_ratio: float = 1.35,
) -> bool:
    """Valida se uma revisao permanece proporcional ao texto original."""
    original_words = count_words(original_text)
    if original_words < 100:
        return True

    candidate_words = count_words(candidate_text)
    min_words = int(round(original_words * min_ratio))
    max_words = int(round(original_words * max_ratio))
    return min_words <= candidate_words <= max_words

def build_size_guard_eval_data(original_text: str, candidate_text: str) -> dict:
    """Cria feedback sintetico quando uma tentativa viola o orçamento de tamanho."""
    original_words = count_words(original_text)
    candidate_words = count_words(candidate_text)
    message = (
        f"A revisão saiu do orçamento de tamanho: original com {original_words} palavras, "
        f"candidata com {candidate_words} palavras. Refaça preservando a extensão aproximada."
    )
    return {
        "overall_score": 0.0,
        "slop": {"slop_penalty": 99.0},
        "prose_quality": {
            "score": 1,
            "weakest_sentence": "",
            "fix": message,
            "note": "Tentativa rejeitada antes da avaliação LLM por violar o orçamento de tamanho.",
        },
        "three_weakest_sentences": [message],
        "top_3_revisions": [message],
    }

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
    legacy_dir = base_dir / "legacy"
    legacy_outline_inputs = [
        legacy_dir / "build_outline.py",
        legacy_dir / "characters.md",
        legacy_dir / "chapters",
    ]
    if all(path.exists() for path in legacy_outline_inputs):
        subprocess.run(["uv", "run", "python", "legacy/build_outline.py"], cwd=str(base_dir))
    if (base_dir / "verify_continuity.py").exists():
        subprocess.run(["uv", "run", "python", "verify_continuity.py"], cwd=str(base_dir))
