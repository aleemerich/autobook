# Fase 06: Organizacao Inicial Do Sistema De Agentes [ROADMAP PRELIMINAR]

## Objetivo

Preparar uma estrutura de agentes mais manutenivel sem quebrar imports atuais, usando o pacote `agent_system/` para mitigar conflitos do Python.

## Status

> [!WARNING]
> **ROADMAP PRELIMINAR (BLOQUEADO):** Esta especificação é preparatória e **não deve ser detalhada ou executada** antes da aprovação do Gate A.

## Direção Recomendada (Decisão Fechada)

Para evitar conflitos críticos de imports no Python (já que o arquivo `agents.py` existe na raiz), a decisão de design está **fechada**: utilizaremos obrigatoriamente um pacote intermediário com o nome `agent_system/` (em vez de `agents/`).

Estrutura fechada da pasta `agent_system/`:
```text
agent_system/
  __init__.py
  base.py
  registry.py
  factory.py
```

Os imports serão migrados gradualmente sem criar pacotes conflitantes na raiz do projeto.

## Fora De Escopo Inicial

- Nao mover todos os agentes de uma vez.
- Nao externalizar todos os prompts nesta fase.
- Nao refatorar `book_generation` profundamente.

## Subfases Futuras (Planejamento)

1. criar `agent_system/base.py`;
2. criar registry simples;
3. espelhar factory atual;
4. manter compatibilidade com `agents.py` por proxy;
5. migrar agentes um por vez.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_agents_registry.py
uv run --with pytest pytest tests
```


