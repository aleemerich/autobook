# Fase 08: Contratos De Feedback E Revisao

## Objetivo

Definir contratos estruturados para que toda critica produzida por agentes seja
consumida por uma etapa posterior. Esta fase corrige a direcao do fluxo antes
de refatorar `book_generation`, evitando agentes que analisam texto sem que sua
saida influencie a revisao.

## Status

Definida pos-Gate A. Executar depois da Fase 7 aceita.

## Problema Que Esta Fase Resolve

O projeto possui agentes criticos, mas o fluxo atual permite que relatorios
sejam gerados sem uma obrigacao clara de consumo. Isso aumenta custo, cria falsa
sensacao de controle de qualidade e nao corrige repeticoes, quebras de
continuidade ou perda de ritmo.

## Contrato Alvo

```text
draft_text
  -> critic_report
  -> revision_plan
  -> revised_text
  -> verification_report
```

## Escopo Da Implementacao

Criar uma camada pequena e testavel, sem ainda refatorar toda a pipeline:

```text
writing/
  __init__.py
  feedback.py
tests/test_feedback_lifecycle.py
```

Contratos sugeridos:

- `CriticFinding`: problema encontrado por um agente critico.
- `CriticReport`: conjunto de achados de um agente.
- `RevisionPlan`: plano consolidado para a reescrita.
- `VerificationReport`: resultado da checagem pos-revisao.

Regras:

- Criticas devem ter origem identificavel: canon, estilo, fluxo, tecnico ou
  outro papel futuro.
- Um plano de revisao vazio deve ser valido quando nenhum problema for
  encontrado.
- O contrato deve permitir serializacao simples para JSON ou dict.
- Markdown pode existir para humanos, mas o consumo automatizado deve depender
  de estrutura.

## Fora De Escopo

- Alterar `book_generation` de forma profunda.
- Mudar prompts dos criticos.
- Criar novos agentes.
- Resolver conflito entre criticas contraditorias com heuristica complexa.
- Implementar score literario novo.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_feedback_lifecycle.py
uv run --with pytest pytest tests
git diff --check -- writing tests docs/planejamento/refactor-plataforma
```

Testes minimos:

- criar relatorio com achados.
- criar relatorio vazio.
- consolidar relatorios em plano de revisao.
- serializar e desserializar contrato sem perder dados essenciais.
- validar que achados preservam papel de origem e instrucao de correcao.

## Criterios De Aceite

- Existe um contrato claro para a Fase 9 consumir.
- Nao ha chamada LLM real.
- Nao ha mudanca de comportamento externo das pipelines.
- A saida dos agentes criticos passa a ter destino tecnico definido.

