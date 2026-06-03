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

def load_editorial_config() -> dict:
    from prompt_loader import get_active_language, PROMPTS_DIR
    lang = get_active_language()
    config_file = PROMPTS_DIR / lang / "editorial.json"
    if not config_file.exists() and lang != "EN":
        config_file = PROMPTS_DIR / "EN" / "editorial.json"
    if not config_file.exists():
        # Fallback to English/Portuguese defaults
        return {
            "retry_temp_map": {
                "1": 0.6,
                "2": 0.6,
                "3": 0.7,
                "4": 0.9,
                "5": 0.5
            },
            "feedback_labels": {
                "slop_critical_header": "### PROBLEMAS DE SLOP CRÍTICO:",
                "canon_violations_header": "### VIOLAÇÕES DE CANON/LORE:",
                "slop_style_header": "### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):",
                "narrative_dimensions_header": "### DEFICIÊNCIAS NAS DIMENSÕES NARRATIVAS:",
                "weakest_sentences_header": "### FRASES MAIS FRACAS (REESCREVER/MELHORAR):",
                "banned_words_msg": "- PALAVRAS PROIBIDAS usadas (MUDAR IMEDIATAMENTE): {words}",
                "suspicious_words_msg": "- Palavras suspeitas usadas (evitar): {words}",
                "structural_tics_msg": "- Tiques estruturais de IA detectados: {words}",
                "cliches_tells_msg": "- Clichês/tells de IA detectados: {words}",
                "em_dash_density_msg": "- Densidade excessiva de travessões: {density} (limite máximo é 15). Substitua a maioria dos travessões explicativos duplos (—) por vírgulas, parênteses ou reestruture as sentenças.",
                "dimension_header": "#### Dimensão '{dim}' (Nota {score}):",
                "weakest_moment_prefix": "  * Ponto fraco: \"{moment}\"",
                "suggested_fix_prefix": "  * Correção sugerida: {fix}"
            },
            "corrective_brief": {
                "header": "# DIRETIVAS DE RECORREÇÃO PARA RETENTATIVA",
                "subheader": "O rascunho anterior falhou na avaliação. Siga estritamente os feedbacks e correções detalhados abaixo ao regenerar o capítulo:",
                "footer_header": "### DIRETRIZES DA RE-EXECUÇÃO:",
                "footer_body": "Use como ponto de partida a versão anterior e modifique-a para incorporar todos os feedbacks acima, preservando toda a trama correta."
            }
        }
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

def get_retry_temperature(retry_idx: int) -> float:
    """Return the creative/corrective temperature for the given retry index (1-based)."""
    try:
        config = load_editorial_config()
        temp_map = config.get("retry_temp_map", {})
        return float(temp_map.get(str(retry_idx), 0.8))
    except Exception:
        temp_map = {1: 0.6, 2: 0.6, 3: 0.7, 4: 0.9, 5: 0.5}
        return temp_map.get(retry_idx, 0.8)

