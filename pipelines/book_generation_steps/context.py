import json
import re
from pathlib import Path
from typing import Dict, Any, List

def load_state(book_data_dir: Path) -> Dict[str, Any]:
    """Carrega o arquivo state.json ou retorna um dict com chapters_drafted inicializado se ausente."""
    state_file = book_data_dir / "state.json"
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    if not isinstance(state, dict):
        state = {}

    if "chapters_drafted" not in state:
        state["chapters_drafted"] = 0
    return state

def load_outline(book_data_dir: Path) -> str:
    """Lê o arquivo outline.md ou levanta FileNotFoundError."""
    outline_file = book_data_dir / "outline.md"
    if not outline_file.exists():
        raise FileNotFoundError(f"Outline file outline.md not found in {book_data_dir}")
    return outline_file.read_text(encoding="utf-8")

def count_total_chapters(outline_text: str) -> int:
    """Conta o total de capítulos a partir do texto do outline."""
    chapters_found = re.findall(r'^###\s*Ch(?:apter)?\s*(\d+)\b', outline_text, re.MULTILINE | re.IGNORECASE)
    return len(chapters_found) if chapters_found else 22

def extract_chapter_outline(outline_text: str, ch: int) -> str:
    """Extrai a seção do outline correspondente ao capítulo atual."""
    pattern = rf'###\s*Ch(?:apter)?\s*{ch}\b.*?(?=###\s*Ch(?:apter)?\s*{ch + 1}\b|## Act|## Foreshadowing|$)'
    ch_outline_match = re.search(pattern, outline_text, re.DOTALL | re.IGNORECASE)
    return ch_outline_match.group(0).strip() if ch_outline_match else f"Capítulo {ch}"

def extract_chapter_title(ch_outline: str, ch: int) -> str:
    """Extrai o título do capítulo atual a partir da seção do outline do capítulo."""
    title_match = re.search(r'###\s*Ch(?:apter)?\s*\d+:\s*(.*?)$', ch_outline, re.MULTILINE)
    return title_match.group(1).strip() if title_match else f"Capítulo {ch}"

def extract_next_chapter_outline(outline_text: str, ch: int) -> str:
    """Extrai a seção do outline correspondente ao próximo capítulo."""
    next_pattern = rf'###\s*Ch(?:apter)?\s*{ch + 1}\b.*?(?=###\s*Ch(?:apter)?\s*{ch + 2}\b|## Act|## Foreshadowing|$)'
    next_match = re.search(next_pattern, outline_text, re.DOTALL | re.IGNORECASE)
    return next_match.group(0).strip() if next_match else "(Fim do romance)"

def extract_chapter_beats(ch_outline: str) -> List[str]:
    """Parseia e extrai a lista de beats de um capítulo a partir de sua seção do outline."""
    beats_section = re.search(r'\*\*Beats:\*\*\s*(.*?)(?=\n\s*\*\*|$)', ch_outline, re.DOTALL | re.IGNORECASE)
    beats = []
    if beats_section:
        for line in beats_section.group(1).split('\n'):
            line = line.strip()
            if line:
                clean_beat = re.sub(r'^\d+\.\s*|-\s*', '', line).strip()
                if clean_beat:
                    beats.append(clean_beat)
    return beats

def load_previous_chapter_tail(chapters_dir: Path, ch: int) -> str:
    """Carrega a cauda do capítulo anterior (limite de 1000 palavras) para gancho de transição."""
    prev_path = chapters_dir / f"ch_{ch - 1:02d}.md"
    if prev_path.exists():
        prev_text = prev_path.read_text(encoding="utf-8").strip()
        prev_words = prev_text.split()
        prev_tail_words = prev_words[-1000:] if len(prev_words) > 1000 else prev_words
        return " ".join(prev_tail_words)
    else:
        return "(Este é o primeiro capítulo do livro, não há contexto anterior)"

def load_lore_files(book_data_dir: Path) -> Dict[str, str]:
    """Carrega os arquivos world.md, canon.md, characters.md e voice.md."""
    world_text = (book_data_dir / "world.md").read_text(encoding="utf-8") if (book_data_dir / "world.md").exists() else ""
    canon_text = (book_data_dir / "canon.md").read_text(encoding="utf-8") if (book_data_dir / "canon.md").exists() else ""
    characters_text = (book_data_dir / "characters.md").read_text(encoding="utf-8") if (book_data_dir / "characters.md").exists() else ""
    voice_text = (book_data_dir / "voice.md").read_text(encoding="utf-8") if (book_data_dir / "voice.md").exists() else ""
    return {
        "world": world_text,
        "canon": canon_text,
        "characters": characters_text,
        "voice": voice_text
    }

def build_lore_data(world_text: str, canon_text: str, characters_text: str) -> str:
    """Monta a string unificada de lore_data no formato atual."""
    return f"=== WORLD BIBLE ===\n{world_text}\n\n=== ESTABLISHED CANON ===\n{canon_text}\n\n=== CHARACTER REGISTRY ===\n{characters_text}"
