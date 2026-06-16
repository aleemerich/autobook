# Fase 07: Externalizacao Gradual De Prompts De Agentes

## Objetivo

Mover prompts hardcoded para arquivos em `prompts/{LANG}/agents/`, com fallback
seguro durante a migracao.

## Status

Spec preparatoria. Detalhar depois da Fase 06.

## Direcao Recomendada

Criar subfases:

```text
fase-07a-loader-prompts-agentes.md
fase-07b-migrar-drafting-agent.md
fase-07c-migrar-critic-agents.md
fase-07d-migrar-synthesis-agent.md
```

## Regras

- Migrar poucos agentes por vez.
- Nao mudar semantica do prompt durante a migracao.
- Testar fallback PT-BR -> EN.
- Manter prompt hardcoded como fallback temporario se necessario.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_agent_prompts.py
uv run --with pytest pytest tests
```