def extract_eval_feedback(stdout: str, retry_idx: int = 5) -> str:
    """
    Parse the evaluation stdout, locate the eval_log JSON path,
    read it, and return a formatted feedback string summarizing the issues,
    filtered progressively based on the corrective retry index (1 to 5).
    """
    match = re.search(r"eval_log:\s*(\S+)", stdout)
    if not match:
        return "No evaluation log file found in the console output."
        
    log_path = Path(match.group(1).strip())
    if not log_path.exists():
        return f"Evaluation log file not found at path: {log_path}"
        
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        feedback_parts = []
        
        # Load localized config
        config = load_editorial_config()
        labels = config.get("feedback_labels", {})
        
        # Parse data structures
        slop = data.get("slop", {})
        tier1 = slop.get("tier1_hits", [])
        tier2 = slop.get("tier2_hits", [])
        tics = slop.get("structural_ai_tics", [])
        tells = slop.get("fiction_ai_tells", [])
        em_dash_density = slop.get("em_dash_density", 0.0)
        
        # 1. Collect canon/continuity issues (Always included in all retries)
        canon = data.get("canon_compliance", {})
        canon_violations = []
        if isinstance(canon, dict) and canon.get("violations"):
            canon_violations = canon["violations"]
            
        # 2. Collect slop tier 1 hits (Always included in all retries)
        slop_tier1_issues = []
        if tier1:
            words_str = ", ".join([f"'{x[0]}' (used {x[1]} times)" if isinstance(x, list) else str(x) for x in tier1])
            banned_words_template = labels.get("banned_words_msg", "- BANNED WORDS used (CHANGE IMMEDIATELY): {words}")
            slop_tier1_issues.append(banned_words_template.format(words=words_str))
            
        # 3. Collect slop tier 2, tics, tells, em-dash (Included in retry >= 3)
        slop_style_issues = []
        if retry_idx >= 3:
            if tier2:
                words_str = ", ".join([f"'{x[0]}' (used {x[1]} times)" if isinstance(x, list) else str(x) for x in tier2])
                susp_words_template = labels.get("suspicious_words_msg", "- Suspicious words used (avoid): {words}")
                slop_style_issues.append(susp_words_template.format(words=words_str))
            if tics:
                words_str = ", ".join([f"'{x[0]}' (used {x[1]} times)" if isinstance(x, list) else str(x) for x in tics])
                tics_template = labels.get("structural_tics_msg", "- AI structural tics detected: {words}")
                slop_style_issues.append(tics_template.format(words=words_str))
            if tells:
                words_str = ", ".join([f"'{x[0]}' (used {x[1]} times)" if isinstance(x, list) else str(x) for x in tells])
                tells_template = labels.get("cliches_tells_msg", "- AI clichés/tells detected: {words}")
                slop_style_issues.append(tells_template.format(words=words_str))
            if em_dash_density > 15:
                em_dash_template = labels.get("em_dash_density_msg", "- Excessive em-dash density: {density}")
                slop_style_issues.append(em_dash_template.format(density=em_dash_density))
                
        # 4. Collect dimension specific fixes
        dimension_issues = []
        dimensions = ["voice_adherence", "beat_coverage", "character_voice", "plants_seeded", "prose_quality", "lore_integration", "engagement"]
        
        failing_dimensions = []
        for dim in dimensions:
            dim_data = data.get(dim, {})
            if isinstance(dim_data, dict):
                score = dim_data.get("score", 10)
                if score < 7:
                    failing_dimensions.append((dim, score, dim_data.get("fix", ""), dim_data.get("weakest_moment", "")))
                    
        failing_dimensions.sort(key=lambda x: x[1])
        
        target_dimensions = failing_dimensions
        if 2 <= retry_idx <= 4:
            target_dimensions = failing_dimensions[:2]
        elif retry_idx < 2:
            target_dimensions = []
            
        dim_header_template = labels.get("dimension_header", "#### Dimension '{dim}' (Score {score}):")
        weak_moment_template = labels.get("weakest_moment_prefix", "  * Weakest moment: \"{moment}\"")
        suggested_fix_template = labels.get("suggested_fix_prefix", "  * Suggested fix: {fix}")
        
        for dim, score, fix_desc, weak_mom in target_dimensions:
            if fix_desc or weak_mom:
                dimension_issues.append(dim_header_template.format(dim=dim, score=score))
                if weak_mom:
                    dimension_issues.append(weak_moment_template.format(moment=weak_mom))
                if fix_desc:
                    dimension_issues.append(suggested_fix_template.format(fix=fix_desc))
                    
        # 5. Weakest sentences (Included in retry >= 4)
        weakest_sentences = []
        if retry_idx >= 4:
            weakest_sentences = data.get("three_weakest_sentences", [])
            
        # Format the feedback string
        if slop_tier1_issues:
            feedback_parts.append(labels.get("slop_critical_header", "### CRITICAL SLOP PROBLEMS:"))
            feedback_parts.extend(slop_tier1_issues)
            feedback_parts.append("")
            
        if canon_violations:
            feedback_parts.append(labels.get("canon_violations_header", "### CANON/LORE VIOLATIONS:"))
            for violation in canon_violations:
                feedback_parts.append(f"- {violation}")
            feedback_parts.append("")
            
        if slop_style_issues:
            feedback_parts.append(labels.get("slop_style_header", "### STYLE & VOCABULARY (SECONDARY SLOP):"))
            feedback_parts.extend(slop_style_issues)
            feedback_parts.append("")
            
        if dimension_issues:
            feedback_parts.append(labels.get("narrative_dimensions_header", "### NARRATIVE DIMENSION DEFICIENCIES:"))
            feedback_parts.extend(dimension_issues)
            feedback_parts.append("")
            
        if weakest_sentences:
            feedback_parts.append(labels.get("weakest_sentences_header", "### WEAKEST SENTENCES (REWRITE/IMPROVE):"))
            for sentence in weakest_sentences:
                feedback_parts.append(f"- \"{sentence}\"")
            feedback_parts.append("")
            
        return "\n".join(feedback_parts)
    except Exception as e:
        return f"Failure reading evaluation log for feedback: {e}"

