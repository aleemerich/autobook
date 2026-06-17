import glob
import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CHAPTERS_DIR = BASE_DIR / "chapters"


def load_file(path):
    """Load a text file, return empty string if missing."""
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return ""


def load_layer_files(base_dir: Path | None = None):
    """Load all planning layer files."""
    if base_dir is None:
        base_dir = BASE_DIR
    book_data_dir = base_dir / "book_data"
    return {
        "voice": load_file(book_data_dir / "voice.md"),
        "world": load_file(book_data_dir / "world.md"),
        "characters": load_file(book_data_dir / "characters.md"),
        "outline": load_file(book_data_dir / "outline.md"),
        "canon": load_file(book_data_dir / "canon.md"),
    }


def load_chapter(n, chapters_dir: Path | None = None):
    """Load a single chapter file."""
    if chapters_dir is None:
        chapters_dir = CHAPTERS_DIR
    return load_file(chapters_dir / f"ch_{n:02d}.md")


def load_all_chapters(chapters_dir: Path | None = None):
    """Load all chapter files in order."""
    if chapters_dir is None:
        chapters_dir = CHAPTERS_DIR
    chapters = {}
    for f in sorted(glob.glob(str(chapters_dir / "ch_*.md"))):
        num = int(re.search(r'ch_(\d+)', f).group(1))
        chapters[num] = Path(f).read_text()
    return chapters
