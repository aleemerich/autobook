# Fase 08: Feedback Lifecycle [ROADMAP PRELIMINAR]

## Objetivo

Garantir que todo feedback produzido por agente seja consumido por uma etapa posterior.

## Status

> [!WARNING]
> **ROADMAP PRELIMINAR (BLOQUEADO):** Esta especificação é preparatória e **não deve ser detalhada ou executada** antes da aprovação do Gate A.

## Estratégia Recomendada para Evitar Retrabalho

Para evitar o refatoramento em código monolítico e posterior retrabalho, a implementação do ciclo de feedback deve ser estruturada em fases coordenadas com a decomposição do pipeline:
- **Fase 8a (Documentação):** Formalizar o contrato de feedback (`critic_report -> revision_plan -> revised_text`).
- **Fase 9:** Decompor `book_generation` em subpipelines menores.
- **Fase 8b (Implementação):** Implementar o feedback lifecycle diretamente no contexto das novas subpipelines.

## Contrato Alvo

```text
critic_report -> revision_plan -> revised_text -> verification_report
```

## Regras

- Agente critico nao deve atuar se sua saida nao for consumida.
- Preferir JSON para automacao e Markdown para relatorio humano.
- Testes devem provar que a saida de critica chega na sintese/revisao.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_feedback_lifecycle.py
uv run --with pytest pytest tests
```


