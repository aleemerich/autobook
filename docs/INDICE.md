# Documentacao do Autobook

Este indice reflete a estrutura real da pasta `docs/` e o estado atual do
codigo na branch em uso. O objetivo deste v0 e servir como snapshot tecnico:
o que existe, o que funciona, o que esta parcial e o que precisa ser
atualizado antes de virar documentacao definitiva.

## Leitura Recomendada

1. [Snapshot v0](SNAPSHOT_V0.md)
2. [Arquitetura](architecture/arquitetura.md)
3. [Pipelines](pipelines/pipelines.md)
4. [Comandos operacionais](operacional/comandos.md)
5. [Dados do livro](book-data/book-data.md)
6. [Testes](tests/tests.md)

## Documentos Principais

| Area | Documento | Status v0 |
| --- | --- | --- |
| Snapshot e lacunas | [SNAPSHOT_V0.md](SNAPSHOT_V0.md) | Atual |
| Arquitetura | [architecture/arquitetura.md](architecture/arquitetura.md) | Coberto, precisa revisao fina |
| Pipelines | [pipelines/pipelines.md](pipelines/pipelines.md) | Coberto, parcialmente desatualizado |
| Fluxo detalhado | [fluxo-detalhado/guia-completo-fluxos.md](fluxo-detalhado/guia-completo-fluxos.md) | Rico, precisa checagem contra codigo |
| Agentes | [agents/agentes.md](agents/agentes.md) | Coberto |
| Cliente LLM | [llm/llm.md](llm/llm.md) | Coberto |
| Prompts e localizacao | [prompts/prompts.md](prompts/prompts.md) | Coberto |
| Generos | [genre-strategy/genre-strategy.md](genre-strategy/genre-strategy.md) | Novo v0 |
| Avaliacao | [evaluation/evaluation.md](evaluation/evaluation.md) | Coberto |
| Continuidade | [continuity/continuity.md](continuity/continuity.md) | Novo v0 |
| Configuracao | [configuration/configuration.md](configuration/configuration.md) | Atualizado para v0 |
| Dados do livro | [book-data/book-data.md](book-data/book-data.md) | Novo v0 |
| Typesetting | [typesetting/typesetting.md](typesetting/typesetting.md) | Coberto, com partes manuais |
| Testes | [tests/tests.md](tests/tests.md) | Atualizado para baseline real |
| Legacy | [legacy/legacy.md](legacy/legacy.md) | Precisa limpeza |
| Qualidade | [quality-analysis/quality-analysis.md](quality-analysis/quality-analysis.md) | Coberto |
| Skills | [skills/skills.md](skills/skills.md) | Novo v0 |
| Comandos | [operacional/comandos.md](operacional/comandos.md) | Novo v0 |
| Planejamento futuro | [planejamento/como-transformar-parecer-em-specs.md](planejamento/como-transformar-parecer-em-specs.md) | Novo v0 |
| Plano para modelos medios | [planejamento/refactor-plataforma/plano-migracao-modelos-medios.md](planejamento/refactor-plataforma/plano-migracao-modelos-medios.md) | Novo v0 |
| Specs por fase | [planejamento/refactor-plataforma/fases/README.md](planejamento/refactor-plataforma/fases/README.md) | Novo v0 |
| Spec 00 - Decisão | [planejamento/refactor-plataforma/00-decisao.md](planejamento/refactor-plataforma/00-decisao.md) | Novo v0 (Fase 0) |
| Spec 01 - run.py Entrypoint | [planejamento/refactor-plataforma/01-run-entrypoint.md](planejamento/refactor-plataforma/01-run-entrypoint.md) | Novo v0 (Fase 0) |
| Spec 02 - Pipeline Contract | [planejamento/refactor-plataforma/02-pipeline-contract.md](planejamento/refactor-plataforma/02-pipeline-contract.md) | Novo v0 (Fase 0) |
| Spec 03 - Branch Workflow | [planejamento/refactor-plataforma/03-branch-workflow.md](planejamento/refactor-plataforma/03-branch-workflow.md) | Novo v0 (Fase 0) |
| Spec 04 - Agent Registry | [planejamento/refactor-plataforma/04-agent-registry.md](planejamento/refactor-plataforma/04-agent-registry.md) | Novo v0 (Fase 0) |
| Spec 05 - Prompt Layout | [planejamento/refactor-plataforma/05-prompt-layout.md](planejamento/refactor-plataforma/05-prompt-layout.md) | Novo v0 (Fase 0) |
| Spec 06 - Feedback Lifecycle | [planejamento/refactor-plataforma/06-feedback-lifecycle.md](planejamento/refactor-plataforma/06-feedback-lifecycle.md) | Novo v0 (Fase 0) |
| Spec 07 - Migration Plan | [planejamento/refactor-plataforma/07-migration-plan.md](planejamento/refactor-plataforma/07-migration-plan.md) | Novo v0 (Fase 0) |
| Gate A Review | [planejamento/refactor-plataforma/gates/gate-a-review.md](planejamento/refactor-plataforma/gates/gate-a-review.md) | Novo v0 (Pós-Fase 5) |
| Fase 05.1 - Hardening Pos-Gate A | [planejamento/refactor-plataforma/fases/fase-05-1-hardening-pos-gate-a.md](planejamento/refactor-plataforma/fases/fase-05-1-hardening-pos-gate-a.md) | Concluída |
| Fase 06 - Agent System | [planejamento/refactor-plataforma/fases/fase-06-agent-system.md](planejamento/refactor-plataforma/fases/fase-06-agent-system.md) | Concluída |
| Fase 07 - Agent Prompts | [planejamento/refactor-plataforma/fases/fase-07-agent-prompts.md](planejamento/refactor-plataforma/fases/fase-07-agent-prompts.md) | Definida |
| Fase 08 - Feedback Lifecycle | [planejamento/refactor-plataforma/fases/fase-08-feedback-lifecycle.md](planejamento/refactor-plataforma/fases/fase-08-feedback-lifecycle.md) | Definida |
| Fase 09 - Book Generation Subpipelines | [planejamento/refactor-plataforma/fases/fase-09-book-generation-subpipelines.md](planejamento/refactor-plataforma/fases/fase-09-book-generation-subpipelines.md) | Definida |
| Fase 10 - Production Planning | [planejamento/refactor-plataforma/fases/fase-10-production-planning.md](planejamento/refactor-plataforma/fases/fase-10-production-planning.md) | Definida |
| Fase 11 - Wizard Workspace | [planejamento/refactor-plataforma/fases/fase-11-wizard-workspace.md](planejamento/refactor-plataforma/fases/fase-11-wizard-workspace.md) | Definida |
| Fase 12 - Docs e README | [planejamento/refactor-plataforma/fases/fase-12-docs-readme.md](planejamento/refactor-plataforma/fases/fase-12-docs-readme.md) | Definida |


