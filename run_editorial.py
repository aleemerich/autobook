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
        log_msg(f"Criado arquivo de template editorial em Markdown: {EDITORIAL_MD}")
        log_msg("Edite este arquivo com suas anotações antes de rodar o pipeline editorial.")
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
        log_msg("Chamando LLM para extração semântica e assertiva do editorial.md...")
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
            
        log_msg("Extração semântica via LLM concluída com sucesso.")
        return {
            "general_notes": general_notes,
            "chapters": chapters
        }
    except Exception as e:
        log_msg(f"AVISO: Falha na extração semântica via LLM: {e}. Usando parser de fallback robusto baseado em regex.")
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

def run_editorial():
    # 1. Load the centralized briefs
    editorial = load_editorial_markdown()
    general_notes = editorial.get("general_notes", "")
    chapters_data = editorial.get("chapters", {})
    
    if not chapters_data:
        log_msg("Aviso: Nenhuma diretiva de capítulos encontrada no Markdown. Encerrando.")
        return
        
    banner("ANALISANDO DIRETIVAS EDITORIAIS")
    
    # 2. Hybrid impact analysis
    parsed_tasks = {}
    for ch_num, ch_info in chapters_data.items():
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
        print(f"Diretrizes Gerais:\n{general_notes}\n")
        
    for ch_num in sorted(parsed_tasks.keys()):
        task = parsed_tasks[ch_num]
        type_str = "QUEBRA DE CONTINUIDADE (CASCATA)" if task["type"] == "continuity_breaking" else "PONTUAL (AJUSTE LOCAL)"
        print(f"[-] Capítulo {ch_num:02d}: {type_str}")
        print(f"    Briefing Humano:\n{task['brief']}")
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
