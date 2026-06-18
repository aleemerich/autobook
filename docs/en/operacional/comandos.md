# Operational Commands

Use `uv` as the default local execution path.

## Setup

```bash
uv sync
cp .env.example .env
```

## Wizard

```bash
uv run python run.py
```

Without arguments, `run.py` opens the Autobook Wizard. It:

- shows the current branch and registered workspace;
- lists available pipelines;
- recommends next steps;
- suggests/creates an `autobook/<slug>` branch;
- can execute the selected pipeline.

## Classic CLI

```bash
uv run python run.py --pipeline ideation
uv run python run.py --pipeline foundation
uv run python run.py --pipeline book_generation --from-scratch
uv run python run.py --pipeline book_generation --chapter 5-7
uv run python run.py --pipeline editorial_revision --chapter 3
```

Protected pipelines require an `autobook/<slug>` branch.

## Evaluation And Continuity

```bash
uv run python evaluate.py --chapter 3
uv run python verify_continuity.py
uv run python resolve_continuity.py
```

`resolve_continuity.py` reads `logs/eval_logs/continuity_report.json`, creates
editorial guidance when needed and calls revision through `run.py`.

## Auxiliary Scripts

See [../scripts/scripts.md](../scripts/scripts.md) for the supported,
experimental and historical classification.

Common examples:

```bash
uv run python gen_brief.py
uv run python gen_revision.py
uv run python compare_chapters.py
uv run python adversarial_edit.py
uv run python typeset/build_tex.py
```

## Quality

```bash
uv run --group dev ruff check .
uv run --with pytest pytest tests -q
uv run --with pytest pytest legacy/tests -q
git diff --check
```

Expected state:

- 320 modern tests passing.
- Legacy tests with no collection and exit code 0.
- Ruff and `git diff --check` without errors.
