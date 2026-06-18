# autobook - Complete Project Study

> Historical reference: this study preserves an older reading of the project and
> may mention obsolete paths, commands and artifacts. For the current contract,
> start at `../INDICE.md`.

## Overview

Autonomous multi-agent pipeline for writing, revising, typesetting,
illustrating and narrating books with AI. Fork of NousResearch's
[autonovel](https://github.com/NousResearch/autonovel).

First produced book: "The Second Son of the House of Bells" (19 chapters, 79K
words) on the `bells` branch.

Locations:

- WSL: `/home/alessandro/dev/autobook`
- Windows: `D:\Dev\autobook`

## Entry Point

`run.py` was already described here as the unified CLI orchestrator:

```bash
uv run python run.py --pipeline [ideation|foundation|book_generation|editorial_revision] [--from-scratch] [--chapter CH_NUMS] [--yes]
```

## Architecture

Command/Composite pattern in `pipelines/base.py`:

- `Step`: atomic base class.
- `Pipeline`: composite step that runs a sequence of steps.

## Four Pipelines

### 1. Ideation (`pipelines/ideation.py`)

- Interactive console questionnaire.
- Generates three diverse concepts through the LLM.
- User selects one or provides custom input.
- Optionally generates the central mystery.
- Output: `seed.txt`, `book_data/MYSTERY.md`, `book_data/state.json`.

### 2. Foundation (`pipelines/foundation.py`)

Generates four structural bibles from `seed.txt`:

1. `world.md` - worldbuilding.
2. `characters.md` - wound/want/need/lie sheets, sliders and speech patterns.
3. `outline.md` - chapters with beats, try-fail cycles and foreshadowing ledger.
4. `canon.md` - fact database.

It also auto-commits through Git and initializes `state.json` with
`chapters_drafted: 0`.

### 3. Book Generation (`pipelines/book_generation.py`)

Generates chapters sequentially with four phases per chapter:

1. Modular beat generation: `DraftingAgent` writes each beat to
   `logs/tmp_draft/beat_NN_raw.md`, with sliding-window context and explicit
   current/next/future beat roadmap.
2. Independent critics: canon, style and flow critics inspect the unified raw
   chapter and support configurable critics through `AUTOBOOK_CRITICS`.
3. Sequential synthesis: `SynthesisAgent` applies corrections critique by
   critique and saves intermediate files.
4. Evaluation and self-healing: `evaluate_chapter()` scores the result,
   continuity verification runs, Git autosave protects progress, and the best
   attempt is kept when the threshold is not reached.

### 4. Editorial Revision (`pipelines/editorial_revision.py`)

- Human-directed revision through `book_data/editorial.md`.
- Self-healing corrective retry loop with five attempts and dynamic
  temperatures.

## Agents (`agents.py`)

The old study described a base `Agent` hierarchy plus an `AgentFactory`
singleton.

| Agent | Temp | Function |
| --- | --- | --- |
| `DraftingAgent` | 0.8 | Structural rough draft. |
| `StylistAgent` | 0.7 | Genre/tension refinement. |
| `TechnicalEditorAgent` | 0.3 | Lore consistency, anti-slop and PT-BR concerns. |
| `CanonCriticAgent` | 0.3 | Canon/lore audit. |
| `StyleCriticAgent` | 0.3 | Style and slop. |
| `FlowCriticAgent` | 0.3 | Pacing and transitions. |
| `SynthesisAgent` | 0.3 | Critique-based correction. |

Embedded system-prompt rules included lore consistency, POV/tone consistency,
PT-PT to PT-BR localization and anti-slop guardrails.

Skills under `skills/`:

- `create_agent.py`: `CustomLocalizerAgent`.
- `redundancy_detector.py`: repeated technical term detection.

## LLM Client (`llm.py`)

`call_llm()` unified Anthropic, OpenAI, Gemini and OpenRouter through `httpx`.

Historical notes:

- Model priority: override model, provider-specific environment value,
  `AUTOBOOK_*_MODEL`, then default.
- Max tokens differed between writing, judge and review roles.
- Retry used three attempts with exponential backoff and `Retry-After` support.
- OpenRouter used `HTTP-Referer` and `X-Title` headers and detected error
  payloads inside `200 OK`.
- Timeouts came from `AUTOBOOK_PIPELINE_TIMEOUT` and optional
  `AUTOBOOK_LLM_TIMEOUT`.

## Genre Strategy (`genre_strategy.py`)

The strategy pattern loaded `genres/{LANG}/{genre}.txt` with this hierarchy:

1. `genres/{LANG}/{genre}.txt`
2. `genres/EN/{genre}.txt`
3. `genres/{LANG}/drama.txt`
4. `genres/EN/drama.txt`

Existing genre folders were `genres/EN/` and `genres/PT-BR/`.

## Prompt Loader (`prompt_loader.py`)

Historical API notes:

- `load_prompt(name)`: loads `prompts/{LANG}/{name}`, with English fallback.
- `load_slop_config()`: loads `prompts/{LANG}/slop.json`.
- `load_genre_rules()`: wrapper around `GenreStrategy`.
- `load_slop_rules_instruction()`: formats `slop.json` as readable LLM
  instructions.

Prompt files included drafting, revision, continuity, editorial, directives and
slop configuration in PT-BR/EN.

## Anti-Slop (`slop.json`)

The JSON structure included:

- `tier1_banned`
- `tier2_suspicious`
- `tier3_filler`
- `transition_openers`
- `fiction_ai_tells`
- `structural_ai_tics`
- `telling_patterns`
- `instruction_templates`

## Evaluate (`evaluate.py`)

Historical modes:

- `--foundation`
- `--chapter=N`
- `--full`

Output: stdout plus `logs/eval_logs/{timestamp}.json`.

Mechanical slop included tier hits, em-dash density, sentence length variation,
transition opener ratio and a 0-10 slop penalty. The LLM judge used a separate
judge model to avoid self-congratulation.

## Voice Profile (`book_data/voice.md`)

Part 1 contained permanent guardrails such as banned words, suspicious clusters,
filler patterns, structural slop and a smell test.

Part 2 contained per-novel voice identity: tone, sentence rhythm, vocabulary,
POV/tense, dialogue conventions, exemplar passages and anti-exemplars.

At the time of the study, Part 2 was empty and represented by HTML comment
placeholders.

## Continuity Verification (`verify_continuity.py`)

The outline parser and LLM judge analyzed timeline, repetition, spatial
conflicts and broken transitions. Output was written to
`logs/eval_logs/continuity_*.json`.

## Project State At The Time

The study described `book_data/` as empty except for a complete Part 1
`voice.md`, and `chapters/` as empty except for `.gitkeep`. It concluded that
no book had yet been generated on that branch.

## Historical `.env` Shape

```env
AUTOBOOK_PROVIDER=openrouter
AUTOBOOK_PIPELINE_TIMEOUT=3600
AUTOBOOK_LOG_TRUNCATE_LIMIT=300
AUTOBOOK_LANGUAGE=PT-BR
AUTOBOOK_GENRE=drama
AUTOBOOK_WRITER_MODEL=openrouter/owl-alpha
AUTOBOOK_JUDGE_MODEL=nvidia/nemotron-3-super-120b-a12b:free,openrouter/owl-alpha,openrouter/free
AUTOBOOK_REVIEW_MODEL=nvidia/nemotron-3-super-120b-a12b:free
OPENROUTER_API_KEY=sk-or-v1-...
FAL_KEY=...
ELEVENLABS_API_KEY=...
```

## Dependencies

- Python >= 3.12
- `httpx`
- `python-dotenv`
- Installation through `uv sync`

## Tests

The historical study described about 40 tests across continuity, evaluate,
foundation, generation flow, ideation, integration, language support, LLM,
logging and typesetting.

Run command:

```bash
uv run --with pytest pytest tests/
```

## Legacy

Historical scripts from the original project included art/cover generation,
audiobook generation, seed generation, outline building, review, chapter draft,
batch drafts, reader panel, arc summary and art directions.

## Typeset

Historical typeset files included:

- `novel.tex`
- `chapters_content.tex`
- `build_tex.py`
- EPUB front/back/colophon/style/metadata files.

## Landing

The old study mentioned `index.html` as a book landing page.

## Workflows

Interactive full-book generation:

```bash
uv run python run.py --pipeline ideation
uv run python run.py --pipeline foundation
uv run python run.py --pipeline book_generation
uv run python run.py --pipeline editorial_revision
```

Autonomous book generation:

```bash
uv run python run.py --pipeline book_generation --from-scratch --yes
```

Specific chapter regeneration:

```bash
uv run python run.py --pipeline book_generation --chapter 5
uv run python run.py --pipeline book_generation --chapter 1-3,7
```

## Iteration Changelog Ideas

The study mentioned tracking evolution through historical attempt logs, arc
summary files, generation attempts, evaluation logs and pipeline logs.

## Design Notes

- Inspired by the `modify-evaluate-keep/discard` loop from
  karpathy/autoresearch.
- Sanderson's Laws for magic/systems.
- Save the Cat beats.
- Dan Harmon's Story Circle.
- MICE Quotient.
- LLM-as-judge with a separate model.
- Git autosave for progress protection.
