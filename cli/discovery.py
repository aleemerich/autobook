from dataclasses import dataclass
from pathlib import Path
import re
from typing import List, Dict

from workspace.branching import current_branch
from pipelines.registry import list_pipelines

@dataclass
class ProjectState:
    current_branch: str
    pipelines: List[str]
    available_languages: List[str]
    available_genres: Dict[str, List[str]]
    has_seed: bool
    book_data_files: List[str]
    foundation_complete: bool
    chapter_numbers: List[int]
    logs_present: List[str]
    production_artifacts_present: List[str]
    recommended_next_steps: List[str]

def discover_project_state(base_dir: Path | None = None) -> ProjectState:
    """Inspeciona o repositório em modo somente-leitura e retorna o estado consolidado da obra."""
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.resolve()

    # 1. Branch atual
    try:
        branch = current_branch()
    except Exception:
        branch = "unknown"

    # 2. Pipelines registrados
    try:
        pipelines = list(list_pipelines().keys())
    except Exception:
        pipelines = []

    # 3. Idiomas (subdiretórios de prompts/)
    available_languages = []
    prompts_dir = base_dir / "prompts"
    if prompts_dir.exists() and prompts_dir.is_dir():
        for item in prompts_dir.iterdir():
            if item.is_dir():
                available_languages.append(item.name)
    available_languages.sort()

    # 4. Gêneros (subdiretórios de genres/ e seus respectivos arquivos txt)
    available_genres = {}
    genres_dir = base_dir / "genres"
    if genres_dir.exists() and genres_dir.is_dir():
        for lang_dir in genres_dir.iterdir():
            if lang_dir.is_dir():
                genres = []
                for f in lang_dir.glob("*.txt"):
                    genres.append(f.stem)
                genres.sort()
                available_genres[lang_dir.name] = genres

    # 5. Semente (seed.txt)
    seed_file = base_dir / "seed.txt"
    has_seed = seed_file.exists() and seed_file.is_file()

    # 6. Arquivos em book_data/ e completude da fundação
    book_data_files = []
    book_data_dir = base_dir / "book_data"
    foundation_files = {"world.md", "characters.md", "outline.md", "canon.md"}
    present_foundation = set()

    if book_data_dir.exists() and book_data_dir.is_dir():
        for item in book_data_dir.iterdir():
            if item.is_file() and not item.name.startswith("."):
                book_data_files.append(item.name)
                if item.name in foundation_files:
                    present_foundation.add(item.name)
    book_data_files.sort()
    foundation_complete = (foundation_files == present_foundation)

    # 7. Capítulos (chapters/ch_*.md)
    chapter_numbers = []
    chapters_dir = base_dir / "chapters"
    if chapters_dir.exists() and chapters_dir.is_dir():
        for f in chapters_dir.glob("ch_*.md"):
            m = re.match(r"ch_(\d+)\.md", f.name)
            if m:
                chapter_numbers.append(int(m.group(1)))
    chapter_numbers.sort()

    # 8. Logs
    logs_present = []
    logs_dir = base_dir / "logs"
    if logs_dir.exists() and logs_dir.is_dir():
        for f in logs_dir.iterdir():
            if f.is_file():
                logs_present.append(f.name)
    logs_present.sort()

    # 9. Artefatos de Produção (book_data/production/)
    production_artifacts_present = []
    prod_dir = book_data_dir / "production"
    if prod_dir.exists() and prod_dir.is_dir():
        for f in prod_dir.iterdir():
            if f.is_file():
                production_artifacts_present.append(f.name)
    production_artifacts_present.sort()

    # 10. Recomendações de próximos passos
    recommended_next_steps = []
    if not has_seed:
        recommended_next_steps.append("ideation")
    elif not foundation_complete:
        recommended_next_steps.append("foundation")
    else:
        if len(production_artifacts_present) == 0:
            recommended_next_steps.append("production_planning (roadmap/ausente)")
        recommended_next_steps.append("book_generation")
        if len(chapter_numbers) > 0:
            recommended_next_steps.append("editorial_revision")
            recommended_next_steps.append("verify_continuity")

    return ProjectState(
        current_branch=branch,
        pipelines=pipelines,
        available_languages=available_languages,
        available_genres=available_genres,
        has_seed=has_seed,
        book_data_files=book_data_files,
        foundation_complete=foundation_complete,
        chapter_numbers=chapter_numbers,
        logs_present=logs_present,
        production_artifacts_present=production_artifacts_present,
        recommended_next_steps=recommended_next_steps,
    )
