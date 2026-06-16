import json
import subprocess
from pathlib import Path
from pipelines.foundation_steps.context import (
    build_foundation_writing_state,
    foundation_git_paths
)

def write_foundation_state(state_file: Path) -> None:
    """Escreve o estado inicial de escrita em state.json."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state = build_foundation_writing_state()
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

def commit_foundation_artifacts(base_dir: Path, include_mystery: bool) -> None:
    """Executa git add e git commit para os arquivos de fundacao."""
    for path in foundation_git_paths(include_mystery):
        subprocess.run(["git", "add", path], cwd=str(base_dir), check=True)
        
    subprocess.run(
        ["git", "commit", "-m", "planning: initialize foundational story bibles and outline"],
        cwd=str(base_dir),
        check=True
    )