## Referencias Historicas e Criativas

Os arquivos abaixo sao uteis como material de referencia, mas nao devem ser
lidos como documentacao tecnica atual sem validacao contra o codigo:

- [others/PIPELINE.md](others/PIPELINE.md)
- [others/CRAFT.md](others/CRAFT.md)
- [others/ANTI-SLOP.md](others/ANTI-SLOP.md)
- [others/ANTI-PATTERNS.md](others/ANTI-PATTERNS.md)
- [others/WORKFLOW.md](others/WORKFLOW.md)
- [others/PROJECT_STUDY.md](others/PROJECT_STUDY.md)
- [others/program.md](others/program.md)
- [others/cauldron.txt](others/cauldron.txt)
- [others/results.tsv](others/results.tsv)

## Analises

- [analises/docs_analysis.md](analises/docs_analysis.md): auditoria detalhada da documentacao contra o codigo.
- [analises/analise_arquitetura_autobook.md](analises/analise_arquitetura_autobook.md): proposta de arquitetura e evolucao.
- [analises/recomendacao_pipeline_producao.md](analises/recomendacao_pipeline_producao.md): parecer sobre pipeline intermediaria, agentes dinamicos, continuidade, estilo e modelos de menor custo.

Observacao: `docs/analises/` aparece como nao versionado no momento deste
snapshot.

## Estado Atual Verificado

- Entrada principal: `run.py`.
- Pipelines suportados pela CLI: `ideation`, `foundation`, `book_generation`, `editorial_revision`.
- Baseline moderno de testes: `uv run --with pytest pytest tests` com 274 testes passando.
- `legacy/tests` nao faz parte do baseline atual; a coleta falha por imports de modulos removidos ou renomeados.
- Python: `>=3.12`.
- Gerenciador recomendado: `uv`.
- Provedores LLM suportados em `llm.py`: `anthropic`, `openai`, `gemini`, `openrouter`.
