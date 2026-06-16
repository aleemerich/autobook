from dataclasses import dataclass
from typing import Callable, Dict

from pipelines.base import Pipeline
from pipelines.book_generation import BookGenerationPipeline
from pipelines.editorial_revision import EditorialRevisionPipeline
from pipelines.ideation import IdeationPipeline
from pipelines.foundation import FoundationPipeline

@dataclass(frozen=True)
class PipelineSpec:
    name: str
    description: str
    factory: Callable[[], Pipeline]
    supports_chapter: bool
    supports_from_scratch: bool

_REGISTRY: Dict[str, PipelineSpec] = {
    "ideation": PipelineSpec(
        name="ideation",
        description="Cria ou preserva o arquivo seed e inicializa o estado do livro.",
        factory=IdeationPipeline,
        supports_chapter=False,
        supports_from_scratch=True,
    ),
    "foundation": PipelineSpec(
        name="foundation",
        description="Gera os documentos de fundação do livro.",
        factory=FoundationPipeline,
        supports_chapter=False,
        supports_from_scratch=True,
    ),
    "book_generation": PipelineSpec(
        name="book_generation",
        description="Gera capítulos, avalia a qualidade e valida continuidade.",
        factory=BookGenerationPipeline,
        supports_chapter=True,
        supports_from_scratch=True,
    ),
    "editorial_revision": PipelineSpec(
        name="editorial_revision",
        description="Aplica revisão editorial e reescreve capítulos do livro.",
        factory=EditorialRevisionPipeline,
        supports_chapter=True,
        supports_from_scratch=False,
    ),
}

def list_pipelines() -> Dict[str, PipelineSpec]:
    """Retorna um dicionário contendo as especificações das pipelines registradas."""
    return _REGISTRY.copy()

def get_pipeline_spec(name: str) -> PipelineSpec:
    """Retorna a especificação de uma pipeline pelo nome. Levanta KeyError se não existir."""
    if name not in _REGISTRY:
        raise KeyError(f"Pipeline desconhecida: '{name}'")
    return _REGISTRY[name]

def get_pipeline(name: str) -> Pipeline:
    """Instancia e retorna a pipeline correspondente ao nome. Levanta KeyError se não existir."""
    spec = get_pipeline_spec(name)
    return spec.factory()
