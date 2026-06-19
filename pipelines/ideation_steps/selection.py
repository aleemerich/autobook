import re

def parse_numbered_concepts(concepts_text: str) -> dict[str, str]:
    """Extrai conceitos numerados em texto simples ou headings Markdown."""
    if not concepts_text:
        return {}
    parts = re.split(r'^\s*(?:#{1,6}\s*)?(\d+)[\.\)]\s+', concepts_text, flags=re.MULTILINE)
    concepts = {}
    if len(parts) <= 1:
        return {}
    for idx in range(1, len(parts), 2):
        num = parts[idx]
        text = parts[idx+1] if idx + 1 < len(parts) else ""
        concepts[num] = f"{num}. {text.strip()}"
    return concepts

def select_concept_text(concepts_text: str, choice: str) -> str:
    """Usa parse_numbered_concepts e retorna o conceito escolhido, ou fallback para o texto completo."""
    concepts = parse_numbered_concepts(concepts_text)
    if choice in concepts:
        return concepts[choice]
    return concepts_text

def default_mystery_template() -> str:
    """Retorna o template padrao de misterio central."""
    return (
        "# THE CENTRAL MYSTERY\n"
        "### Author's Eyes Only — Not for AI agent context during drafting\n\n"
        "---\n\n"
        "<!-- Define the central secret... -->\n"
    )

def build_initial_ideation_state() -> dict:
    """Retorna o estado inicial consolidado do livro."""
    return {"chapters_drafted": 0, "phase": "foundation", "current_focus": "planning"}
