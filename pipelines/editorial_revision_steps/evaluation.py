import json
from pathlib import Path

def load_evaluation_json(path: Path) -> dict:
    """Le um arquivo JSON contendo a avaliacao do capitulo."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

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
