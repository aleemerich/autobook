import sys
import re
import json
from pathlib import Path
from llm import call_llm

BASE_DIR = Path(__file__).parent.parent.parent.resolve()
BOOK_DATA_DIR = BASE_DIR / "book_data"
EDITORIAL_MD = BOOK_DATA_DIR / "editorial.md"

def load_editorial_markdown_fallback(text: str) -> dict:
    """Fallback parser usando regex para quando a API do LLM estiver indisponivel."""
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
    """Analisa o editorial.md centralizado usando extrator semantico do LLM com fallback regex."""
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
