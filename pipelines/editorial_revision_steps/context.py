import re
from pathlib import Path

def parse_chapter_number(path: Path) -> int | None:
    """Para arquivo ch_XX.md, retorna XX como int. Retorna None para nomes invalidos."""
    name = path.name
    match = re.match(r"^ch_(\d+)\.md$", name)
    if match:
        return int(match.group(1))
    return None

def list_chapter_files(chapters_dir: Path) -> list[Path]:
    """Lista arquivos ch_*.md validos ordenados pelo numero do capitulo."""
    if not chapters_dir.exists():
        return []
    files = []
    for p in chapters_dir.glob("ch_*.md"):
        if parse_chapter_number(p) is not None:
            files.append(p)
    return sorted(files, key=parse_chapter_number)

def filter_chapter_files(chapter_files: list[Path], selected_chapters: list[int] | None) -> list[Path]:
    """Filtra a lista de arquivos de capitulos mantendo apenas os presentes em selected_chapters."""
    if not selected_chapters:
        return chapter_files
    selected_set = set(selected_chapters)
    return [f for f in chapter_files if parse_chapter_number(f) in selected_set]

def load_chapter_text(path: Path) -> str:
    """Le o texto do arquivo de capitulo em UTF-8."""
    return path.read_text(encoding="utf-8")
