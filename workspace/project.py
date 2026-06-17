import datetime
import json
from pathlib import Path
from typing import Any, Dict

def workspace_metadata_path(base_dir: Path | None = None) -> Path:
    """
    Retorna o caminho do arquivo 'workspace.json' dentro da pasta 'book_data'.
    Se base_dir for None, resolve a partir da raiz do projeto.
    """
    if base_dir is None:
        base_dir = Path(__file__).parent.parent.resolve()
    return base_dir / "book_data" / "workspace.json"

def build_workspace_metadata(title: str, branch: str) -> Dict[str, Any]:
    """
    Gera um dicionário serializável com os metadados do workspace.
    Levanta ValueError caso o título ou a branch estejam vazios.
    """
    if not title or not title.strip():
        raise ValueError("O título da obra não pode ser vazio.")
    if not branch or not branch.strip():
        raise ValueError("A branch do projeto não pode ser vazia.")
    from workspace.branching import is_book_branch
    if not is_book_branch(branch.strip()):
        raise ValueError("A branch do projeto deve seguir o formato autobook/<slug>.")

    return {
        "title": title.strip(),
        "branch": branch.strip(),
        "created_at": datetime.datetime.now().isoformat(),
        "schema_version": 1
    }

def validate_workspace_metadata(data: Any) -> Dict[str, Any]:
    """
    Valida a estrutura dos metadados de workspace.
    Retorna o dicionário validado.
    Levanta ValueError se a estrutura ou tipos não estiverem corretos.
    """
    if not isinstance(data, dict):
        raise ValueError("Os metadados do workspace devem ser um objeto JSON (dicionário).")

    # Verificar schema_version
    if "schema_version" not in data:
        raise ValueError("O campo 'schema_version' é obrigatório nos metadados do workspace.")
    if data["schema_version"] != 1:
        raise ValueError(f"Versão de schema '{data['schema_version']}' não suportada. Esperado: 1.")

    # Verificar title
    if "title" not in data:
        raise ValueError("O campo 'title' é obrigatório nos metadados do workspace.")
    if not isinstance(data["title"], str) or not data["title"].strip():
        raise ValueError("O campo 'title' deve ser uma string não vazia.")

    # Verificar branch
    if "branch" not in data:
        raise ValueError("O campo 'branch' é obrigatório nos metadados do workspace.")
    if not isinstance(data["branch"], str) or not data["branch"].strip():
        raise ValueError("O campo 'branch' deve ser uma string não vazia.")
    from workspace.branching import is_book_branch
    if not is_book_branch(data["branch"].strip()):
        raise ValueError("O campo 'branch' deve seguir o formato autobook/<slug>.")

    # Verificar created_at
    if "created_at" not in data:
        raise ValueError("O campo 'created_at' é obrigatório nos metadados do workspace.")
    if not isinstance(data["created_at"], str) or not data["created_at"].strip():
        raise ValueError("O campo 'created_at' deve ser uma string não vazia.")
    try:
        datetime.datetime.fromisoformat(data["created_at"])
    except ValueError as e:
        raise ValueError("O campo 'created_at' deve estar em formato ISO 8601 válido.") from e

    return data

def write_workspace_metadata(title: str, branch: str, base_dir: Path | None = None) -> Path:
    """
    Cria a pasta 'book_data' caso necessário e escreve o arquivo de metadados.
    Retorna o caminho do arquivo escrito.
    """
    path = workspace_metadata_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = build_workspace_metadata(title, branch)
    validate_workspace_metadata(data)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return path

def load_workspace_metadata(base_dir: Path | None = None) -> Dict[str, Any] | None:
    """
    Carrega e parseia os metadados do workspace se existirem.
    Retorna None se o arquivo não existir.
    Levanta ValueError se o JSON for inválido ou se a estrutura de metadados for inválida.
    """
    path = workspace_metadata_path(base_dir)
    if not path.exists() or not path.is_file():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"O arquivo de metadados do workspace contém JSON inválido: {e}")

    return validate_workspace_metadata(data)
