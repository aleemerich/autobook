#!/usr/bin/env python3
"""
pipelines/editorial_revision.py — Editorial Revision Pipeline.
Parses editorial.md, performs dynamic and corrective chapter rewriting,
and validates improvements against the evaluation harness.
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from pipelines.base import Step, Pipeline
from llm import call_llm
from evaluate import evaluate_chapter

BASE_DIR = Path(__file__).parent.parent.resolve()
CHAPTERS_DIR = BASE_DIR / "chapters"
BOOK_DATA_DIR = BASE_DIR / "book_data"
EDITORIAL_MD = BOOK_DATA_DIR / "editorial.md"

def load_editorial_config() -> dict:
    from prompt_loader import get_active_language, PROMPTS_DIR
    lang = get_active_language()
    config_file = PROMPTS_DIR / lang / "editorial.json"
    if not config_file.exists() and lang != "EN":
        config_file = PROMPTS_DIR / "EN" / "editorial.json"
    if not config_file.exists():
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
                "em_dash_density_msg": "- Densidade excessiva de travessões: {density} (limite máximo é 15).",
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
    try:
        config = load_editorial_config()
        temp_map = config.get("retry_temp_map", {})
        return float(temp_map.get(str(retry_idx), 0.8))
    except Exception:
        temp_map = {1: 0.6, 2: 0.6, 3: 0.7, 4: 0.9, 5: 0.5}
        return temp_map.get(retry_idx, 0.8)

def load_editorial_markdown_fallback(text: str) -> dict:
    """Fallback parser using regex in case the LLM API is unavailable."""
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
            match = re.search(r"(?:capítulo|cap|chapter)\s*(\d+)", title)
            if match:
                ch_num = int(match.group(1))
                downstream = []
                ds_match = re.search(r"(?:affects_downstream|afeta|jusante|affects)\s*:\s*([0-9\s,]+)", content, re.IGNORECASE)
                if ds_match:
                    downstream = [int(x.strip()) for x in ds_match.group(1).split(",") if x.strip().isdigit()]
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
    """Parse the centralized editorial.md using an LLM semantic extractor with regex fallback."""
    if not EDITORIAL_MD.exists():
        return {"general_notes": "", "chapters": {}}
        
    text = EDITORIAL_MD.read_text(encoding="utf-8")
    
    system_prompt = (
        "Você é um extrator de dados semânticos estruturados para pipelines editoriais literários.\n"
        "Sua tarefa é analisar o arquivo markdown editorial.md contendo diretrizes gerais de estilo e edições específicas de capítulos "
        "e convertê-lo em um JSON com formato estrito.\n\n"
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
        "1. Identifique as seções do documento. Geralmente '# Diretrizes Gerais' ou '# Geral'.\n"
        "2. Identifique os capítulos com base em cabeçalhos como '# Capítulo X', '# Cap X' ou '# Chapter X'. A chave sob 'chapters' deve ser apenas o número do capítulo como string.\n"
        "3. Determine 'type' e 'affects_downstream'. Se a diretiva alterar a cronologia do enredo, introduzir objetos novos cruciais ou alterar eventos, use 'continuity_breaking' e liste os subsequentes. Se for local, use 'punctual' e deixe 'affects_downstream' vazio.\n\n"
        "Responda APENAS com o JSON válido."
    )
    
    user_prompt = f"Conteúdo do editorial.md:\n\n{text}\n\nExtraia e responda apenas com o JSON."
    
    try:
        response = call_llm(prompt=user_prompt, system_prompt=system_prompt, temperature=0.1, is_judge=True)
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("\n", 1)[0]
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
            
        data = json.loads(cleaned)
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
        return {"general_notes": general_notes, "chapters": chapters}
    except Exception as e:
        print(f"[Warning] Semantic extraction failed: {e}. Falling back to regex parser.", file=sys.stderr)
        return load_editorial_markdown_fallback(text)

def format_eval_feedback(eval_data: dict, retry_idx: int) -> str:
    """Formats raw evaluation metrics and scores into markdown directives for LLM correction."""
    feedback_parts = []
    
    # 1. Canon
    canon = eval_data.get("canon_compliance", {})
    if isinstance(canon, dict) and canon.get("violations"):
        feedback_parts.append("### VIOLAÇÕES DE CANON/LORE:")
        for v in canon["violations"]:
            feedback_parts.append(f"- {v}")
            
    # 2. Slop
    slop = eval_data.get("slop", {})
    tier1 = slop.get("tier1_hits", [])
    tier2 = slop.get("tier2_hits", [])
    tics = slop.get("structural_ai_tics", [])
    tells = slop.get("fiction_ai_tells", [])
    em_dash = slop.get("em_dash_density", 0.0)
    
    slop_critical = []
    if tier1:
        words = ", ".join([f"'{w[0]}' (usado {w[1]} vezes)" for w in tier1])
        slop_critical.append(f"- PALAVRAS PROIBIDAS usadas (MUDAR IMEDIATAMENTE): {words}")
    if slop_critical:
        feedback_parts.append("### PROBLEMAS DE SLOP CRÍTICO:")
        feedback_parts.extend(slop_critical)
        
    slop_style = []
    if retry_idx >= 3:
        if tier2:
            words = ", ".join([f"'{w[0]}' (usado {w[1]} vezes)" for w in tier2])
            slop_style.append(f"- Palavras suspeitas usadas: {words}")
        if tics:
            words = ", ".join([f"'{w[0]}' (usado {w[1]} vezes)" for w in tics])
            slop_style.append(f"- Tiques estruturais de IA detectados: {words}")
        if tells:
            words = ", ".join([f"'{w[0]}' (usado {w[1]} vezes)" for w in tells])
            slop_style.append(f"- Clichês/tells de IA detectados: {words}")
        if em_dash > 15:
            slop_style.append(f"- Densidade excessiva de travessões: {em_dash} (limite máximo é 15)")
            
    if slop_style:
        feedback_parts.append("### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):")
        feedback_parts.extend(slop_style)
        
    # 3. Narrative Dimensions
    dimensions = ["voice_adherence", "beat_coverage", "character_voice", "plants_seeded", "prose_quality", "lore_integration", "engagement"]
    failing = []
    for dim in dimensions:
        dim_data = eval_data.get(dim, {})
        if isinstance(dim_data, dict):
            score = dim_data.get("score", 10)
            if score < 7:
                failing.append((dim, score, dim_data.get("fix", ""), dim_data.get("weakest_moment", "")))
                
    failing.sort(key=lambda x: x[1])
    target_dimensions = failing
    if 2 <= retry_idx <= 4:
        target_dimensions = failing[:2]
    elif retry_idx < 2:
        target_dimensions = []
        
    if target_dimensions:
        feedback_parts.append("### DEFICIÊNCIAS NAS DIMENSÕES NARRATIVAS:")
        for dim, score, fix, moment in target_dimensions:
            feedback_parts.append(f"#### Dimensão '{dim}' (Nota {score}):")
            if moment:
                feedback_parts.append(f"  * Ponto fraco: \"{moment}\"")
            if fix:
                feedback_parts.append(f"  * Correção sugerida: {fix}")
                
    # 4. Weakest sentences
    weak_sentences = eval_data.get("three_weakest_sentences", [])
    if weak_sentences:
        feedback_parts.append("### FRASES MAIS FRACAS (REESCREVER/MELHORAR):")
        for s in weak_sentences:
            feedback_parts.append(f"- \"{s}\"")
            
    return "\n".join(feedback_parts)


class LoadEditorialStep(Step):
    def __init__(self):
        super().__init__("Load and Parse editorial.md")

    def run(self, context: Dict[str, Any]) -> None:
        print("[LoadEditorialStep] Parsing editorial.md...")
        parsed = load_editorial_markdown()
        context["general_notes"] = parsed.get("general_notes", "")
        context["chapters_briefs"] = parsed.get("chapters", {})
        print(f"[LoadEditorialStep] Found general notes and {len(context['chapters_briefs'])} chapter-specific brief(s).")


class ExecuteEditorialStep(Step):
    def __init__(self):
        super().__init__("Execute Editorial Rewrites")

    def run(self, context: Dict[str, Any]) -> None:
        chapters_briefs = context.get("chapters_briefs", {})
        general_notes = context.get("general_notes", "")
        
        # Determine chapters to process
        target_chapters = context.get("chapters")
        if not target_chapters:
            # Fallback: process all chapters specified in editorial.md
            target_chapters = sorted(list(chapters_briefs.keys()))
            
        if not target_chapters:
            print("[ExecuteEditorialStep] No chapters specified and no chapters found in editorial.md. Skipping.")
            return
            
        print(f"[ExecuteEditorialStep] Chapters to process: {target_chapters}")
        
        num_retries = int(os.environ.get("NUM_EDITORIAL_RETRIES", 5))
        temp_map = {1: 0.6, 2: 0.6, 3: 0.7, 4: 0.9, 5: 0.5}
        
        for ch_num in target_chapters:
            print(f"\n======================================")
            print(f"Processing Editorial Revision: Chapter {ch_num}")
            print(f"======================================")
            
            ch_file_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
            if not ch_file_path.exists():
                print(f"[ExecuteEditorialStep] Chapter file {ch_file_path} does not exist. Skipping.")
                continue
                
            original_text = ch_file_path.read_text(encoding="utf-8")
            
            # Evaluate baseline
            print("[ExecuteEditorialStep] Measuring pre-editorial baseline score...")
            eval_data = evaluate_chapter(ch_num)
            pre_score = eval_data.get("overall_score", 0.0)
            pre_slop = eval_data.get("slop", {}).get("slop_penalty", 0.0)
            print(f"[ExecuteEditorialStep] Baseline Score: {pre_score} (Slop: {pre_slop})")
            
            task = chapters_briefs.get(ch_num, {"brief": "Apply general directives.", "type": "punctual", "affects_downstream": []})
            
            # Create a temporary brief combining chapter-specific brief + general notes
            brief_content = f"# DIRETIVAS EDITORIAIS\n\n{task['brief']}\n\n## DIRETIVAS GERAIS\n{general_notes}"
            temp_brief_path = BASE_DIR / f"ch{ch_num:02d}_brief_temp.txt"
            temp_brief_path.write_text(brief_content, encoding="utf-8")
            
            # Initial run of revision
            print(f"[ExecuteEditorialStep] Generating initial rewrite for Chapter {ch_num}...")
            subprocess.run(
                [sys.executable, "gen_revision.py", str(ch_num), str(temp_brief_path), "--temperature", "0.8"],
                cwd=str(BASE_DIR),
                check=True
            )
            
            # Evaluate the first draft
            eval_data = evaluate_chapter(ch_num)
            post_score = eval_data.get("overall_score", 0.0)
            slop_penalty = eval_data.get("slop", {}).get("slop_penalty", 0.0)
            
            success = False
            best_fallback_text = ch_file_path.read_text(encoding="utf-8")
            best_fallback_score = post_score
            best_fallback_slop = slop_penalty
            
            print(f"[ExecuteEditorialStep] Attempt 1 Score: {post_score} (Slop: {slop_penalty})")
            
            if post_score >= pre_score and post_score >= 7.0 and slop_penalty == 0.0:
                success = True
                print("[ExecuteEditorialStep] Attempt 1 reached target quality.")
            else:
                # Start retry feedback loops
                for retry_idx in range(1, num_retries + 1):
                    print(f"[ExecuteEditorialStep] Corrective Loop {retry_idx}/{num_retries} for Chapter {ch_num}...")
                    
                    feedback_str = format_eval_feedback(eval_data, retry_idx)
                    
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
                        task["brief"],
                        "",
                        "## DIRETIVAS GERAIS:",
                        general_notes
                    ]
                    
                    corrective_brief_path = BASE_DIR / f"ch{ch_num:02d}_corrective_temp.txt"
                    corrective_brief_path.write_text("\n".join(corrective_brief_lines), encoding="utf-8")
                    
                    retry_temp = temp_map.get(retry_idx, 0.7)
                    
                    subprocess.run(
                        [sys.executable, "gen_revision.py", str(ch_num), str(corrective_brief_path), "--temperature", str(retry_temp)],
                        cwd=str(BASE_DIR),
                        check=True
                    )
                    
                    if corrective_brief_path.exists():
                        corrective_brief_path.unlink()
                        
                    # Evaluate again
                    eval_data = evaluate_chapter(ch_num)
                    post_score = eval_data.get("overall_score", 0.0)
                    slop_penalty = eval_data.get("slop", {}).get("slop_penalty", 0.0)
                    print(f"[ExecuteEditorialStep] Corrective Loop {retry_idx} Score: {post_score} (Slop: {slop_penalty})")
                    
                    if post_score >= pre_score and post_score >= 7.0 and slop_penalty == 0.0:
                        success = True
                        print("[ExecuteEditorialStep] Corrective loop successfully hit quality goals.")
                        break
                    else:
                        is_better = False
                        if post_score > best_fallback_score:
                            is_better = True
                        elif post_score == best_fallback_score:
                            if slop_penalty < best_fallback_slop:
                                is_better = True
                                
                        if is_better:
                            best_fallback_text = ch_file_path.read_text(encoding="utf-8")
                            best_fallback_score = post_score
                            best_fallback_slop = slop_penalty
                        else:
                            # Revert to the best text so far before next iteration
                            ch_file_path.write_text(best_fallback_text, encoding="utf-8")
            
            # Cleanup temp brief
            if temp_brief_path.exists():
                temp_brief_path.unlink()
                
            # Finalize kept version
            if success or best_fallback_score >= pre_score:
                final_score = post_score if success else best_fallback_score
                if not success:
                    ch_file_path.write_text(best_fallback_text, encoding="utf-8")
                
                print(f"[ExecuteEditorialStep] Committing changes for Chapter {ch_num} (Score: {final_score})...")
                subprocess.run(["git", "add", f"chapters/ch_{ch_num:02d}.md"], cwd=str(BASE_DIR))
                commit_msg = f"editorial: revised ch{ch_num:02d} ({pre_score} -> {final_score})"
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(BASE_DIR))
                subprocess.run(["git", "push"], cwd=str(BASE_DIR))
            else:
                print(f"[ExecuteEditorialStep] All attempts failed to improve. Reverting to original pristine text.")
                ch_file_path.write_text(original_text, encoding="utf-8")
                
        # Consolidate outline and manuscript
        print("[ExecuteEditorialStep] Consolidating manuscript and outlines...")
        if (BASE_DIR / "legacy" / "build_outline.py").exists():
            subprocess.run(["uv", "run", "python", "legacy/build_outline.py"], cwd=str(BASE_DIR))
        if (BASE_DIR / "verify_continuity.py").exists():
            subprocess.run(["uv", "run", "python", "verify_continuity.py"], cwd=str(BASE_DIR))


class EditorialRevisionPipeline(Pipeline):
    def __init__(self):
        super().__init__("Editorial Revision Pipeline")
        self.add_step(LoadEditorialStep())
        self.add_step(ExecuteEditorialStep())
