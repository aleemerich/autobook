import json
import pytest
from pathlib import Path

from workspace.project import (
    workspace_metadata_path,
    build_workspace_metadata,
    write_workspace_metadata,
    load_workspace_metadata,
    validate_workspace_metadata
)

def test_workspace_metadata_path(tmp_path: Path) -> None:
    """Valida que o caminho retornado aponta corretamente para book_data/workspace.json."""
    # Teste com diretório temporário passado como base
    path = workspace_metadata_path(tmp_path)
    assert path == tmp_path / "book_data" / "workspace.json"
    
    # Teste com base_dir = None (deve resolver caminho na raiz do projeto)
    path_default = workspace_metadata_path(None)
    assert path_default.name == "workspace.json"
    assert path_default.parent.name == "book_data"

def test_build_workspace_metadata() -> None:
    """Valida a construção correta de metadados e integridade dos campos."""
    metadata = build_workspace_metadata("O Hobbit", "autobook/o-hobbit")
    
    assert metadata["title"] == "O Hobbit"
    assert metadata["branch"] == "autobook/o-hobbit"
    assert metadata["schema_version"] == 1
    assert "created_at" in metadata

def test_build_workspace_metadata_validation() -> None:
    """Valida que campos vazios são rejeitados com ValueError."""
    # Título vazio
    with pytest.raises(ValueError) as excinfo:
        build_workspace_metadata("", "autobook/some-branch")
    assert "título da obra não pode ser vazio" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        build_workspace_metadata("   ", "autobook/some-branch")
    assert "título da obra não pode ser vazio" in str(excinfo.value)

    # Branch vazia
    with pytest.raises(ValueError) as excinfo:
        build_workspace_metadata("O Hobbit", "")
    assert "branch do projeto não pode ser vazia" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        build_workspace_metadata("O Hobbit", "  ")
    assert "branch do projeto não pode ser vazia" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        build_workspace_metadata("O Hobbit", "feature/hobbit")
    assert "formato autobook/<slug>" in str(excinfo.value)

def test_write_workspace_metadata(tmp_path: Path) -> None:
    """Valida que write_workspace_metadata cria a pasta book_data e grava JSON válido."""
    written_path = write_workspace_metadata("Silmarillion", "autobook/silmarillion", base_dir=tmp_path)
    
    assert written_path.exists()
    assert written_path.is_file()
    
    # Valida conteúdo escrito
    with open(written_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["title"] == "Silmarillion"
    assert data["branch"] == "autobook/silmarillion"
    assert data["schema_version"] == 1
    assert "created_at" in data

def test_load_workspace_metadata(tmp_path: Path) -> None:
    """Valida o carregamento correto de metadados sob diferentes estados do arquivo."""
    # 1. Arquivo ausente (deve retornar None)
    assert load_workspace_metadata(tmp_path) is None

    # 2. Arquivo válido
    write_workspace_metadata("Silmarillion", "autobook/silmarillion", base_dir=tmp_path)
    metadata = load_workspace_metadata(tmp_path)
    assert metadata is not None
    assert metadata["title"] == "Silmarillion"
    assert metadata["branch"] == "autobook/silmarillion"

    # 3. Arquivo contendo JSON inválido (deve lançar ValueError)
    path = workspace_metadata_path(tmp_path)
    with open(path, "w", encoding="utf-8") as f:
        f.write("{invalid_json}")
        
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "contém JSON inválido" in str(excinfo.value)

def test_load_workspace_metadata_validation_scenarios(tmp_path: Path) -> None:
    """Valida que load_workspace_metadata levanta ValueError para diversas estruturas inválidas."""
    path = workspace_metadata_path(tmp_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 1. JSON contendo array/lista
    with open(path, "w", encoding="utf-8") as f:
        json.dump([1, 2, 3], f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "objeto JSON (dicionário)" in str(excinfo.value)

    # 2. schema_version ausente
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"title": "Hobbit", "branch": "autobook/hobbit", "created_at": "2026-01-01T00:00:00"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "schema_version" in str(excinfo.value)

    # 3. schema_version diferente de 1
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 2, "title": "Hobbit", "branch": "autobook/hobbit", "created_at": "2026-01-01T00:00:00"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "Versão de schema '2' não suportada" in str(excinfo.value)

    # 4. title ausente ou vazio
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "branch": "autobook/hobbit", "created_at": "2026-01-01T00:00:00"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "campo 'title' é obrigatório" in str(excinfo.value)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "title": "  ", "branch": "autobook/hobbit", "created_at": "2026-01-01T00:00:00"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "string não vazia" in str(excinfo.value)

    # 5. branch ausente ou vazia
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "title": "Hobbit", "created_at": "now"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "campo 'branch' é obrigatório" in str(excinfo.value)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "title": "Hobbit", "branch": "feature/hobbit", "created_at": "2026-01-01T00:00:00"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "formato autobook/<slug>" in str(excinfo.value)

    # 6. created_at ausente, vazia ou inválida
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "title": "Hobbit", "branch": "autobook/hobbit"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "campo 'created_at' é obrigatório" in str(excinfo.value)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "title": "Hobbit", "branch": "autobook/hobbit", "created_at": "  "}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "string não vazia" in str(excinfo.value)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "title": "Hobbit", "branch": "autobook/hobbit", "created_at": "not-a-date"}, f)
    with pytest.raises(ValueError) as excinfo:
        load_workspace_metadata(tmp_path)
    assert "ISO 8601" in str(excinfo.value)
