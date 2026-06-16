# Fase 05.1: Hardening Pos-Gate A

## Objetivo

Aplicar as correcoes pequenas registradas no Gate A antes de iniciar o ciclo de
agentes. Esta fase nao muda arquitetura, nao altera comportamento de pipelines
e serve para reduzir divida tecnica imediata.

## Status

Concluida.

## Dependencias

- Fases 0 a 5 concluidas.
- Gate A aprovado em `docs/planejamento/refactor-plataforma/gates/gate-a-review.md`.

## Escopo

1. Tornar `PipelineSpec` imutavel.
   - Arquivo: `pipelines/registry.py`.
   - Acao esperada: usar `@dataclass(frozen=True)`.

2. Proteger nomes invalidos de branch de obra.
   - Arquivo: `workspace/branching.py`.
   - Acao esperada: `book_branch_name("")` e titulos que viram slug vazio devem
     levantar erro claro, sem retornar `autobook/`.

3. Ampliar cobertura de discovery.
   - Arquivo: `tests/test_cli_discovery.py`.
   - Cobrir pipelines retornadas pelo registry.
   - Cobrir arquivos presentes em `logs/`.
   - Cobrir artefatos presentes em `book_data/production/`.

4. Atualizar documentacao pontual.
   - Arquivos provaveis:
     - `docs/INDICE.md`
     - `docs/planejamento/refactor-plataforma/fases/README.md`
   - Ajustar status e baseline de testes se estiverem desatualizados.

## Fora De Escopo

- Nao implementar `agent_system/`.
- Nao alterar prompts.
- Nao alterar `agents.py`.
- Nao alterar fluxo de `book_generation`.
- Nao criar wizard completo.
- Nao executar comandos Git destrutivos.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_pipeline_registry.py tests/test_workspace_branching.py tests/test_cli_discovery.py
uv run --with pytest pytest tests
git diff --check -- pipelines workspace cli tests docs/planejamento/refactor-plataforma docs/INDICE.md
```

## Criterios De Aceite

- Suite moderna de testes passa.
- Discovery continua somente leitura.
- Registry continua sem instanciar pipelines ao listar.
- Branch vazia ou sanitizada para vazio nao gera nome invalido.
- Documentacao reflete que o Gate A foi aprovado e que a fase seguinte e a
  Fase 6.

