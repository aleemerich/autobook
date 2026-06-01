#!/usr/bin/env python3
"""
run_editorial.py — Automated Editorial Revision Pipeline.
Coordinates human-directed chapter revisions, analyzing impacts via a hybrid approach (User + AI),
presenting a non-sycophantic critique, and handling downstream continuity cascades.
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Load project settings and helpers
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from run_pipeline import run_tool, log_msg, banner, step, git_add_commit, git_reset_hard

EDITORIAL_FILE = BASE_DIR / "editorial_brief.json"
CHAPTERS_DIR = BASE_DIR / "chapters"
BRIEFS_DIR = BASE_DIR / "briefs"

def load_editorial_brief() -> dict:
    """Load or initialize the editorial brief file."""
    if not EDITORIAL_FILE.exists():
        default_content = {
            "general_notes": "Aumentar o realismo científico nos diálogos e remover vícios de escrita típicos de IA (como repetições em tríade).",
            "chapters": {
                "11": {
                    "brief": "Padre Tomás Delgado deve ser mais enigmático e fazer perguntas desafiadoras em vez de longos discursos expositivos.",
                    "type": "punctual"
                }
            }
        }
        with open(EDITORIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(default_content, f, indent=2, ensure_ascii=False)
        log_msg(f"Criado arquivo de template editorial em: {EDITORIAL_FILE}")
        log_msg("Edite este arquivo com suas correções antes de rodar o pipeline editorial.")
        sys.exit(0)
        
    try:
        with open(EDITORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log_msg(f"ERROR: Falha ao carregar {EDITORIAL_FILE}: {e}", level="FATAL")
        sys.exit(1)

def classify_brief_with_ai(ch_num: int, brief: str) -> dict:
    """
    Call the LLM Judge model to critically analyze the chapter's editorial instructions.
    Returns a dictionary with 'type', 'affects_downstream', and 'criticism'.
    """
    from llm import call_llm
    
    system_prompt = (
        "You are an elite, highly critical literary editor. Your style is direct, "
        "extremely precise, and devoid of any sycophancy or filler words. You do NOT praise. "
        "Your task is to analyze a chapter's proposed editorial instructions and classify "
        "their structural impact on the novel.\n\n"
        "Classification Rules:\n"
        "1. 'punctual': The changes are strictly confined to the chapter's internal prose, "
        "style, dialogue, or localized pacing. No plot facts or downstream continuity are affected.\n"
        "2. 'continuity_breaking': The changes introduce a new physical item, reveal a secret, "
        "alter character states/fates/knowledges, or change historical timeline events. These "
        "WILL propagate downstream and require subsequent chapters to be updated/rewritten in sequence.\n\n"
        "You MUST return your output in strict JSON format with exactly the following keys:\n"
        "{\n"
        "  \"type\": \"punctual\" or \"continuity_breaking\",\n"
        "  \"affects_downstream\": [list of integer chapter numbers affected, empty if punctual],\n"
        "  \"criticism\": \"Brief, direct, non-flattering, no-nonsense critique of the current draft/instruction.\"\n"
        "}"
    )
    
    user_prompt = (
        f"Chapter: {ch_num}\n"
        f"Proposed Edit Brief:\n{brief}\n\n"
        "Analyze the brief and output only the raw JSON. Do not include markdown wraps or explanation outside the JSON."
    )
    
    try:
        response = call_llm(prompt=user_prompt, system_prompt=system_prompt, temperature=0.2, is_judge=True)
        # Parse the JSON safely (clean up markdown code blocks if any)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("\n", 1)[0]
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
            
        data = json.loads(cleaned)
        return {
            "type": data.get("type", "punctual"),
            "affects_downstream": [int(x) for x in data.get("affects_downstream", [])],
            "criticism": data.get("criticism", "Sem críticas adicionais.")
        }
    except Exception as e:
        return {
            "type": "punctual",
            "affects_downstream": [],
            "criticism": f"Falha ao analisar via IA: {e}."
        }

def parse_score(stdout: str, key: str = "overall_score") -> float:
    """Parse score from evaluator stdout."""
    match = re.search(rf"{key}:\s*([0-9.]+)", stdout)
    return float(match.group(1)) if match else 0.0

def run_editorial():
    # 1. Load the centralized briefs
    editorial = load_editorial_brief()
    general_notes = editorial.get("general_notes", "")
    chapters_data = editorial.get("chapters", {})
    
    if not chapters_data:
        log_msg("Aviso: Nenhuma diretiva de capítulos encontrada no JSON. Encerrando.")
        return
        
    banner("ANALISANDO DIRETIVAS EDITORIAIS")
    
    # 2. Hybrid impact analysis
    parsed_tasks = {}
    for ch_str, ch_info in chapters_data.items():
        ch_num = int(ch_str)
        brief = ch_info.get("brief", "")
        user_type = ch_info.get("type", "punctual")
        user_downstream = ch_info.get("affects_downstream", [])
        
        step(f"Analisando Capítulo {ch_num} com Inteligência Editorial...")
        ai_analysis = classify_brief_with_ai(ch_num, brief)
        
        # Merge Downstream ranges
        merged_downstream = sorted(list(set([int(x) for x in user_downstream] + ai_analysis["affects_downstream"])))
        
        # Determine hybrid type
        if user_type == "continuity_breaking" or ai_analysis["type"] == "continuity_breaking" or len(merged_downstream) > 0:
            final_type = "continuity_breaking"
        else:
            final_type = "punctual"
            
        parsed_tasks[ch_num] = {
            "brief": brief,
            "type": final_type,
            "affects_downstream": merged_downstream,
            "criticism": ai_analysis["criticism"]
        }
        
    # 3. Present the Adjustment Plan (Dry-Run)
    print("\n" + "=" * 60)
    print("PLANO DE AJUSTE EDITORIAL (AGUARDANDO APROVAÇÃO)")
    print("=" * 60)
    if general_notes:
        print(f"Diretrizes Gerais: {general_notes}\n")
        
    for ch_num in sorted(parsed_tasks.keys()):
        task = parsed_tasks[ch_num]
        type_str = "QUEBRA DE CONTINUIDADE (CASCATA)" if task["type"] == "continuity_breaking" else "PONTUAL (AJUSTE LOCAL)"
        print(f"[-] Capítulo {ch_num:02d}: {type_str}")
        print(f"    Briefing Humano: \"{task['brief']}\"")
        print(f"    Crítica Direta da IA: \"{task['criticism']}\"")
        if task["affects_downstream"]:
            print(f"    Capítulos Afetados a Jusante: {task['affects_downstream']}")
        print("-" * 60)
        
    # 4. Interactive prompt
    try:
        choice = input("\nDeseja iniciar as ações de correção acima? [Y/n] ").strip().lower()
        if choice not in ["", "y", "yes", "s", "sim"]:
            log_msg("Operação abortada pelo usuário.")
            return
    except (KeyboardInterrupt, EOFError):
        print("\nOperação abortada.")
        return
        
    # 5. Process revisions
    banner("EXECUTANDO REVISÕES EDITORIAIS")
    
    # Track cascading continuity warnings
    # maps chapter -> list of strings
    continuity_warnings = {}
    
    # Process chapters in order
    sorted_chapters = sorted(parsed_tasks.keys())
    for ch_num in sorted_chapters:
        task = parsed_tasks[ch_num]
        banner(f"PROCESSANDO CAPÍTULO {ch_num:02d} ({task['type'].upper()})", char=".")
        
        # Build local brief content
        brief_lines = [
            f"# Diretivas de Correção Editorial - Capítulo {ch_num}",
            "",
            "## Solicitação Principal do Autor:",
            task["brief"],
            ""
        ]
        
        if general_notes:
            brief_lines += [
                "## Diretrizes Gerais da Obra:",
                general_notes,
                ""
            ]
            
        # Inject dynamic cascading continuity warnings
        if ch_num in continuity_warnings and continuity_warnings[ch_num]:
            brief_lines += [
                "## [IMPORTANTE] Avisos de Continuidade (Alterações a Jusante):",
                "Fatos estabelecidos em capítulos anteriores que você deve integrar e respeitar nesta escrita:"
            ]
            for warning in continuity_warnings[ch_num]:
                brief_lines.append(f"- {warning}")
            brief_lines.append("")
            
        # Write temporary brief file
        BRIEFS_DIR.mkdir(exist_ok=True)
        temp_brief_path = BRIEFS_DIR / f"ch{ch_num:02d}_editorial_temp.md"
        temp_brief_path.write_text("\n".join(brief_lines), encoding="utf-8")
        
        # Evaluate before revision
        pre_eval = run_tool(f"uv run python evaluate.py --chapter={ch_num}", timeout=120)
        pre_score = parse_score(pre_eval.stdout, "overall_score")
        
        # Run revision
        step(f"Reescrevendo Capítulo {ch_num}...")
        run_tool(f"uv run python gen_revision.py {ch_num} {temp_brief_path}", timeout=300)
        
        # Evaluate after revision
        post_eval = run_tool(f"uv run python evaluate.py --chapter={ch_num}", timeout=120)
        post_score = parse_score(post_eval.stdout, "overall_score")
        
        # Keep or discard decision
        log_msg(f"Capítulo {ch_num}: Pontuação {pre_score} -> {post_score}")
        
        if post_score >= pre_score:
            commit_hash = git_add_commit(f"editorial: revise ch{ch_num:02d} ({task['type']}) {pre_score}->{post_score}")
            log_msg(f"Mantendo alteração no Capítulo {ch_num:02d}. Commit: {commit_hash}")
            
            # If continuity breaking, register warnings for downstream chapters
            if task["type"] == "continuity_breaking":
                warning_msg = f"No Capítulo {ch_num}, foi estabelecido o seguinte fato: {task['brief']}"
                for downstream_ch in task["affects_downstream"]:
                    if downstream_ch not in continuity_warnings:
                        continuity_warnings[downstream_ch] = []
                    continuity_warnings[downstream_ch].append(warning_msg)
        else:
            step(f"A revisão reduziu a nota ({post_score} < {pre_score}). Revertendo alterações.")
            git_reset_hard("HEAD")
            
        # Clean up temporary brief file
        if temp_brief_path.exists():
            temp_brief_path.unlink()
            
    # 6. Rebuild manuscript, arc summary and LaTeX
    banner("CONSOLIDANDO MANUSCRITO E ESTRUTURA")
    run_tool("uv run python build_arc_summary.py")
    run_tool("uv run python build_outline.py")
    run_tool("uv run python typeset/build_tex.py")
    
    git_add_commit("editorial: finalize manuscript, outline, and LaTeX typeset consolidation")
    
    banner("PIPELINE EDITORIAL CONCLUÍDO COM SUCESSO")

def main():
    run_editorial()

if __name__ == "__main__":
    main()