def get_eval_data(stdout: str) -> dict:
    """Parse the evaluation stdout, locate the eval_log JSON path, and load its JSON contents."""
    match = re.search(r"eval_log:\s*(\S+)", stdout)
    if not match:
        return {}
    log_path = Path(match.group(1).strip())
    if not log_path.exists():
        return {}
    try:
        return json.loads(log_path.read_text(encoding="utf-8"))
    except Exception:
        return {}

def run_editorial(chapters_opt=None, all_opt=False, auto_approve=False):
    NUM_EDITORIAL_RETRIES = 5
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
    if auto_approve:
        log_msg("Auto-approving the adjustment plan due to --yes / -y flag.")
    else:
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
        pre_data = get_eval_data(pre_eval.stdout)
        pre_score = pre_data.get("overall_score", 0.0)
        
        # Option 3 check: Skip if no directives of any kind AND the current version is already perfect
        has_specific_brief = bool(task["brief"].strip()) if task["brief"] else False
        has_general_notes = bool(general_notes.strip()) if general_notes else False
        has_continuity_warnings = bool(ch_num in continuity_warnings and continuity_warnings[ch_num])
        pre_slop = pre_data.get("slop", {}).get("slop_penalty", 0.0)
        
        if (not has_specific_brief) and (not has_general_notes) and (not has_continuity_warnings):
            if pre_score >= 7.0 and pre_slop == 0.0:
                log_msg(f"Chapter {ch_num:02d} has no directives, no general notes, no continuity warnings, and already has a high-quality score ({pre_score}) with zero slop. Skipping revision.")
                continue
        
        # Run revision (Attempt 1)
        step(f"Rewriting Chapter {ch_num} (Attempt 1)...")
        run_tool(f"uv run python gen_revision.py {ch_num} {temp_brief_path} --temperature 0.8", timeout=REVISION_TIMEOUT)
        
        # Evaluate after revision
        post_eval = run_tool(f"uv run python evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
        post_data = get_eval_data(post_eval.stdout)
        post_score = post_data.get("overall_score", 0.0)
        slop_penalty = post_data.get("slop", {}).get("slop_penalty", 0.0)
        
        log_msg(f"Chapter {ch_num} Attempt 1: Score {pre_score} -> {post_score} (Slop Penalty: {slop_penalty})")
        
        success = False
        best_fallback_text = ""
        best_fallback_score = -1.0
        best_fallback_slop = 999.0
        
        # We immediately succeed only if the score is >= baseline, >= 7.0 (high quality), and has zero slop penalty
        if post_score >= pre_score and post_score >= 7.0 and slop_penalty == 0.0:
            success = True
            log_msg(f"Chapter {ch_num} Attempt 1: High quality score and zero slop achieved ({post_score}).")
        else:
            # Save fallback
            best_fallback_text = ch_file_path.read_text(encoding="utf-8") if ch_file_path.exists() else ""
            best_fallback_score = post_score
            best_fallback_slop = slop_penalty
            log_msg(f"Chapter {ch_num} Attempt 1: Needs optimization. Saving fallback (score {best_fallback_score}, slop penalty {best_fallback_slop}).")
            
            # Start retry loop
            for retry_idx in range(1, NUM_EDITORIAL_RETRIES + 1):
                step(f"Rewriting Chapter {ch_num} (Corrective Retry Attempt {retry_idx + 1}/{NUM_EDITORIAL_RETRIES + 1})...")
                
                # Parse previous evaluate log for feedback with progressive filtering
                feedback_str = extract_eval_feedback(post_eval.stdout, retry_idx=retry_idx)
                
                # Load localized brief templates
                editorial_config = load_editorial_config()
                brief_tmpl = editorial_config.get("corrective_brief", {})
                
                # Write corrective brief combining previous brief and feedback
                header_text = brief_tmpl.get("header", "# DIRETIVAS DE RECORREÇÃO PARA RETENTATIVA")
                subheader_text = brief_tmpl.get("subheader", "O rascunho anterior falhou na avaliação. Siga estritamente os feedbacks e correções detalhados abaixo ao regenerar o capítulo:")
                footer_header_text = brief_tmpl.get("footer_header", "DIRETRIZES DA RE-EXECUÇÃO")
                footer_body_text = brief_tmpl.get("footer_body", "Use como ponto de partida a versão anterior e modifique-a para incorporar todos os feedbacks acima, preservando toda a trama correta.")
                
                corrective_brief_lines = [
                    f"{header_text} - Capítulo {ch_num} ({retry_idx})",
                    "",
                    subheader_text,
                    "",
                    feedback_str,
                    "",
                    f"## [{footer_header_text}]:",
                    footer_body_text,
                    "",
                    f"## [ORIGINAL DIRECTIVES]:",
                    task["brief"] if task["brief"] else "Apply general directives.",
                ]
                if general_notes:
                    corrective_brief_lines += [
                        "",
                        "## [GENERAL NOTES]:",
                        general_notes
                    ]
                
                corrective_brief_path = BRIEFS_DIR / f"ch{ch_num:02d}_corrective_temp.md"
                corrective_brief_path.write_text("\n".join(corrective_brief_lines), encoding="utf-8")
                
                # Run revision with dynamic temperature
                retry_temp = get_retry_temperature(retry_idx)
                run_tool(f"uv run python gen_revision.py {ch_num} {corrective_brief_path} --temperature {retry_temp}", timeout=REVISION_TIMEOUT)
                
                # Clean up temp corrective brief
                if corrective_brief_path.exists():
                    corrective_brief_path.unlink()
                    
                # Evaluate again
                post_eval = run_tool(f"uv run python evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
                post_data = get_eval_data(post_eval.stdout)
                post_score = post_data.get("overall_score", 0.0)
                slop_penalty = post_data.get("slop", {}).get("slop_penalty", 0.0)
                
                log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: Score {post_score}, Slop Penalty {slop_penalty} (baseline: {pre_score}, best fallback: {best_fallback_score}, best fallback slop: {best_fallback_slop})")
                
                if post_score >= pre_score and post_score >= 7.0 and slop_penalty == 0.0:
                    success = True
                    log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: Success! Perfect score and quality achieved.")
                    break
                else:
                    # Check if this attempt is better than the fallback (prefer higher score, tie-break on lower slop)
                    is_better = False
                    if post_score > best_fallback_score:
                        is_better = True
                    elif post_score == best_fallback_score:
                        if slop_penalty < best_fallback_slop:
                            is_better = True
                            
                    if is_better:
                        log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: Score/slop improved upon best fallback. Updating fallback.")
                        best_fallback_text = ch_file_path.read_text(encoding="utf-8") if ch_file_path.exists() else ""
                        best_fallback_score = post_score
                        best_fallback_slop = slop_penalty
                    else:
                        log_msg(f"Chapter {ch_num} Attempt {retry_idx + 1}: No improvement. Restoring best fallback text for next pass.")
                        if best_fallback_text:
                            ch_file_path.write_text(best_fallback_text, encoding="utf-8")
                            
        # Decide kept state
        if success or best_fallback_score >= pre_score:
            final_kept_score = post_score if success else best_fallback_score
            if not success and best_fallback_text:
                ch_file_path.write_text(best_fallback_text, encoding="utf-8")
            commit_hash = git_add_commit(f"editorial: revise ch{ch_num:02d} ({task['type']}) {pre_score}->{final_kept_score}")
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
    
    # Run global timeline and continuity validation (non-strict for audit report)
    run_tool("uv run python verify_continuity.py", timeout=EVAL_TIMEOUT)
    
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
        "-y", "--yes",
        action="store_true",
        help="Bypass interactive approval and run the pipeline automatically."
    )
    args = parser.parse_args()
    
    run_editorial(chapters_opt=args.chapters, all_opt=args.all, auto_approve=args.yes)

if __name__ == "__main__":
    main()
