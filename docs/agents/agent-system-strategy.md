# Estrategia do Sistema de Agentes

Status: decisao arquitetural atual.

## Decisao

O pacote `agent_system/` permanece como adapter moderno sobre o modulo legado
`agents.py`.

Essa decisao evita uma migracao grande e arriscada das classes de agentes neste
momento, preserva compatibilidade com chamadas existentes e ainda permite que o
codigo novo dependa de contratos mais explicitos (`AgentSpec`, registry e
factory moderna).

## Contrato Atual

- Codigo novo deve importar `AgentFactory`, `create_agent` e metadados de
  papeis a partir de `agent_system/` sempre que possivel.
- `agents.py` continua sendo o backend de implementacao concreta dos agentes.
- Registro dinamico de agentes customizados continua suportado, mas o acesso
  deve passar por metodos publicos do legado, como `register_agent`,
  `has_registered_agent` e `unregister_agent`.
- Nenhum codigo novo deve ler ou alterar `_agents_registry` diretamente.

## Migracao Futura Opcional

Uma migracao completa das classes de `agents.py` para `agent_system/` so deve
ser feita se houver ganho claro de manutencao. Se acontecer, deve ser quebrada
em fases pequenas:

1. mover uma classe de agente por vez;
2. manter `agents.py` como camada de compatibilidade;
3. preservar prompts externos em `prompts/{LANG}/agents/`;
4. manter testes de compatibilidade da factory legada ate o fim da transicao.

## Feedback Estruturado

Os agentes criticos devem preferir saida JSON no contrato `CriticReport`, com
`critic_role` e `findings`. Cada finding deve conter:

- `source`
- `instruction`
- `quote`
- `severity`

O parser em `pipelines/book_generation_steps/critique.py` continua aceitando
markdown como fallback para compatibilidade com modelos menores ou respostas
mal formatadas.
