# Fase 06: Infraestrutura Inicial Do Sistema De Agentes

## Objetivo

Criar uma camada modular para agentes sem mudar comportamento narrativo,
prompts, chamadas LLM ou imports legados. A fase prepara o pacote
`agent_system/` para que as fases seguintes possam organizar prompts,
especializacao por obra e feedback sem depender do arquivo monolitico
`agents.py`.

## Status

Definida pos-Gate A. Pode ser delegada depois da Fase 05.1.

## Decisao Arquitetural

Usar obrigatoriamente o pacote `agent_system/`. Nao criar uma pasta `agents/`
enquanto existir `agents.py` na raiz, para evitar conflito de imports do
Python.

`agents.py` continua existindo e continua sendo o ponto legado de importacao.
Esta fase nao remove, nao renomeia e nao deprecia esse arquivo.

## Estado Atual

`agents.py` concentra:

- `Agent`: classe base que chama `llm.call_llm` no metodo `execute`.
- `DraftingAgent`: escrita do rascunho narrativo.
- `StylistAgent`: reescrita com genero, ritmo e estilo.
- `TechnicalEditorAgent`: consistencia tecnica, lore, PT-BR e anti-slop.
- `CanonCriticAgent`: critica canonica e de lore.
- `StyleCriticAgent`: critica de estilo, voz e repeticoes.
- `FlowCriticAgent`: critica de ritmo, fluxo e transicoes.
- `SynthesisAgent`: correcao direcionada a partir de critica.
- `AgentFactory`: singleton que instancia agentes por papel.
- `load_skill_agent`: carregamento dinamico de agentes em `skills/`.

## Escopo Da Implementacao

Criar estrutura minima:

```text
agent_system/
  __init__.py
  base.py
  registry.py
  factory.py
tests/test_agent_system.py
```

Comportamento esperado:

- `agent_system/base.py` define contratos leves para agentes e especificacoes
  de papel, sem chamar LLM.
- `agent_system/registry.py` lista os papeis atuais de agentes de forma
  centralizada:
  - `drafting`
  - `stylist`
  - `technical_editor`
  - `canon_critic`
  - `style_critic`
  - `flow_critic`
  - `synthesis`
- `agent_system/factory.py` oferece uma API nova para criar agentes, delegando
  para o `AgentFactory` legado de `agents.py` quando necessario.
- Listar papeis nao deve instanciar agentes nem chamar LLM.
- Criar agentes pode usar as classes legadas, mas nao pode alterar seus prompts
  nem seus parametros padrao.
- Imports legados como `from agents import AgentFactory` continuam funcionando.

## Fora De Escopo

- Externalizar prompts para arquivos.
- Alterar textos dos prompts existentes.
- Alterar `execute` ou `llm.call_llm`.
- Refatorar `book_generation`.
- Criar agentes especializados por obra.
- Remover ou deprecar `agents.py`.
- Mudar o carregamento dinamico de `skills/` alem do necessario para preservar
  compatibilidade.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_agent_system.py
uv run --with pytest pytest tests
git diff --check -- agent_system agents.py tests docs/planejamento/refactor-plataforma
```

Testes minimos:

- registry lista todos os papeis atuais.
- registry retorna erro claro para papel inexistente.
- factory cria pelo menos um agente legado sem chamar `execute`.
- factory aceita kwargs dos agentes atuais.
- imports legados de `agents.py` continuam funcionando.
- listar agentes nao chama LLM.

## Criterios De Aceite

- Nenhum prompt muda.
- Nenhuma chamada real a LLM ocorre em testes.
- Todas as pipelines existentes continuam importando normalmente.
- O novo pacote existe, mas o sistema antigo continua funcional.
- A Fase 7 pode usar `agent_system/` como base para externalizar prompts.

## Risco Principal

Conflito de imports e dependencias circulares entre `agents.py` e
`agent_system/`. O executor deve preferir importacao tardia em factory quando
isso reduzir risco de ciclo.

