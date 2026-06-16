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

## Estado Pos-Gate A

As Fases 0 a 5 foram executadas e o Gate A foi aprovado com correcoes
nao bloqueantes. A ordem abaixo define o caminho de trabalho a partir desse
ponto. Cada fase so deve ser delegada depois que a anterior for aceita pelo
supervisor.

## Fases Concluidas

Estas fases compoem a fundacao ja implementada:

| Ordem | Spec | Status |
| --- | --- | --- |
| 0 | [fase-00-specs.md](fase-00-specs.md) | Concluida |
| 1 | [fase-01-pipeline-base.md](fase-01-pipeline-base.md) | Concluida |
| 2 | [fase-02-pipeline-registry.md](fase-02-pipeline-registry.md) | Concluida |
| 3 | [fase-03-run-wizard-stub.md](fase-03-run-wizard-stub.md) | Concluida |
| 4 | [fase-04-branch-workflow.md](fase-04-branch-workflow.md) | Concluida |
| 5 | [fase-05-discovery.md](fase-05-discovery.md) | Concluida |

## Proximas Fases Definidas

Estas fases estao definidas pelo supervisor. O executor deve receber uma fase
por vez, com seus arquivos-alvo e comandos de teste.

| Ordem | Spec | Status |
| --- | --- | --- |
| 5.1 | [fase-05-1-hardening-pos-gate-a.md](fase-05-1-hardening-pos-gate-a.md) | Concluida |
| 6 | [fase-06-agent-system.md](fase-06-agent-system.md) | Concluida |
| 7 | [fase-07-agent-prompts.md](fase-07-agent-prompts.md) | Definida pos-Gate A |
| 8 | [fase-08-feedback-lifecycle.md](fase-08-feedback-lifecycle.md) | Definida pos-Gate A |
| 9 | [fase-09-book-generation-subpipelines.md](fase-09-book-generation-subpipelines.md) | Definida pos-Gate A |
| 10 | [fase-10-production-planning.md](fase-10-production-planning.md) | Definida pos-Gate A |
| 11 | [fase-11-wizard-workspace.md](fase-11-wizard-workspace.md) | Definida pos-Gate A |
| 12 | [fase-12-docs-readme.md](fase-12-docs-readme.md) | Definida pos-Gate A |


## Regra De Ouro

Cada fase deve terminar com:

- testes passando;
- diff pequeno;
- docs atualizadas quando necessario;
- resumo claro do que mudou;
- riscos e pendencias registrados.
