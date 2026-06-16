# Fase 10: Production Planning

## Objetivo

Criar uma pipeline intermediaria que analisa o material da obra antes da escrita
de capitulos e gera artefatos estruturados para orientar quantidade de
capitulos, ritmo, estilo, continuidade e equipe de agentes.

Esta fase ataca diretamente os problemas observados: repeticao, quebra de
linha temporal, numero fixo de capitulos, perda de estilo ao longo do livro e
agentes especializados atuando sem criterio.

## Status

Definida pos-Gate A. Executar depois da Fase 9 aceita.

## Decisao De Design

Adotar arquitetura hibrida:

- nucleo generico de agentes, prompts e contratos mantido pelo projeto;
- equipe e estrategia especificas por obra geradas sob demanda em
  `book_data/production/`.

Nao criar um grande conjunto de agentes genericos que atuam sempre. Agentes
especializados devem ser escalados quando a obra justificar.

## Pre-Requisitos

- Branch workflow operacional.
- Discovery operacional.
- Agent system inicial.
- Prompts externalizados.
- Contratos de feedback definidos.
- `book_generation` com subpipelines e pontos de consumo.

## Pipeline Alvo

Registrar nova pipeline:

```text
production_planning
```

Ela deve ser executada depois de `foundation` e antes de `book_generation`.

## Artefatos Alvo

```text
book_data/production/book_profile.md
book_data/production/scope_plan.json
book_data/production/chapter_strategy.json
book_data/production/style_contract.md
book_data/production/continuity_contract.md
book_data/production/agent_roster.json
book_data/production/validation_rubrics.json
```

Significado minimo:

- `book_profile.md`: leitura consolidada da obra e intencao do projeto.
- `scope_plan.json`: faixa ou estimativa de tamanho, nao numero fixo cego.
- `chapter_strategy.json`: estrutura inicial dos capitulos e funcao narrativa.
- `style_contract.md`: regras de voz, ritmo, densidade e proibicoes.
- `continuity_contract.md`: fatos, linha temporal e pontos de verificacao.
- `agent_roster.json`: agentes obrigatorios e agentes sob demanda.
- `validation_rubrics.json`: criterios usados por criticos e verificadores.

## Regra De Branch

E proibido gravar artefatos de production planning em `main` ou `master`.
Escrita real deve ocorrer apenas em branch de obra, por exemplo:

```text
autobook/<slug>
```

Testes podem usar diretorios temporarios e mocks.

## Fora De Escopo

- Gerar capitulos.
- Reescrever capitulos existentes.
- Implementar wizard completo.
- Garantir qualidade literaria final apenas por esta pipeline.
- Criar todos os agentes especializados possiveis.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_production_planning.py
uv run --with pytest pytest tests/test_pipeline_registry.py
uv run --with pytest pytest tests
git diff --check -- pipelines book_data tests docs/planejamento/refactor-plataforma
```

Testes minimos:

- pipeline registrada em `pipelines/registry.py`.
- pipeline bloqueia escrita em `main`/`master`.
- pipeline cria artefatos em diretorio temporario quando branch e valida.
- artefatos minimos possuem chaves esperadas.
- pipeline nao chama LLM real em testes.

## Criterios De Aceite

- `production_planning` pode ser descoberta pelo wizard futuro.
- Artefatos ficam estruturados e consumiveis pela Fase 9.
- Quantidade de capitulos passa a ser derivada do material e da estrategia.
- Estilo e continuidade passam a ter contratos persistidos.

