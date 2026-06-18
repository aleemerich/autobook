# Comandos Operacionais

Use `uv` como caminho padrao para execucao local.

## Setup

```bash
uv sync
cp .env.example .env
```

## Wizard

```bash
uv run python run.py
```

Sem argumentos, `run.py` abre o Autobook Wizard. Ele:

- mostra branch atual e workspace registrado;
- lista pipelines disponiveis;
- recomenda proximos passos;
- sugere/cria branch `autobook/<slug>`;
- pode executar a pipeline escolhida.

## CLI Classica

```bash
uv run python run.py --pipeline ideation
uv run python run.py --pipeline foundation
uv run python run.py --pipeline book_generation --from-scratch
uv run python run.py --pipeline book_generation --chapter 5-7
uv run python run.py --pipeline editorial_revision --chapter 3
```

Pipelines protegidas exigem branch `autobook/<slug>`.

## Avaliacao E Continuidade

```bash
uv run python evaluate.py --chapter 3
uv run python verify_continuity.py
uv run python resolve_continuity.py
```

`resolve_continuity.py` le `logs/eval_logs/continuity_report.json`, gera uma
orientacao editorial quando necessario e chama a revisao via `run.py`.

## Scripts Auxiliares

Consulte [../scripts/scripts.md](../scripts/scripts.md) para a classificacao
entre suportado, experimental e historico.

Exemplos comuns:

```bash
uv run python gen_brief.py
uv run python gen_revision.py
uv run python compare_chapters.py
uv run python adversarial_edit.py
uv run python typeset/build_tex.py
```

## Qualidade

```bash
uv run --group dev ruff check .
uv run --with pytest pytest tests -q
uv run --with pytest pytest legacy/tests -q
git diff --check
```

Estado esperado:

- 320 testes modernos passando.
- Legacy tests sem coleta e exit code 0.
- Ruff e `git diff --check` sem erros.
