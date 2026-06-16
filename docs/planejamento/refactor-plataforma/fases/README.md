# Specs Por Fase

Esta pasta quebra o plano mestre
`docs/planejamento/refactor-plataforma/plano-migracao-modelos-medios.md` em
specs menores, adequadas para execucao por modelos medios e revisao por um
supervisor.

## Como Usar

Para delegar uma tarefa:

1. Escolha uma fase.
2. Entregue ao executor apenas:
   - o plano mestre;
   - esta spec da fase;
   - os arquivos de codigo citados na spec.
3. Exija os testes listados.
4. Submeta o diff ao supervisor.

## Fases Prontas Para Execução

Estas fases estão revisadas e prontas para delegação direta aos modelos executores:

| Ordem | Spec | Status |
| --- | --- | --- |
| 0 | [fase-00-specs.md](fase-00-specs.md) | Pronta para execucao |
| 1 | [fase-01-pipeline-base.md](fase-01-pipeline-base.md) | Pronta para execucao |
| 2 | [fase-02-pipeline-registry.md](fase-02-pipeline-registry.md) | Pronta para execucao |
| 3 | [fase-03-run-wizard-stub.md](fase-03-run-wizard-stub.md) | Pronta para execucao |
| 4 | [fase-04-branch-workflow.md](fase-04-branch-workflow.md) | Pronta para execucao |
| 5 | [fase-05-discovery.md](fase-05-discovery.md) | Pronta para execucao |

## Roadmap Preliminar (Bloqueado)

Estas fases constituem a direção estratégica de longo prazo e **exigem a aprovação formal do Gate A (Revisão Arquitetural)** antes de qualquer detalhamento ou execução:

| Ordem | Spec | Status |
| --- | --- | --- |
| 6 | [fase-06-agent-system.md](fase-06-agent-system.md) | Roadmap (Requer Gate A) |
| 7 | [fase-07-agent-prompts.md](fase-07-agent-prompts.md) | Roadmap (Requer Gate A) |
| 8 | [fase-08-feedback-lifecycle.md](fase-08-feedback-lifecycle.md) | Roadmap (Requer Gate A) |
| 9 | [fase-09-book-generation-subpipelines.md](fase-09-book-generation-subpipelines.md) | Roadmap (Requer Gate A) |
| 10 | [fase-10-production-planning.md](fase-10-production-planning.md) | Roadmap (Requer Gate A) |
| 11 | [fase-11-wizard-workspace.md](fase-11-wizard-workspace.md) | Roadmap (Requer Gate A) |
| 12 | [fase-12-docs-readme.md](fase-12-docs-readme.md) | Roadmap (Requer Gate A) |


## Regra De Ouro

Cada fase deve terminar com:

- testes passando;
- diff pequeno;
- docs atualizadas quando necessario;
- resumo claro do que mudou;
- riscos e pendencias registrados.

