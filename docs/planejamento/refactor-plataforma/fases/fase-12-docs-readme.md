# Fase 12: Consolidacao De Docs E README

## Objetivo

Revisar `README.md` e `docs/` apos as mudancas estruturais para que a
documentacao reflita o projeto real: registry, wizard, branch por obra,
production planning, agentes, prompts e fluxo de geracao.

## Status

Definida pos-Gate A. Executar depois da Fase 11 aceita.

## Regra De Documentacao Incremental

Cada fase anterior deve atualizar a documentacao relacionada quando alterar
comportamento publico. A Fase 12 nao substitui esse dever. Ela e uma auditoria
final para corrigir inconsistencias, remover texto antigo e consolidar o fluxo.

## Escopo

Revisar no minimo:

```text
README.md
docs/INDICE.md
docs/SNAPSHOT_V0.md
docs/architecture/arquitetura.md
docs/pipelines/pipelines.md
docs/agents/agentes.md
docs/prompts/prompts.md
docs/operacional/comandos.md
docs/book-data/book-data.md
docs/tests/tests.md
```

## Conteudo Que Deve Estar Coberto

- Como executar a CLI classica.
- Como abrir e usar o wizard.
- Como funciona branch por obra.
- O que fica proibido em `main`/`master`.
- Quais pipelines existem e em que ordem usar.
- O papel de `production_planning`.
- Onde ficam artefatos de producao.
- Como agentes sao registrados.
- Como prompts de agentes sao carregados.
- Como funciona o ciclo de feedback.
- Qual e o baseline moderno de testes.

## Fora De Escopo

- Documentar recursos planejados como se ja existissem.
- Reescrever arquitetura novamente.
- Alterar codigo.
- Corrigir bugs de implementacao encontrados durante a auditoria, salvo ajustes
  pequenos e explicitamente documentais.

## Verificacoes Esperadas

```bash
git diff --check -- README.md docs
uv run --with pytest pytest tests
```

## Criterios De Aceite

- README permite a um usuario executar o projeto sem ler o codigo.
- `docs/INDICE.md` aponta para documentos atuais.
- Docs distinguem claramente implementado, legado e planejado.
- Nenhum baseline de teste antigo permanece como atual.
- O snapshot final vira base confiavel para a proxima rodada de melhorias.

