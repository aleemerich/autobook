from pathlib import Path

def load_text_file(path: Path) -> str:
    """Retorna conteudo UTF-8 do arquivo ou string vazia se nao existir."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def extract_voice_part2(voice_text: str) -> str:
    """Retorna a segunda parte do texto de voice.md ou fallback do texto completo."""
    if not voice_text:
        return ""
    lines = voice_text.split('\n')
    try:
        part2_start = next(i for i, l in enumerate(lines) if 'Part 2' in l)
        return '\n'.join(lines[part2_start:])
    except StopIteration:
        return voice_text

def build_foundation_writing_state() -> dict:
    """Retorna o estado inicial de escrita apos a fundacao."""
    return {"chapters_drafted": 0, "phase": "writing", "current_focus": "chapters"}

def foundation_git_paths(include_mystery: bool) -> list[str]:
    """Retorna os paths relativos dos artefatos estruturais para git add."""
    paths = [
        "seed.txt",
        "book_data/world.md",
        "book_data/characters.md",
        "book_data/outline.md",
        "book_data/canon.md",
    ]
    if include_mystery:
        paths.append("book_data/MYSTERY.md")
    return paths
