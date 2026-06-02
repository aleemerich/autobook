#!/usr/bin/env python3
"""
run_editorial.py — Automated Editorial Revision Pipeline.
Coordinates human-directed chapter revisions, analyzing impacts via a hybrid approach (User + AI),
presenting a non-sycophantic critique, and handling downstream continuity cascades.
Loads and parses editorial.md.
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

EDITORIAL_MD = BASE_DIR / "editorial.md"
CHAPTERS_DIR = BASE_DIR / "chapters"
BRIEFS_DIR = BASE_DIR / "briefs"

def load_editorial_markdown_fallback(text: str) -> dict:
    """
    Fallback parser using regex in case the LLM API is unavailable.
    """
    sections = re.split(r"^#\s+", text, flags=re.MULTILINE)
    general_notes = ""
    chapters = {}
    
    for section in sections:
        if not section.strip():
            continue
            
        lines = section.split("\n")
        title = lines[0].strip().lower()
        content = "\n".join(lines[1:]).strip()
        
        if any(keyword in title for keyword in ["geral", "diretriz", "nota", "general", "guideline", "notes"]):
            general_notes = content
        else:
            # Match chapter number
            match = re.search(r"(?:capítulo|cap|chapter)\s*(\d+)", title)
            if match:
                ch_num = int(match.group(1))
                
                # Check for affects_downstream inside content
                downstream = []
                ds_match = re.search(r"(?:affects_downstream|afeta|jusante|affects)\s*:\s*([0-9\s,]+)", content, re.IGNORECASE)
                if ds_match:
                    downstream = [int(x.strip()) for x in ds_match.group(1).split(",") if x.strip().isdigit()]
                    # Remove the affects_downstream line from the brief so it doesn't pollute the prompt
                    content = re.sub(r"(?:affects_downstream|afeta|jusante|affects)\s*:\s*[0-9\s,]+", "", content, flags=re.IGNORECASE).strip()
                
                chapters[ch_num] = {
                    "brief": content,
                    "type": "continuity_breaking" if downstream else "punctual",
                    "affects_downstream": downstream
                }
                
    return {
        "general_notes": general_notes,
        "chapters": chapters
    }

def load_editorial_markdown() -> dict:
    """
    Parse the centralized editorial.md file using an LLM semantic extractor.
    Falls back to a robust regex parser if the LLM call fails or returns invalid JSON.
    """
    if not EDITORIAL_MD.exists():
        default_content = (
            "# Diretrizes Gerais\n"
            "- Aumentar o realismo científico nos diálogos.\n"
            "- Remover vícios de escrita típicos de IA (como repetições em tríade).\n\n"
            "# Capítulo 11\n"
            "- Padre Tomás Delgado deve ser mais enigmático e fazer perguntas desafiadoras em vez de longos discursos expositivos.\n\n"
            "# Capítulo 17\n"
            "- Helena dá a Elisa uma chave física de bronze que pertencia a Béla.\n"
            "- affects_downstream: 18, 19, 20\n"
        )
        EDITORIAL_MD.write_text(default_content, encoding="utf-8")
        log_msg(f"Created default editorial Markdown template at: {EDITORIAL_MD}")
        log_msg("Please edit this file with your notes before running the editorial pipeline.")
        sys.exit(0)
        
    text = EDITORIAL_MD.read_text(encoding="utf-8")
    
    # Try parsing via LLM
    from llm import call_llm
    
    system_prompt = (
        "Você é um extrator de dados semântico de elite, frio, extremamente preciso e objective. "
        "Sua única função é ler o documento de diretrizes editoriais do autor em Markdown e convertê-lo em "
        "um JSON estruturado e validado. Você é totalmente sincero e assertivo, ignorando qualquer bajulação ou elogios.\n\n"
        "Estrutura do JSON a ser retornado:\n"
        "{\n"
        "  \"general_notes\": \"Texto das diretrizes gerais de estilo, tom, etc. (vazio se não houver)\",\n"
        "  \"chapters\": {\n"
        "    \"<numero_do_capitulo>\": {\n"
        "      \"brief\": \"Instruções específicas e condensadas para este capítulo\",\n"
        "      \"type\": \"punctual\" ou \"continuity_breaking\",\n"
        "      \"affects_downstream\": [lista de números inteiros de capítulos afetados se for quebra de continuidade]\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        "Regras Críticas de Extração:\n"
        "1. Identifique as seções do documento. A seção de diretrizes gerais geralmente tem cabeçalhos como '# Diretrizes Gerais' ou '# Geral'.\n"
        "2. Identifique os capítulos com base em cabeçalhos como '# Capítulo X', '# Cap X' ou '# Chapter X'. A chave sob 'chapters' deve ser apenas o número do capítulo como string (ex: \"11\").\n"
        "3. Determine assertivamente 'type' e 'affects_downstream'. Se a diretiva do capítulo alterar a cronologia do enredo, introduzir um novo objeto físico crucial (como uma chave física de bronze), revelar segredos que mudam o comportamento dos personagens, classifique-o assertivamente como 'continuity_breaking' e inclua no array 'affects_downstream' os capítulos subsequentes lógicos que sofrerão impacto direto, mesmo se o autor não os tiver listado explicitamente. Se a alteração for estritamente local (estilo, diálogos pontuais), use 'punctual' e deixe 'affects_downstream' vazio.\n\n"
        "Responda APENAS com o JSON válido. Não inclua nenhuma explicação, introdução ou conclusão fora do JSON."
    )
    
    user_prompt = (
        f"Conteúdo do editorial.md a ser extraído:\n\n{text}\n\n"
        "Extraia e responda apenas com o JSON."
    )
    
    try:
        log_msg("Calling LLM for semantic and assertive extraction of editorial.md...")
        response = call_llm(prompt=user_prompt, system_prompt=system_prompt, temperature=0.1, is_judge=True)
        
        # Clean response string of markdown wraps
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("\n", 1)[0]
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
            
        data = json.loads(cleaned)
        
        # Validate schema structure
        general_notes = data.get("general_notes", "").strip()
        chapters = {}
        
        for k, v in data.get("chapters", {}).items():
            if not k.isdigit():
                continue
            ch_num = int(k)
            chapters[ch_num] = {
                "brief": v.get("brief", "").strip(),
                "type": v.get("type", "punctual"),
                "affects_downstream": [int(x) for x in v.get("affects_downstream", [])]
            }
            
        log_msg("Semantic extraction via LLM completed successfully.")
        return {
            "general_notes": general_notes,
            "chapters": chapters
        }
    except Exception as e:
        log_msg(f"WARNING: Semantic extraction via LLM failed: {e}. Falling back to robust regex parser.")
        return load_editorial_markdown_fallback(text)

def classify_brief_with_ai(ch_num: int, brief: str) -> dict:
    """
    Call the LLM Judge model to critically analyze the chapter's editorial instructions.
    Returns a dictionary with 'type', 'affects_downstream', and 'criticism'.
    """
    from llm import call_llm
    
    system_prompt = (
        "Você é um editor literário de elite, extremamente crítico, pragmático e direto. "
        "Seu estilo é cirúrgico, frio, sem rodeios e totalmente desprovido de bajulação, elogios vazios ou formalidades. "
        "Sua missão é analisar as diretrizes de alteração de um capítulo e classificar seu impacto na estrutura da obra.\n\n"
        "Regras de Classificação:\n"
        "1. 'punctual': Mudanças estritamente locais no estilo, tom, diálogo ou ritmo do capítulo, "
        "sem alterar fatos do enredo, cronologia ou estados físicos/mentais dos personagens fora deste capítulo.\n"
        "2. 'continuity_breaking': Mudanças que introduzem novos fatos, segredos, objetos físicos, "
        "alteram o destino de um personagem ou mudam eventos históricos que causam impacto inevitável a jusante. "
        "Você DEVE classificar como 'continuity_breaking' e listar precisamente no array 'affects_downstream' os capítulos que precisam ser reescritos em sequência.\n\n"
        "Você DEVE responder estritamente com um objeto JSON válido contendo exatamente as chaves:\n"
        "{\n"
        "  \"type\": \"punctual\" ou \"continuity_breaking\",\n"
        "  \"affects_downstream\": [lista de números inteiros de capítulos afetados],\n"
        "  \"criticism\": \"Uma crítica sincera, fria, direta e absolutamente sem bajulação sobre o briefing fornecido.\"\n"
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

def get_all_chapter_numbers() -> list:
    """Scan chapters directory for existing chapter numbers."""
    numbers = []
    if CHAPTERS_DIR.exists():
        for f in CHAPTERS_DIR.glob("ch_*.md"):
            match = re.search(r"ch_(\d+)\.md", f.name)
            if match:
                numbers.append(int(match.group(1)))
    return sorted(numbers)


def parse_chapters_range(chapters_str: str, all_possible: list) -> list:
    """Parse strings like '1-4, 7, 9-11' or 'all' and return a sorted list of integers."""
    if not chapters_str or chapters_str.strip().lower() == "all":
        return all_possible
        
    nums = set()
    parts = chapters_str.split(",")
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            try:
                start_str, end_str = part.split("-", 1)
                start = int(start_str.strip())
                end = int(end_str.strip())
                for i in range(start, end + 1):
                    if i in all_possible:
                        nums.add(i)
            except ValueError:
                pass
        else:
            try:
                val = int(part)
                if val in all_possible:
                    nums.add(val)
            except ValueError:
                pass
    return sorted(list(nums))

def extract_eval_feedback(stdout: str) -> str:
    """
    Parse the evaluation stdout, locate the eval_log JSON path,
    read it, and return a formatted feedback string summarizing the issues.
    """
    match = re.search(r"eval_log:\s*(\S+)", stdout)
    if not match:
        return "Nenhum arquivo de log de avaliação encontrado no console."
        
    log_path = Path(match.group(1).strip())
    if not log_path.exists():
        return f"Arquivo de log de avaliação não encontrado no caminho: {log_path}"
        
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        feedback_parts = []
        
        # 1. Collect slop hits
        slop = data.get("slop", {})
        tier1 = slop.get("tier1_hits", [])
        tier2 = slop.get("tier2_hits", [])
        tics = slop.get("structural_ai_tics", [])
        tells = slop.get("fiction_ai_tells", [])
        em_dash_density = slop.get("em_dash_density", 0.0)
        
        slop_issues = []
        if tier1:
            slop_issues.append("- PALAVRAS PROIBIDAS usadas (MUDAR IMEDIATAMENTE): " + ", ".join([f"'{x[0]}' (usada {x[1]} vezes)" if isinstance(x, list) else str(x) for x in tier1]))
        if tier2:
            slop_issues.append("- Palavras suspeitas usadas (evitar): " + ", ".join([f"'{x[0]}' (usada {x[1]} vezes)" if isinstance(x, list) else str(x) for x in tier2]))
        if tics:
            slop_issues.append("- Tiques estruturais de IA detectados: " + ", ".join([f"'{x[0]}' (usada {x[1]} vezes)" if isinstance(x, list) else str(x) for x in tics]))
        if tells:
            slop_issues.append("- Clichês/tells de IA detectados: " + ", ".join([f"'{x[0]}' (usada {x[1]} vezes)" if isinstance(x, list) else str(x) for x in tells]))
        if em_dash_density > 15:
            slop_issues.append(f"- Densidade excessiva de travessões: {em_dash_density} (limite máximo é 15). Substitua a maioria dos travessões explicativos duplos (—) por vírgulas, parênteses ou reestruture as sentenças.")
            
        if slop_issues:
            feedback_parts.append("### PROBLEMAS DE SLOP & VOCABULÁRIO:")
            feedback_parts.extend(slop_issues)
            feedback_parts.append("")
            
        # 2. Collect canon/continuity issues
        canon = data.get("canon_compliance", {})
        if isinstance(canon, dict) and canon.get("violations"):
            feedback_parts.append("### VIOLAÇÕES DE CANON/LORE:")
            for violation in canon["violations"]:
                feedback_parts.append(f"- {violation}")
            feedback_parts.append("")
            
        # 3. Collect dimension specific fixes
        dimension_issues = []
        for key in ["voice_adherence", "beat_coverage", "character_voice", "plants_seeded", "prose_quality", "lore_integration", "engagement"]:
            dim_data = data.get(key, {})
            if isinstance(dim_data, dict) and dim_data.get("score", 10) < 7:
                fix_desc = dim_data.get("fix", "")
                weak_mom = dim_data.get("weakest_moment", "")
                if fix_desc or weak_mom:
                    dimension_issues.append(f"#### Dimensão '{key}' (Nota {dim_data.get('score')}):")
                    if weak_mom:
                        dimension_issues.append(f"  * Ponto fraco: \"{weak_mom}\"")
                    if fix_desc:
                        dimension_issues.append(f"  * Correção sugerida: {fix_desc}")
                        
        if dimension_issues:
            feedback_parts.append("### SUGESTÕES DAS DIMENSÕES DE AVALIAÇÃO:")
            feedback_parts.extend(dimension_issues)
            feedback_parts.append("")
            
        # 4. Weakest sentences
        weakest_sentences = data.get("three_weakest_sentences", [])
        if weakest_sentences:
            feedback_parts.append("### FRASES MAIS FRACAS (REESCREVER/MELHORAR):")
            for sentence in weakest_sentences:
                feedback_parts.append(f"- \"{sentence}\"")
            feedback_parts.append("")
            
        return "\n".join(feedback_parts)
    except Exception as e:
        return f"Falha ao ler o arquivo de log do avaliador para feedback: {e}"

def run_editorial(chapters_opt=None, all_opt=False, retries_opt=2):
    # Load configurable timeouts
    PIPELINE_TIMEOUT = int(os.environ.get("AUTOBOOK_PIPELINE_TIMEOUT", "3600"))
    REVISION_TIMEOUT = int(os.environ.get("AUTOBOOK_REVISION_TIMEOUT", str(max(PIPELINE_TIMEOUT, 1200))))
    EVAL_TIMEOUT = int(os.environ.get("AUTOBOOK_EVAL_TIMEOUT", str(max(PIPELINE_TIMEOUT // 2, 600))))
    EXPORT_TIMEOUT = int(os.environ.get("AUTOBOOK_EXPORT_TIMEOUT", str(max(PIPELINE_TIMEOUT // 2, 600))))

    # 1. Load the centralized briefs
    editorial = load_editorial_markdown()
    general_notes = editorial.get("general_notes", "")
    chapters_data = editorial.get("chapters", {})
    
    all_possible = get_all_chapter_numbers()
    
    # Resolve which chapters to run on
    target_chapters = []
    if all_opt:
        target_chapters = all_possible
    elif chapters_opt:
        target_chapters = parse_chapters_range(chapters_opt, all_possible)
    else:
        # Backward compatibility: process only the ones in editorial.md
        target_chapters = sorted(chapters_data.keys())
        
    if not target_chapters:
        log_msg("Warning: No chapters resolved to process. Exiting.")
        return
        
    banner("ANALYZING EDITORIAL DIRECTIVES")
    
    # 2. Hybrid impact analysis
    parsed_tasks = {}
    for ch_num in target_chapters:
        ch_info = chapters_data.get(ch_num)
        if ch_info:
            brief = ch_info.get("brief", "")
            user_type = ch_info.get("type", "punctual")
            user_downstream = ch_info.get("affects_downstream", [])
        else:
            brief = ""
            user_type = "punctual"
            user_downstream = []
            
        if brief.strip():
            step(f"Analyzing Chapter {ch_num} with Editorial Intelligence...")
            ai_analysis = classify_brief_with_ai(ch_num, brief)
            
            # Merge Downstream ranges
            merged_downstream = sorted(list(set([int(x) for x in user_downstream] + ai_analysis["affects_downstream"])))
            
            # Determine hybrid type
            if user_type == "continuity_breaking" or ai_analysis["type"] == "continuity_breaking" or len(merged_downstream) > 0:
                final_type = "continuity_breaking"
            else:
                final_type = "punctual"
            criticism = ai_analysis["criticism"]
        else:
            merged_downstream = []
            final_type = "punctual"
            criticism = "Sem diretivas específicas de capítulo. Aplicando apenas diretrizes gerais."
            
        parsed_tasks[ch_num] = {
            "brief": brief,
            "type": final_type,
            "affects_downstream": merged_downstream,
            "criticism": criticism
        }
        
    # 3. Present the Adjustment Plan (Dry-Run)
    print("\n" + "=" * 60)
    print("EDITORIAL ADJUSTMENT PLAN (AWAITING APPROVAL)")
    print("=" * 60)
    if general_notes:
        print(f"Diretrizes Gerais:\n{general_notes}\n")
        
    for ch_num in sorted(parsed_tasks.keys()):
        task = parsed_tasks[ch_num]
        type_str = "CONTINUITY BREAKING (CASCADE)" if task["type"] == "continuity_breaking" else "PUNCTUAL (LOCAL ADJUSTMENT)"
        print(f"[-] Chapter {ch_num:02d}: {type_str}")
        if task["brief"]:
            print(f"    Human Briefing:\n{task['brief']}")
        print(f"    Direct AI Criticism: \"{task['criticism']}\"")
        if task["affects_downstream"]:
            print(f"    Downstream Chapters Affected: {task['affects_downstream']}")
        print("-" * 60)
        
    # 4. Interactive prompt
    try:
        choice = input("\nDo you want to initiate the correction actions above? [Y/n] ").strip().lower()
        if choice not in ["", "y", "yes", "s", "sim"]:
            log_msg("Operation aborted by user.")
            return
    except (KeyboardInterrupt, EOFError):
        print("\nOperation aborted.")
        return
        
    # 5. Process revisions
    banner("EXECUTING EDITORIAL REVISIONS")
    
    # Track cascading continuity warnings
    # maps chapter -> list of strings
    continuity_warnings = {}
    
    # Process chapters in order
    sorted_chapters = sorted(parsed_tasks.keys())
    for ch_num in sorted_chapters:
        task = parsed_tasks[ch_num]
        banner(f"PROCESSING CHAPTER {ch_num:02d} ({task['type'].upper()})", char=".")
        
        # Build local brief content
        brief_lines = [
            f"# Diretivas de Correção Editorial - Capítulo {ch_num}",
            "",
            "## Solicitação Principal do Autor:",
            task["brief"] if task["brief"] else "Aplicar diretrizes gerais da obra neste capítulo.",
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
        
        # Backup and evaluation setup
        ch_file_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
        original_text = ch_file_path.read_text(encoding="utf-8") if ch_file_path.exists() else ""
        
        # Evaluate before revision
        pre_eval = run_tool(f"uv run python evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
        pre_score = parse_score(pre_eval.stdout, "overall_score")
        
        # Run revision (Attempt 1)
        step(f"Rewriting Chapter {ch_num} (Attempt 1)...")
        run_tool(f"uv run python gen_revision.py {ch_num} {temp_brief_path}", timeout=REVISION_TIMEOUT)
        
        # Evaluate after revision
        post_eval = run_tool(f"uv run python evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
        post_score = parse_score(post_eval.stdout, "overall_score")
        
        log_msg(f"Chapter {ch_num} Attempt 1: Score {pre_score} -> {post_score}")
        
        success = False
        best_fallback_text = ""
        best_fallback_score = -1.0
        
        if post_score >= pre_score:
            success = True
            log_msg(f"Chapter {ch_num} Attempt 1: Score improved or maintained.")
        else:
            # Save fallback
            best_fallback_text = ch_file_path.read_text(encoding="utf-8") if ch_file_path.exists() else ""
            best_fallback_score = post_score
            log_msg(f"Chapter {ch_num} Attempt 1: Regression detected. Saving fallback (score {best_fallback_score}).")
            
            # Start retry loop
            for retry_idx in range(1, retries_opt + 1):
                step(f"Rewriting Chapter {ch_num} (Corrective Retry Attempt {retry_idx + 1}/{retries_opt + 1})...")
                
                # Parse previous evaluate log for feedback
                feedback_str = extract_eval_feedback(post_eval.stdout)
                
                # Write corrective brief combining previous brief and feedback
                corrective_brief_lines = [
                    f"# Diretivas de Correção Editorial - Capítulo {ch_num} (RETENTATIVA CORRETIVA {retry_idx})",
                    "",
                    "A tentativa anterior de revisão não atingiu a pontuação mínima necessária devido a desvios ou problemas de qualidade no rascunho atual.",
                    "Sua missão é corrigir o rascunho atual para eliminar esses erros específicos, mantendo a coerência e as diretivas da história.",
                    "",
                    "## [PROBLEMAS CRÍTICOS A CORRIGIR]:",
                    feedback_str,
                    "",
                    "## [DIRETIVAS ORIGINAIS DE REVISÃO]:",
                    task["brief"] if task["brief"] else "Aplicar diretrizes gerais da obra neste capítulo.",
                ]
                if general_notes:
                    corrective_brief_lines += [
                        "",
                        "## [DIRETRIZES GERAIS DA OBRA]:",
                        general_notes
                    ]
                
                corrective_brief_path = BRIEFS_DIR / f"ch{ch_num:02d}_corrective_temp.md"
                corrective_brief_path.write_text("\n".join(corrective_brief_lines), encoding="utf-8")
                
                # Run revision
                run_tool(f"uv run python gen_revision.py {ch_num} {corrective_brief_path}", timeout=REVISION_TIMEOUT)
                
                # Clean up temp corrective brief
                if corrective_brief_path.exists():
                    corrective_brief_path.unlink()
                    
                # Evaluate again
                post_eval = run_tool(f"uv run python evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
                post_score = parse_score(post_eval.stdout, "overall_score")
                log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: Score {post_score} (baseline: {pre_score}, best fallback: {best_fallback_score})")
                
                if post_score >= pre_score:
                    success = True
                    log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: Success! Score is now {post_score} >= baseline {pre_score}.")
                    break
                else:
                    if post_score > best_fallback_score:
                        log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: Score {post_score} improved upon best fallback {best_fallback_score}. Updating fallback.")
                        best_fallback_text = ch_file_path.read_text(encoding="utf-8") if ch_file_path.exists() else ""
                        best_fallback_score = post_score
                    else:
                        log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: Score {post_score} is worse or equal to best fallback {best_fallback_score}. Restoring best fallback text for next pass.")
                        if best_fallback_text:
                            ch_file_path.write_text(best_fallback_text, encoding="utf-8")
                            
        # Decide kept state
        if success:
            commit_hash = git_add_commit(f"editorial: revise ch{ch_num:02d} ({task['type']}) {pre_score}->{post_score}")
            log_msg(f"Keeping revision for Chapter {ch_num:02d}. Commit: {commit_hash}")
            
            # If continuity breaking, register warnings for downstream chapters
            if task["type"] == "continuity_breaking":
                warning_msg = f"In Chapter {ch_num}, the following fact was established: {task['brief']}"
                for downstream_ch in task["affects_downstream"]:
                    if downstream_ch not in continuity_warnings:
                        continuity_warnings[downstream_ch] = []
                    continuity_warnings[downstream_ch].append(warning_msg)
        else:
            log_msg(f"All retries finished without reaching baseline {pre_score}. Keeping best fallback (score: {best_fallback_score}).")
            if best_fallback_text:
                ch_file_path.write_text(best_fallback_text, encoding="utf-8")
                commit_hash = git_add_commit(f"editorial: revise ch{ch_num:02d} (fallback {best_fallback_score} < {pre_score})")
                log_msg(f"Keeping fallback version for Chapter {ch_num:02d}. Commit: {commit_hash}")
            else:
                log_msg(f"No fallback text available. Reverting to pristine original.")
                if original_text:
                    ch_file_path.write_text(original_text, encoding="utf-8")
            
        # Clean up temporary brief file
        if temp_brief_path.exists():
            temp_brief_path.unlink()
            
    # 6. Rebuild manuscript, arc summary and LaTeX
    banner("CONSOLIDATING MANUSCRIPT AND STRUCTURE")
    run_tool("uv run python build_arc_summary.py", timeout=EXPORT_TIMEOUT)
    run_tool("uv run python build_outline.py", timeout=EXPORT_TIMEOUT)
    run_tool("uv run python typeset/build_tex.py", timeout=EXPORT_TIMEOUT)
    
    git_add_commit("editorial: finalize manuscript, outline, and LaTeX typeset consolidation")
    
    banner("EDITORIAL PIPELINE COMPLETED SUCCESSFULLY")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Automated Editorial Revision Pipeline.")
    parser.add_argument(
        "-c", "--chapters",
        type=str,
        help="Chapters to process, e.g., '1-4', '5,8', or 'all'."
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Shortcut to process all chapters."
    )
    parser.add_argument(
        "-r", "--retries",
        type=int,
        default=2,
        help="Maximum corrective retries on regression (default: 2)."
    )
    args = parser.parse_args()
    
    run_editorial(chapters_opt=args.chapters, all_opt=args.all, retries_opt=args.retries)

if __name__ == "__main__":
    main()
