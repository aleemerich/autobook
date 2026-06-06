#!/usr/bin/env python3
"""
verify_continuity.py — Global Novel Continuity and Timeline Validator.

Parses outline.md to extract chapter-by-chapter summaries and beats,
sends them to the LLM Continuity Judge, and analyzes the entire timeline
for repetitions, timeline loops, spatial conflicts, and broken transitions.
"""

import os
import sys
import json
import re
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")

# Insert local path to load llm and prompt_loader
sys.path.insert(0, str(BASE_DIR))
from llm import call_llm

OUTLINE_PATH = BASE_DIR / "book_data" / "outline.md"
EVAL_LOGS_DIR = BASE_DIR / "logs" / "eval_logs"
BUILD_OUTLINE_PY = BASE_DIR / "legacy" / "build_outline.py"

def parse_json_response(text):
    """Extract JSON from a response that might have markdown fences or trailing text."""
    text = text.strip()
    
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
    if text.endswith("```"):
        text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass
        
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end < start:
        raise ValueError("No valid JSON object found in response")
        
    json_candidate = text[start:end+1]
    
    try:
        return json.loads(json_candidate, strict=False)
    except json.JSONDecodeError:
        pass
        
    # Try quote repair
    repaired = re.sub(r',\s*([}\]])', r'\1', json_candidate)
    repaired = repair_json_quotes(repaired)
    try:
        return json.loads(repaired, strict=False)
    except json.JSONDecodeError as e:
        fixed = re.sub(r'(?<!\\)\n', '\\n', repaired)
        try:
            return json.loads(fixed, strict=False)
        except json.JSONDecodeError:
            raise e

def repair_json_quotes(s):
    result = []
    in_string = False
    escape = False
    i = 0
    n = len(s)
    
    while i < n:
        c = s[i]
        if escape:
            result.append(c)
            escape = False
            i += 1
            continue
            
        if c == '\\':
            result.append(c)
            escape = True
            i += 1
            continue
            
        if c == '"':
            is_structural = False
            
            if not in_string:
                is_structural = True
            else:
                next_non_ws = ""
                j = i + 1
                while j < n:
                    if not s[j].isspace():
                        next_non_ws = s[j]
                        break
                    j += 1
                
                if next_non_ws in [':', '}', ']', ','] or next_non_ws == "":
                    is_structural = True
            
            if is_structural:
                in_string = not in_string
                result.append(c)
            else:
                result.append('\\"')
        else:
            result.append(c)
        i += 1
        
    return "".join(result)


def validate_and_repair_json(raw_text, required_key="continuity_score"):
    """
    Validate that raw_text is a valid JSON and contains the required_key.
    If standard JSON parsing fails or the key is missing, attempts to extract
    the required key and reconstruct a minimal valid dict.
    Returns the parsed dict if successful/repaired, or None if completely invalid.
    """
    # 1. Try normal parsing
    try:
        data = parse_json_response(raw_text)
        if isinstance(data, dict) and required_key in data:
            if required_key == "continuity_score":
                if "inconsistencies" not in data or not isinstance(data["inconsistencies"], list):
                    data["inconsistencies"] = []
                if "timeline_flow" not in data:
                    data["timeline_flow"] = ""
            return data
    except Exception:
        pass

    # 2. Regex fallback for required_key
    score_match = re.search(rf'"{required_key}"\s*:\s*(\d+(?:\.\d+)?)', raw_text)
    if score_match:
        try:
            score_val = float(score_match.group(1))
            if required_key == "continuity_score":
                return {
                    "continuity_score": score_val,
                    "inconsistencies": [],
                    "timeline_flow": "Reconstruído via extração regex."
                }
        except Exception:
            pass
    return None


def get_reduced_chapters_data(chapters_data):
    reduced = []
    for ch in chapters_data:
        reduced.append({
            "num": ch["num"],
            "title": ch["title"],
            "location": ch["location"],
            "characters": ch["characters"],
            "summary": ch["summary"][:150] + "..." if len(ch["summary"]) > 150 else ch["summary"],
            "beats": ch["beats"][:3],
            "plants": ch["plants"],
            "harvests": ch["harvests"]
        })
    return reduced


def get_minimal_chapters_data(chapters_data):
    minimal = []
    for ch in chapters_data:
        minimal.append({
            "num": ch["num"],
            "title": ch["title"],
            "location": ch["location"],
            "beats": ch["beats"][:2],
            "summary": ch["summary"][:50] + "..." if len(ch["summary"]) > 50 else ch["summary"]
        })
    return minimal

