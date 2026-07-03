# Scripts

The main flow goes through `run.py`, but the repository contains auxiliary
scripts. They are classified to avoid confusing side tools with the central
contract.

## Classification

| Group | Rule |
| --- | --- |
| Supported | Used by pipelines or documented as an operational command. Must have tests and mocks. |
| Experimental | Useful for exploration, but does not block the main flow. |
| Historical | Kept for context; should not be expanded without an explicit decision. |

## Supported

| Script | Role |
| --- | --- |
| `run.py` | Main entry point: wizard and classic CLI. |
| `main.py` | Simple delegator to `run.main()`. |
| `evaluate.py` | Evaluation facade. |
| `verify_continuity.py` | Global continuity verification. |
| `resolve_continuity.py` | Converts continuity findings into an editorial flow through `run.py`. |
| `gen_revision.py` | Editorial rewrite used by `editorial_revision`. |
| `gen_brief.py` | Auxiliary brief generation when used manually. |
| `typeset/build_tex.py` | Generates `typeset/chapters_content.tex`. |
| `typeset/build_epub.py` | Generates `typeset/novel.epub` from chapters and metadata. |
| `typeset/build_final.py` | Generates final PDF/EPUB artifacts and guides external dependency installation. |

## Experimental Or Auxiliary

| Script | Role |
| --- | --- |
| `compare_chapters.py` | Compares chapter versions with an external prompt. |
| `adversarial_edit.py` | Suggests adversarial edits. |
| `apply_cuts.py` | Applies controlled editorial cuts. |
| `voice_fingerprint.py` | Extracts/prints a voice fingerprint. |
| `gen_audiobook_script.py` | Generates an audiobook script with optional cast. |

These scripts have initial hardening, but they should only become central
contracts if they receive documentation, tests and recurring usage in the main
flow.

## Historical

Files under `legacy/` preserve old implementations and are not part of the
modern baseline.

## Rules For New Scripts

- Use `encoding="utf-8"` for text reads/writes.
- Reuse `llm.py`, `prompt_loader.py` and `evaluation/json_utils.py` when
  applicable.
- Do not run destructive Git commands without a testable helper.
- Add tests without network, real LLM calls or real subprocesses when possible.
