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
        part2_start = next(i for i, line in enumerate(lines) if 'Part 2' in line)
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

def load_seed_and_voice(seed_path: Path, voice_path: Path) -> dict:
    """Carrega os insumos de seed e voice."""
    voice_content = load_text_file(voice_path)
    return {
        "seed": load_text_file(seed_path),
        "voice": voice_content,
        "voice_part2": extract_voice_part2(voice_content)
    }

def load_world_inputs(seed_path: Path, voice_path: Path) -> dict:
    """Carrega os insumos necessarios para a geracao do world.md."""
    return load_seed_and_voice(seed_path, voice_path)

def load_characters_inputs(seed_path: Path, world_path: Path, voice_path: Path) -> dict:
    """Carrega os insumos necessarios para a geracao do characters.md."""
    inputs = load_seed_and_voice(seed_path, voice_path)
    inputs["world"] = load_text_file(world_path)
    return inputs

def load_outline_inputs(
    seed_path: Path,
    world_path: Path,
    characters_path: Path,
    mystery_path: Path,
    craft_path: Path,
    voice_path: Path
) -> dict:
    """Carrega os insumos necessarios para a geracao do outline.md."""
    if not craft_path.exists():
        raise FileNotFoundError(f"[Foundation] CRAFT.md não encontrado no caminho especificado: {craft_path}")
    inputs = load_seed_and_voice(seed_path, voice_path)
    inputs["world"] = load_text_file(world_path)
    inputs["characters"] = load_text_file(characters_path)
    inputs["mystery"] = load_text_file(mystery_path)
    inputs["craft"] = load_text_file(craft_path)
    return inputs

def load_canon_inputs(seed_path: Path, world_path: Path, characters_path: Path) -> dict:
    """Carrega os insumos necessarios para a geracao do canon.md."""
    return {
        "seed": load_text_file(seed_path),
        "world": load_text_file(world_path),
        "characters": load_text_file(characters_path)
    }
