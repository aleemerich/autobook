# 02 - Pipeline Contract, Registry and Discovery Spec

## Objetivo
Especificar a evolução dos contratos de execução do Autobook, introduzindo metadados opcionais para passos e pipelines, um registro dinâmico centralizado (`pipelines/registry.py`) e uma ferramenta de descoberta do estado do projeto (`cli/discovery.py`).

## Fora De Escopo
- Adicionar validações estáticas ou verificações obrigatórias de execução com base em dependências declaradas (`requires` e `produces`) nesta fase.
- Alterar a lógica interna dos passos concretos atuais ou a maneira como eles gravam dados no filesystem.

## Estado Atual
- **Step e Pipeline:** Definidos em `pipelines/base.py` de forma simples, sem metadados declarativos adicionais de inputs e outputs. O construtor do `Step` aceita apenas `name`.
- **Registry:** Não existe. As pipelines concretas (`IdeationPipeline`, `FoundationPipeline`, etc.) são importadas estaticamente na parte superior do arquivo `run.py`.
- **Discovery:** Não há nenhum mecanismo centralizado que inspecione o diretório do projeto e determine dinamicamente o status (quais capítulos existem, se há seed.txt, etc.) para servir como inteligência ao wizard.

## Comportamento Desejado
- **Contrato Estendido (Fase 1):** `Step` e `Pipeline` aceitam metadados opcionais em seus construtores:
  - `name: str` (obrigatório)
  - `description: str | None = None`
  - `requires: list[str] | None = None` (lista de dependências de entrada)
  - `produces: list[str] | None = None` (lista de artefatos de saída)
  - *Nota:* Para evitar efeitos colaterais de listas mutáveis no construtor Python, usar `None` como padrão e instanciar as listas internamente.
- **Registro Centralizado (Fase 2):** Criar `pipelines/registry.py` provendo:
  - `list_pipelines() -> dict[str, PipelineSpec]`
  - `get_pipeline(name: str) -> Pipeline`
  - `get_pipeline_spec(name: str) -> PipelineSpec`
  - `PipelineSpec` (dataclass contendo: `name`, `description`, `factory` (callable), `supports_chapter: bool`, `supports_from_scratch: bool`).
- **Descoberta do Estado (Fase 5):** Criar `cli/discovery.py` com `discover_project_state(base_dir: Path | None = None) -> ProjectState` retornando informações como a branch ativa, idiomas disponíveis em `prompts/`, gêneros disponíveis em `genres/`, capítulos gerados e arquivos de `book_data/` presentes.

## Decisão de Validação de Dependências
Por decisão do supervisor, **os metadados `requires` e `produces` não serão validados ou lincados de forma restritiva ou obrigatória** nas pipelines concretas durante as Fases 1 a 5. A utilidade desse mapeamento e o design de um linter ou mecanismo de orquestração automático baseado em grafos de dependência serão julgados no Gate A pelo supervisor.

## Arquivos Afetados Futuramente
- `pipelines/base.py`
- [NEW] `pipelines/registry.py`
- [NEW] `cli/discovery.py`
- `run.py`
- [NEW] `tests/test_pipeline_base.py`
- [NEW] `tests/test_pipeline_registry.py`
- [NEW] `tests/test_cli_discovery.py`

## Contratos De Entrada
- Instanciação de `Step` e `Pipeline` aceitando metadados adicionais.
- O método `discover_project_state` aceita um `base_dir: Path` opcional para facilitação de testes com diretórios temporários (`tmp_path`).

## Contratos De Saida
- Estruturas de dados dataclass/dicionário para o Registry e Discovery.

## Testes Necessarios
1. **Pipelines Base:** Validar que `Step("nome")` permanece compatível e que `Step("nome", requires=["a"], produces=["b"])` preserva metadados sem erros.
2. **Registry:** Garantir que chamar `list_pipelines()` não instancia nem executa as pipelines concretas (deve retornar apenas as definições estáticas). Validar o retorno correto de `get_pipeline()` e o tratamento de erro em entradas desconhecidas.
3. **Discovery:** Usar o utilitário `tmp_path` do pytest nos testes para criar estados simulados e validar o correto mapeamento do estado do projeto (presença de seed, capítulos, gêneros, idiomas).

## Criterios De Aceite
- Sem alterações ou quebras nas execuções de pipelines existentes no repositório.
- A suite de testes modernos (`tests/`) passa inteiramente.
- Sem chamadas a LLMs durante a execução do Registry ou do Discovery.

## Perguntas Abertas
- Como organizar a taxonomia de strings para a lista de `requires` e `produces` (ex: `"seed.txt"`, `"book_data/outline.md"`) de modo a assegurar nomes uniformes?
