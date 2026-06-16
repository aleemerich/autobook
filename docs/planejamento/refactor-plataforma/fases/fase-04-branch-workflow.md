# Fase 04: Workflow De Branch Por Obra

## Objetivo

Criar utilitarios seguros para suportar a regra:

```text
main = projeto limpo
branch autobook/<slug> = obra em producao
```

Nesta fase, os utilitarios devem existir e ser testados, mas nao precisam ser
integrados ao wizard completo.

## Contexto Obrigatorio

Ler:

- `docs/SNAPSHOT_V0.md`
- `docs/planejamento/refactor-plataforma/03-branch-workflow.md`
- `.git` apenas se necessario para entender estado, sem comandos destrutivos

## Arquivos Permitidos

```text
workspace/__init__.py
workspace/branching.py
tests/test_workspace_branching.py
```

## Fora De Escopo

- Nao executar `git checkout -b` em testes.
- Nao trocar branch real.
- Nao mover `book_data/`, `chapters/` ou `seed.txt`.
- Nao bloquear pipelines existentes ainda.

## Comportamento Desejado

Criar funcoes puras sempre que possivel:

```python
slugify_work_title(title: str) -> str
book_branch_name(title_or_slug: str) -> str
is_main_branch(branch: str) -> bool
```

Funcoes que chamam Git devem ser isoladas e mockaveis:

```python
current_branch() -> str
ensure_not_main_for_generation(branch: str | None = None) -> None
```

Convencao inicial:

```text
autobook/<slug>
```

## Passos

1. Criar pacote `workspace/`.
2. Implementar funcoes puras de slug/branch.
3. Implementar leitura de branch atual por subprocess de forma isolada.
4. Criar excecao clara para tentativa de gerar obra em `main`/`master`.
5. Criar testes com mock para comandos Git.

## Testes Obrigatorios

```bash
uv run --with pytest pytest tests/test_workspace_branching.py
uv run --with pytest pytest tests
```

## Casos De Teste Minimos

- titulo com espacos vira slug.
- titulo com acentos vira slug ASCII ou slug seguro.
- caracteres especiais sao removidos.
- branch `main` e bloqueada.
- branch `master` e bloqueada.
- branch `autobook/minha-obra` e aceita.
- subprocess Git e mockado.

## Criterios De Aceite

- Nenhum teste troca branch real.
- Nenhum comando destrutivo e usado.
- Regras de branch ficam centralizadas.
- Futuro wizard pode reutilizar essas funcoes.

## Checklist Para O Executor

- [ ] Nao executei comandos destrutivos.
- [ ] Testei com mocks.
- [ ] Nao integrei bloqueio nos pipelines ainda.
- [ ] Rodei testes obrigatorios.

## Checklist Para O Supervisor

- [ ] Funcoes puras estao separadas de subprocess.
- [ ] Nome de branch e previsivel.
- [ ] `main` e `master` sao tratados.
- [ ] Nao ha alteracao de fluxo atual.

## Prompt Sugerido Para Delegar

```text
Implemente a Fase 04. Crie workspace/branching.py com utilitarios puros e
mockaveis para branch por obra. Nao troque branch real, nao integre ainda aos
pipelines e nao use comandos destrutivos. Adicione testes.
```

