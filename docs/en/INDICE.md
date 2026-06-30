# Autobook Documentation

This index represents the current operational documentation for the project.
Historical files remain available when they help explain the system's origin,
but they should not be treated as execution contracts without checking them
against the current code.

## Recommended Reading

1. [Current snapshot](SNAPSHOT_V0.md)
2. [Architecture](architecture/arquitetura.md)
3. [Pipelines](pipelines/pipelines.md)
4. [Complete terminal commands](operacional/comandos-completos.md)
5. [Book data](book-data/book-data.md)
6. [Tests and quality](tests/tests.md)

## Documentation Map

| Area | Document | Purpose |
| --- | --- | --- |
| Snapshot | [SNAPSHOT_V0.md](SNAPSHOT_V0.md) | Summary of the current project state. |
| Architecture | [architecture/arquitetura.md](architecture/arquitetura.md) | Components, responsibilities and dependencies. |
| Full flow | [fluxo-detalhado/guia-completo-fluxos.md](fluxo-detalhado/guia-completo-fluxos.md) | End-to-end journey for producing a book. |
| Pipelines | [pipelines/pipelines.md](pipelines/pipelines.md) | Registry, contracts and phases for each pipeline. |
| Complete commands | [operacional/comandos-completos.md](operacional/comandos-completos.md) | All terminal commands, parameters, examples and end-to-end sequence. |
| Agents | [agents/agentes.md](agents/agentes.md) | Roles, factory, prompts and structured feedback. |
| Agent strategy | [agents/agent-system-strategy.md](agents/agent-system-strategy.md) | Architectural decision for the modern adapter. |
| Prompts | [prompts/prompts.md](prompts/prompts.md) | Prompt layout, languages and fallbacks. |
| LLM | [llm/llm.md](llm/llm.md) | Multi-provider client and model roles. |
| Configuration | [configuration/configuration.md](configuration/configuration.md) | Environment variables and configuration files. |
| Book data | [book-data/book-data.md](book-data/book-data.md) | Contract for `book_data/`, `chapters/` and `logs/`. |
| Evaluation | [evaluation/evaluation.md](evaluation/evaluation.md) | Scores, slop, LLM judging and reports. |
| Continuity | [continuity/continuity.md](continuity/continuity.md) | Continuity verification and resolution. |
| Quality | [quality-analysis/quality-analysis.md](quality-analysis/quality-analysis.md) | Literary and technical quality layers. |
| Genres | [genre-strategy/genre-strategy.md](genre-strategy/genre-strategy.md) | Genre rules and language fallback. |
| Skills | [skills/skills.md](skills/skills.md) | Agent utilities and redundancy tools. |
| Scripts | [scripts/scripts.md](scripts/scripts.md) | Supported, experimental and legacy root scripts. |
| Typesetting | [typesetting/typesetting.md](typesetting/typesetting.md) | Generation of `chapters_content.tex`. |
| Legacy | [legacy/legacy.md](legacy/legacy.md) | Historical area and disabled tests. |
| Backlog | [backlog/pacotes_residuais_pos_refactor_2026-06-17.md](backlog/pacotes_residuais_pos_refactor_2026-06-17.md) | Record of post-refactor residual packages. |
| Historical references | [others/README.md](others/README.md) | How to interpret this language folder's `others/`. |

## Verified State

- Main entry point: `run.py`.
- Interactive mode: `uv run python run.py`.
- Registered pipelines: `ideation`, `foundation`, `book_generation`, `editorial_revision`.
- Book branches: required format `autobook/<slug>` for protected pipelines.
- Modern baseline: `uv run --with pytest pytest tests -q` with 320 passing tests.
- Style checks: `uv run --group dev ruff check .`.
- `legacy/tests` is historical, ignored by configuration and exits with code 0 when run directly.
- Python: `>=3.12`.
- Recommended package manager: `uv`.
