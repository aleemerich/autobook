# Documentacao do Autobook

Este indice representa a documentacao operacional atual do projeto. Arquivos
historicos continuam disponiveis quando ajudam a entender a origem do sistema,
mas nao devem ser usados como contrato de execucao sem checagem contra o codigo.

## Leitura Recomendada

1. [Snapshot atual](SNAPSHOT_V0.md)
2. [Arquitetura](architecture/arquitetura.md)
3. [Pipelines](pipelines/pipelines.md)
4. [Comandos operacionais](operacional/comandos.md)
5. [Dados da obra](book-data/book-data.md)
6. [Testes e qualidade](tests/tests.md)

## Mapa Da Documentacao

| Area | Documento | Uso |
| --- | --- | --- |
| Snapshot | [SNAPSHOT_V0.md](SNAPSHOT_V0.md) | Resumo do estado atual do projeto. |
| Arquitetura | [architecture/arquitetura.md](architecture/arquitetura.md) | Componentes, responsabilidades e dependencias. |
| Fluxo completo | [fluxo-detalhado/guia-completo-fluxos.md](fluxo-detalhado/guia-completo-fluxos.md) | Jornada ponta a ponta de uma obra. |
| Pipelines | [pipelines/pipelines.md](pipelines/pipelines.md) | Registro, contratos e fases de cada pipeline. |
| Agentes | [agents/agentes.md](agents/agentes.md) | Papeis, factory, prompts e feedback estruturado. |
| Estrategia de agentes | [agents/agent-system-strategy.md](agents/agent-system-strategy.md) | Decisao arquitetural sobre o adapter moderno. |
| Prompts | [prompts/prompts.md](prompts/prompts.md) | Layout de prompts, idiomas e fallbacks. |
| LLM | [llm/llm.md](llm/llm.md) | Cliente multi-provider e modelos. |
| Configuracao | [configuration/configuration.md](configuration/configuration.md) | Variaveis de ambiente e arquivos de configuracao. |
| Dados da obra | [book-data/book-data.md](book-data/book-data.md) | Contrato de `book_data/`, `chapters/` e `logs/`. |
| Avaliacao | [evaluation/evaluation.md](evaluation/evaluation.md) | Score, slop, juiz LLM e reports. |
| Continuidade | [continuity/continuity.md](continuity/continuity.md) | Verificacao e resolucao de continuidade. |
| Qualidade | [quality-analysis/quality-analysis.md](quality-analysis/quality-analysis.md) | Camadas de qualidade literaria e tecnica. |
| Generos | [genre-strategy/genre-strategy.md](genre-strategy/genre-strategy.md) | Regras de genero e fallback por idioma. |
| Skills | [skills/skills.md](skills/skills.md) | Utilitarios de agentes e redundancia. |
| Scripts | [scripts/scripts.md](scripts/scripts.md) | Scripts raiz suportados, experimentais e legados. |
| Typesetting | [typesetting/typesetting.md](typesetting/typesetting.md) | Geracao de `chapters_content.tex`. |
| Legacy | [legacy/legacy.md](legacy/legacy.md) | Area historica e testes desativados. |
| Backlog | [backlog/pacotes_residuais_pos_refactor_2026-06-17.md](backlog/pacotes_residuais_pos_refactor_2026-06-17.md) | Registro dos pacotes residuais pos-refactor. |
| Referencias historicas | [others/README.md](others/README.md) | Como interpretar `docs/others/`. |

## Estado Verificado

- Entrada principal: `run.py`.
- Modo interativo: `uv run python run.py`.
- Pipelines registradas: `ideation`, `foundation`, `book_generation`, `editorial_revision`.
- Branches de obra: formato obrigatorio `autobook/<slug>` para pipelines protegidas.
- Baseline moderno: `uv run --with pytest pytest tests -q` com 320 testes passando.
- Checks de estilo: `uv run --group dev ruff check .`.
- `legacy/tests` e historico, ignorado por configuracao e com exit code 0 quando executado diretamente.
- Python: `>=3.12`.
- Gerenciador recomendado: `uv`.
