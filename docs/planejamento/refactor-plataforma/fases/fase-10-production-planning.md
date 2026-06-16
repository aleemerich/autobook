# Fase 10: Production Planning [ROADMAP PRELIMINAR]

## Objetivo

Implementar a pipeline `production_planning` proposta em `docs/analises/recomendacao_pipeline_producao.md` utilizando a base refatorada.

## Status

> [!WARNING]
> **ROADMAP PRELIMINAR (BLOQUEADO):** Esta especificação é preliminar e **não deve ser executada** antes do Gate A. Ela só deve ser detalhada depois do Gate A e após a conclusão sólida das fases de registry, discovery e branch workflow.

## Regra de Segurança de Branch (Crítica)

A pipeline `production_planning` **só está autorizada a gerar e gravar artefatos estruturados na branch dedicada da obra** (ex: `autobook/<slug>`). É expressamente proibido gerar ou persistir artefatos de produção na branch `main` ou `master` (salvo execuções de testes automatizados unitários ou modo dry-run explicitamente configurados).

## Pre-requisitos

- pipeline registry;
- discovery;
- branch workflow completo;
- contrato de pipelines;
- agent system inicial;
- prompt layout inicial;
- feedback lifecycle definido.

## Artefatos Alvo

```text
book_data/production/scope_plan.json
book_data/production/chapter_plan.json
book_data/production/style_contract.md
book_data/production/style_metrics.json
book_data/production/continuity_graph.json
book_data/production/agent_roster.json
book_data/production/validation_rubrics.json
book_data/production/retrieval_index.json
```

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_production_planning.py
uv run --with pytest pytest tests
```


