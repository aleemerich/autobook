# Fase 09: `book_generation` Em Subpipelines

## Objetivo

Separar `book_generation` em subpipelines reutilizaveis.

## Status

Nao executar como uma unica tarefa. Quebrar antes em subfases.

## Subfases Recomendadas

```text
fase-09a-extrair-chapter-preparation.md
fase-09b-extrair-drafting.md
fase-09c-extrair-critique.md
fase-09d-extrair-revision.md
fase-09e-extrair-validation.md
fase-09f-extrair-persistence.md
```

## Regra

Cada subfase deve manter comportamento externo e testes passando.

## Fora De Escopo

- Nao implementar `production_planning`.
- Nao mudar formato de capitulos.
- Nao mudar criterio de score.