def parse_outline(outline_path: Path) -> list:
    """Parse outline.md and extract structured fields per chapter."""
    if not outline_path.exists():
        return []
        
    text = outline_path.read_text(encoding="utf-8")
    
    # Split by chapters using the headers. Matches '### Ch X: ...' or '### Chapter X: ...'
    chapters_raw = re.split(r'^###\s+Ch(?:apter)?\s+(\d+):', text, flags=re.MULTILINE)
    
    entries = []
    if len(chapters_raw) < 2:
        return entries
        
    for i in range(1, len(chapters_raw), 2):
        ch_num = int(chapters_raw[i])
        ch_content = chapters_raw[i+1]
        
        # Split ch_content at '---' to isolate this chapter's entry from next or ledgers
        ch_body = ch_content.split('\n---')[0].strip()
        
        lines = ch_body.split('\n')
        title_line = lines[0].strip() if lines else f"Chapter {ch_num}"
        
        # Extract location
        location = "N/A"
        loc_match = re.search(r'\*\*Location:\*\*\s*(.*)$', ch_body, re.MULTILINE)
        if loc_match:
            location = loc_match.group(1).strip()
            
        # Extract characters
        characters = []
        char_match = re.search(r'-\s*\*\*Characters:\*\*\s*(.*)$', ch_body, re.MULTILINE)
        if char_match:
            characters = [c.strip() for c in char_match.group(1).split(',') if c.strip()]
            
        # Extract try-fail
        try_fail = "N/A"
        tf_match = re.search(r'-\s*\*\*Try-fail cycle:\*\*\s*(.*)$', ch_body, re.MULTILINE)
        if tf_match:
            try_fail = tf_match.group(1).strip()
            
        # Extract emotional arc
        emotional_arc = "N/A"
        ea_match = re.search(r'-\s*\*\*Emotional arc:\*\*\s*(.*)$', ch_body, re.MULTILINE)
        if ea_match:
            emotional_arc = ea_match.group(1).strip()
            
        # Extract summary
        summary = "N/A"
        sum_match = re.search(r'\*\*Summary:\*\*\s*(.*?)(?=\n\s*\*\*|$)', ch_body, re.DOTALL)
        if sum_match:
            summary = sum_match.group(1).strip()
            
        # Extract beats
        beats = []
        beats_section = re.search(r'\*\*Beats:\*\*\s*(.*?)(?=\n\s*\*\*|$)', ch_body, re.DOTALL)
        if beats_section:
            beats = [re.sub(r'^\d+\.\s*', '', line).strip() for line in beats_section.group(1).split('\n') if line.strip()]
            
        # Extract plants
        plants = []
        plants_section = re.search(r'\*\*Plants:\*\*\s*(.*?)(?=\n\s*\*\*|$)', ch_body, re.DOTALL)
        if plants_section:
            plants = [re.sub(r'^-\s*', '', line).strip() for line in plants_section.group(1).split('\n') if line.strip()]
            
        # Extract harvests
        harvests = []
        harvests_section = re.search(r'\*\*Harvests:\*\*\s*(.*?)(?=\n\s*\*\*|$)', ch_body, re.DOTALL)
        if harvests_section:
            harvests = [re.sub(r'^-\s*', '', line).strip() for line in harvests_section.group(1).split('\n') if line.strip()]
            
        # Extract chapter question
        chapter_question = "N/A"
        cq_match = re.search(r'\*\*Chapter question:\*\*\s*(.*)$', ch_body, re.MULTILINE)
        if cq_match:
            chapter_question = cq_match.group(1).strip()
            
        entries.append({
            "num": ch_num,
            "title": title_line,
            "location": location,
            "characters": characters,
            "try_fail": try_fail,
            "emotional_arc": emotional_arc,
            "summary": summary,
            "beats": beats,
            "plants": plants,
            "harvests": harvests,
            "chapter_question": chapter_question
        })
        
    return entries

