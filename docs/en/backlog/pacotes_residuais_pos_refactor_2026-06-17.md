# Post-Refactor Residual Packages - 2026-06-17

This file records the residual backlog that came out of the senior code audit.
The original analysis documents were removed from the main tree; this summary
preserves the operational result without keeping broken references.

## Reference Validation

- `uv run --group dev ruff check .` without errors.
- `uv run --with pytest pytest tests -q` with 320 passing tests.
- `uv run --with pytest pytest legacy/tests -q` with no tests collected and exit code 0.

## Executed Packages

| Package | State | Result |
| --- | --- | --- |
| Package 1 | Completed | Functional breakages and operational noise addressed. |
| Package 2 | Completed | Additional modularization and hygiene in central areas. |
| Package 3 | Completed | Directly requested adjustments in scripts and flows. |
| Package 4 | Completed | Operational hardening and cleanup. |
| Package 5 | Completed | Final adjustments before residual packages. |
| Package 6 | Completed | Advanced editorial feedback and structured ingestion. |
| Package 7 | Completed | Additional contract and robustness adjustments. |
| Package 8 | Completed | Final comparison against the audit and cleanup. |

## Consolidated Result

| Topic | Current state |
| --- | --- |
| Main entry | `main.py` delegates to `run.main()`; `run.py` owns wizard and classic CLI. |
| Legacy tests | Outside the modern baseline, ignored in a controlled way. |
| Evaluation | `evaluate.py` acts as facade over `evaluation/`. |
| Prompts | Agent, foundation, evaluation and tool prompts live in `prompts/{LANG}/`. |
| Git | Operations go through `workspace/git.py` or testable workspace helpers. |
| Wizard | Decomposed into helpers and integrated with branch/workspace. |
| LLM | Configuration errors are typed and propagated. |
| Agents | Current strategy: modern adapter in `agent_system/` over `agents.py`. |
| Feedback | Critiques are converted to `CriticReport` and consolidated into `RevisionPlan`. |
| Tooling | `pyproject.toml` declares the `dev` group and gradual ruff config. |
| Scripts | Root scripts are classified as supported, experimental or historical. |

## Future Backlog

These items do not block the current refactor:

1. Promote or archive experimental scripts if they become part of the supported
   flow.
2. Expand native JSON output from critic agents.
3. Gradually expand lint coverage to currently excluded directories.
4. Improve terminal messages in peripheral scripts for consistent language and
   accent handling.
