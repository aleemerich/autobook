# Typesetting

Typesetting is still an auxiliary step, not a registered main pipeline. The
supported script is:

```bash
uv run python typeset/build_tex.py
```

It reads chapters from `chapters/` and generates:

```text
typeset/chapters_content.tex
```

## Flow

```mermaid
flowchart LR
    Chapters["chapters/ch_XX.md"] --> Script["typeset/build_tex.py"]
    Script --> Tex["typeset/chapters_content.tex"]
    Tex --> External["external PDF/EPUB tools"]
```

## Current State

- LaTeX content generation is supported.
- Final PDF/EPUB production depends on external tools and is not guaranteed by
  an Autobook pipeline.
- Test artifacts that existed in this folder were removed from operational
  documentation.

## Evolution Rules

- If PDF/EPUB becomes a contract, create a documented pipeline or command.
- Add tests for complex markdown, accents, empty chapters and file order.
- Do not mix final artifact generation with narrative generation in the same
  step.
