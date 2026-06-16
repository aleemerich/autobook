# 07 - Refactoring Migration Plan Spec

## Objetivo

Consolidar a ordem de execucao do refatoramento da plataforma Autobook apos o
Gate A, mantendo a divisao entre planejamento de supervisor e implementacao por
modelos executores.

## Estado Atual

As Fases 0 a 5 foram implementadas e o Gate A foi aprovado com correcoes nao
bloqueantes. A partir deste ponto, as fases seguintes estao definidas em specs
individuais e devem ser executadas uma por vez, sempre com revisao do
supervisor antes de avancar.

## Ordem Definida

| Ordem | Fase | Objetivo |
| --- | --- | --- |
| 5.1 | Hardening Pos-Gate A | Corrigir achados pequenos antes de agentes. |
| 6 | Agent System | Criar `agent_system/` sem mudar comportamento narrativo. |
| 7 | Agent Prompts | Externalizar prompts gradualmente. |
| 8 | Feedback Lifecycle | Criar contratos estruturados para critica e revisao. |
| 9 | Book Generation Subpipelines | Refatorar `book_generation` em etapas reutilizaveis. |
| 10 | Production Planning | Gerar estrategia da obra e artefatos de producao. |
| 11 | Wizard Workspace | Transformar o wizard em area de trabalho guiada. |
| 12 | Docs e README | Consolidar documentacao contra o comportamento real. |

## Specs Canonicas

```text
docs/planejamento/refactor-plataforma/fases/fase-05-1-hardening-pos-gate-a.md
docs/planejamento/refactor-plataforma/fases/fase-06-agent-system.md
docs/planejamento/refactor-plataforma/fases/fase-07-agent-prompts.md
docs/planejamento/refactor-plataforma/fases/fase-08-feedback-lifecycle.md
docs/planejamento/refactor-plataforma/fases/fase-09-book-generation-subpipelines.md
docs/planejamento/refactor-plataforma/fases/fase-10-production-planning.md
docs/planejamento/refactor-plataforma/fases/fase-11-wizard-workspace.md
docs/planejamento/refactor-plataforma/fases/fase-12-docs-readme.md
```

## Regras De Execucao

1. O executor recebe uma fase por vez.
2. O executor nao redefine arquitetura.
3. O executor pode tomar decisoes locais simples quando nao ampliam escopo.
4. O supervisor revisa diff, testes, docs e aderencia antes da fase seguinte.
5. Qualquer alteracao de comportamento publico deve atualizar docs na mesma
   entrega.
6. Nenhuma fase pode chamar LLM real em testes.
7. Nenhuma fase pode executar comando Git destrutivo em testes.

## Papel Do Supervisor

O supervisor e responsavel por:

- definir fases;
- definir criterios de aceite;
- decidir mudancas de ordem;
- aprovar ou rejeitar entregas;
- impedir refactors amplos fora de escopo;
- proteger retrocompatibilidade da CLI e dos imports.

## Papel Do Executor

O executor e responsavel por:

- ler a spec da fase;
- implementar somente o escopo permitido;
- adicionar ou ajustar testes;
- rodar os comandos obrigatorios;
- atualizar docs incrementais quando aplicavel;
- reportar arquivos alterados, testes e riscos.

## Criterios Gerais De Aceite

- Suite moderna passa.
- `git diff --check` passa nos arquivos alterados.
- Mudanca e pequena o suficiente para revisao.
- Docs nao prometem recurso inexistente.
- O projeto continua compativel com a CLI classica.
