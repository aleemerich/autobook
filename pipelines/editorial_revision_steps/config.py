import json


def load_editorial_config() -> dict:
    """Carrega a configuracao editorial com base no idioma ativo."""
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
    """Calcula a temperatura de retentativa com base no indice do retry."""
    try:
        config = load_editorial_config()
        temp_map = config.get("retry_temp_map", {})
        return float(temp_map.get(str(retry_idx), 0.8))
    except Exception:
        temp_map = {1: 0.6, 2: 0.6, 3: 0.7, 4: 0.9, 5: 0.5}
        return temp_map.get(retry_idx, 0.8)
