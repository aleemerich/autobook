# Fase 07: Externalizacao Gradual De Prompts De Agentes

## Objetivo

Mover prompts hardcoded de agentes para arquivos versionados em
`prompts/{LANG}/agents/`, preservando comportamento. Esta fase melhora
manutencao e prepara variacoes por idioma, genero e obra, mas nao reescreve a
estrategia literaria dos prompts.

## Status

Definida pos-Gate A. Executar somente depois da Fase 6 aceita.

## Dependencias

- `agent_system/` criado e testado.
- Imports legados de `agents.py` preservados.

## Estrutura Alvo

```text
prompts/
  EN/
    agents/
      drafting.txt
      stylist.txt
      technical_editor.txt
      canon_critic.txt
      style_critic.txt
      flow_critic.txt
      synthesis.txt
  PT-BR/
    agents/
      ...
```

## Subfases Obrigatorias

Esta fase nao deve ser executada como um refactor unico. A ordem e:

1. **Fase 07A: Loader de prompts de agentes**
   - Criar funcao de carregamento com fallback por idioma.
   - Nao migrar agentes ainda.
   - Testar fallback `PT-BR -> EN`.

2. **Fase 07B: Migrar agentes de escrita**
   - Migrar `DraftingAgent` e `StylistAgent`.
   - Preservar exatamente o conteudo semantico dos prompts.
   - Manter fallback hardcoded temporario.

3. **Fase 07C: Migrar editor tecnico e criticos**
   - Migrar `TechnicalEditorAgent`, `CanonCriticAgent`,
     `StyleCriticAgent` e `FlowCriticAgent`.
   - Preservar placeholders como `lore_data`, `slop_rules` e
     `genre_rules`.

4. **Fase 07D: Migrar sintese**
   - Migrar `SynthesisAgent`.
   - Garantir que a saida continue sendo apenas prosa corrigida.

## Fora De Escopo

- Melhorar ou reescrever prompts.
- Criar prompts especificos por obra.
- Criar roteamento automatico de agentes.
- Alterar temperaturas.
- Alterar contratos de saida dos agentes.
- Remover fallback hardcoded antes da migracao estar validada.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_agent_prompts.py
uv run --with pytest pytest tests/test_agent_system.py
uv run --with pytest pytest tests
git diff --check -- agents.py agent_system prompts tests docs/planejamento/refactor-plataforma
```

Testes minimos:

- loader encontra prompt em idioma solicitado.
- loader usa fallback para `EN` quando idioma nao possui arquivo.
- ausencia de prompt retorna erro claro ou fallback hardcoded previsto.
- agente migrado monta prompt final com os mesmos blocos dinamicos de antes.
- nenhum teste chama LLM real.

## Criterios De Aceite

- Mudanca de local do prompt nao muda comportamento esperado.
- Prompts ficam localizaveis por papel.
- `agents.py` permanece compativel durante a transicao.
- A Fase 8 pode definir contratos de feedback sem depender de prompts
  hardcoded em Python.