def run_continuity_validation(strict: bool = False, threshold: float = 7.5) -> dict:
    """Execute timeline and continuity check using LLM Judge."""
    print("=" * 60)
    print("GLOBAL TIMELINE AND CONTINUITY VALIDATION")
    print("=" * 60)
    
    # 1. Check/Rebuild outline.md
    if not OUTLINE_PATH.exists():
        print("[INFO] outline.md not found. Rebuilding from chapters first...")
        if BUILD_OUTLINE_PY.exists():
            subprocess.run(["uv", "run", "python", str(BUILD_OUTLINE_PY)], check=True)
        else:
            print("[ERROR] build_outline.py not found. Cannot proceed without outline.md.")
            sys.exit(1)
            
    chapters_data = parse_outline(OUTLINE_PATH)
    if not chapters_data:
        print("[ERROR] Failed to parse any chapters from outline.md.")
        sys.exit(1)
        
    print(f"[INFO] Successfully parsed {len(chapters_data)} chapters for timeline analysis.")
    
    # 2. Resolve list of judge models
    judge_models_str = os.environ.get("AUTOBOOK_JUDGE_MODEL", "openrouter/free")
    models_list = [m.strip() for m in judge_models_str.split(",") if m.strip()]
    if not models_list:
        models_list = ["openrouter/free"]

    result = None

    # 3. Call LLM Continuity Judge with 3 cycles and models loop
    system_prompt_full = (
        "Você é um Editor de Continuidade Literária de Elite, extremamente detalhista, clínico e frio. "
        "Sua única função é ler a sequência cronológica de capítulos (resumos, beats, personagens, locais, plants, harvests) de um romance e identificar "
        "erros de continuidade, loops temporais, repetições de debates/diálogos, inconsistências físicas e quebras de transição causal.\n\n"
        "Diretrizes Críticas de Análise:\n"
        "1. Repetição de Eventos/Loops Narrativos: Identifique se alguma conversa, descoberta de dados ou ação principal se repete "
        "no capítulo seguinte como se estivesse acontecendo pela primeira vez (ex: personagens discutindo a mesma falácia duas vezes, descobrindo o mesmo "
        "dado em momentos separados sem fazer referência ao evento anterior). Isso é uma inconsistência de alta gravidade (High Severity).\n"
        "2. Consistência Física e Espacial: Identifique se detalhes do mundo ou propriedades mudam inexplicavelmente (ex: apartamento no 3º andar em um capítulo e no 5º andar no outro; objetos mudando de lugar sem explicação).\n"
        "3. Linha do Tempo e Causalidade: Avalie se a transição cronológica de tempo (horas, dias, noites) e a relação de causa e efeito fazem sentido linear. A ação do fim do capítulo N deve se conectar logicamente à ação do início de N+1.\n"
        "4. Foreshadowing (Plants e Harvests): Aponte se há fios plantados que nunca foram colhidos ou colheitas que aparecem sem pistas anteriores.\n\n"
        "Você DEVE responder estritamente com um objeto JSON válido contendo exatamente este formato:\n"
        "{\n"
        "  \"continuity_score\": <nota de 0.0 a 10.0 representando a qualidade geral da consistência global. A nota deve ser baixa (ex: < 7.0) se houver repetições narrativas graves ou furos na linha do tempo>,\n"
        "  \"inconsistencies\": [\n"
        "    {\n"
        "      \"chapters\": [<lista de inteiros dos capítulos envolvidos, ex: [1, 2]>],\n"
        "      \"severity\": \"high\" | \"medium\" | \"low\",\n"
        "      \"issue_type\": \"event_repetition\" | \"setting_contradiction\" | \"timeline_break\" | \"causality_break\" | \"other\",\n"
        "      \"description\": \"Explicação cirúrgica e detalhada do problema de continuidade encontrado.\",\n"
        "      \"suggested_fix\": \"Como o escritor deve reestruturar, reescrever ou ajustar as cenas/capítulos para eliminar a inconsistência.\"\n"
        "    }\n"
        "  ],\n"
        "  \"timeline_flow\": \"Um breve diagnóstico (1-2 parágrafos) avaliando a fluidez temporal global, lógica e causalidade das transições entre os capítulos.\"\n"
        "}\n\n"
        "Responda APENAS com o JSON válido. Não inclua nenhuma explicação, comentário, introdução ou conclusão fora do JSON."
    )

    system_prompt_reduced = (
        "Você é um Editor de Continuidade Literária. Identifique inconsistências cronológicas e físicas e retorne este JSON:\n"
        "{\n"
        "  \"continuity_score\": <nota de 0.0 a 10.0>,\n"
        "  \"inconsistencies\": [\n"
        "    {\n"
        "      \"chapters\": [<lista de cap>],\n"
        "      \"severity\": \"high\" | \"medium\" | \"low\",\n"
        "      \"issue_type\": \"event_repetition\" | \"setting_contradiction\" | \"timeline_break\" | \"causality_break\" | \"other\",\n"
        "      \"description\": \"...\",\n"
        "      \"suggested_fix\": \"...\"\n"
        "    }\n"
        "  ],\n"
        "  \"timeline_flow\": \"...\"\n"
        "}"
    )

    system_prompt_minimal = (
        "Você é um Editor de Continuidade Literária. Verifique se há erros graves de cronologia ou furos na linha do tempo e responda APENAS com este JSON:\n"
        "{\n"
        "  \"continuity_score\": <nota de 0.0 a 10.0>,\n"
        "  \"inconsistencies\": []\n"
        "}"
    )

    for cycle in range(1, 4):
        print(f"[INFO] Beginning continuity validation Cycle {cycle}...", file=sys.stderr)
        
        # Prepare prompts
        if cycle == 1:
            sys_prompt = system_prompt_full
            chapters_json_str = json.dumps(chapters_data, indent=2, ensure_ascii=False)
        elif cycle == 2:
            sys_prompt = system_prompt_reduced
            chapters_json_str = json.dumps(get_reduced_chapters_data(chapters_data), indent=2, ensure_ascii=False)
        else:
            sys_prompt = system_prompt_minimal
            chapters_json_str = json.dumps(get_minimal_chapters_data(chapters_data), indent=2, ensure_ascii=False)

        user_prompt = (
            f"Abaixo está a sequência dos capítulos do livro em formato JSON estruturado:\n\n"
            f"{chapters_json_str}\n\n"
            f"Analise toda a linha do tempo e forneça o relatório no formato JSON exigido."
        )

        for model in models_list:
            print(f"[INFO] Trying model '{model}' in continuity Cycle {cycle}...", file=sys.stderr)
            try:
                raw_response = call_llm(prompt=user_prompt, system_prompt=sys_prompt, temperature=0.1, is_judge=True, override_model=model)
                parsed = validate_and_repair_json(raw_response, "continuity_score")
                if parsed is not None:
                    print(f"[INFO] Successfully obtained valid continuity check from model '{model}' (Cycle {cycle})!", file=sys.stderr)
                    result = parsed
                    break
            except Exception as e:
                print(f"WARNING: Continuity check failed for model '{model}' in Cycle {cycle}: {e}", file=sys.stderr)
            
            # Immediately rotate: no sleep
            print(f"[INFO] Model '{model}' failed or returned invalid JSON. Rotating to next model...", file=sys.stderr)

        if result is not None:
            break

    if result is None:
        print("[ERROR] All continuity evaluation cycles and models failed. Falling back to default baseline report.", file=sys.stderr)
        result = {
            "continuity_score": 5.0,
            "inconsistencies": [
                {
                    "chapters": [],
                    "severity": "high",
                    "issue_type": "other",
                    "description": "Falha na execução/parsing de todas as tentativas e modelos de verificação de continuidade.",
                    "suggested_fix": "Verifique a conectividade e os logs de API de todos os modelos."
                }
            ],
            "timeline_flow": "Impossível analisar devido a falhas persistentes de execução da API ou de processamento de JSON."
        }
        
    score = result.get("continuity_score", 0.0)
    inconsistencies = result.get("inconsistencies", [])
    flow_desc = result.get("timeline_flow", "")
    
    # 4. Save result logs
    EVAL_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = EVAL_LOGS_DIR / "continuity_report.json"
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    
    print("\n" + "-"*60)
    print(f"CONTINUITY SCORE: {score:.1f}/10.0")
    try:
        report_display_path = report_path.relative_to(BASE_DIR)
    except ValueError:
        report_display_path = report_path
    print(f"Report saved to: {report_display_path}")
    print("-"*60)
    print(f"\nTimeline Flow Diagnosis:\n{flow_desc}\n")
    
    if inconsistencies:
        print(f"Found {len(inconsistencies)} issues:")
        for idx, inc in enumerate(inconsistencies):
            ch_str = ", ".join(f"Ch {c:02d}" for c in inc.get("chapters", []))
            severity = inc.get("severity", "unknown").upper()
            type_str = inc.get("issue_type", "other").upper()
            print(f"\n[{idx+1}] {severity} Severity — {type_str} (Chapters: {ch_str})")
            print(f"    Description: {inc.get('description', '')}")
            print(f"    Suggested Fix: {inc.get('suggested_fix', '')}")
    else:
        print("No continuity or timeline issues detected!")
        
    print("=" * 60)
    
    # 5. Handle strict mode exiting
    if strict and score < threshold:
        print(f"\n[CRITICAL ERROR] Continuity score {score:.1f} is below the threshold of {threshold:.1f}.")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify global novel timeline and continuity.")
    parser.add_argument(
        "-s", "--strict",
        action="store_true",
        help="Exit with code 1 if continuity score is below threshold."
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=7.5,
        help="Strict mode score threshold (default: 7.5)."
    )
    args = parser.parse_args()
    
    run_continuity_validation(strict=args.strict, threshold=args.threshold)
