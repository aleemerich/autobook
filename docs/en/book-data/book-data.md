# Book Data (`book_data/`)

`book_data/` stores state, planning and reference files used by the pipelines.
They are runtime data for the current book and should not be treated as content
versioned on the main branch.

In the main repository, `book_data/` is versioned only with `.gitkeep`. Real
files are ignored by Git and should be created on `autobook/<slug>` branches.
Versioned bootstrap templates live in `templates/book_data/`.

## Files

| File | Generated/Used By | Role |
| --- | --- | --- |
| `state.json` | `ideation`, `foundation`, `book_generation` | Pipeline cursor, including `chapters_drafted`, `phase` and `current_focus`. |
| `MYSTERY.md` | `ideation`, `foundation` | Optional central mystery, used while building the outline. |
| `world.md` | `foundation`, `book_generation`, evaluation | World bible and environment rules. |
| `characters.md` | `foundation`, `book_generation`, evaluation | Character registry, relationships and voice patterns. |
| `outline.md` | `foundation`, `book_generation`, continuity | Chapter and beat structure. |
| `canon.md` | `foundation`, `book_generation`, evaluation | Established facts that must not be contradicted. |
| `voice.md` | `foundation`, `book_generation`, evaluation | Voice profile and stylistic constraints. |
| `editorial.md` | `editorial_revision`, `resolve_continuity.py` | General and per-chapter revision briefs. |
| `workspace.json` | Wizard, auxiliary scripts | Local book metadata, including title and `autobook/<slug>` branch. |
| `audiobook_cast.json` | `gen_audiobook_script.py` | Optional voice/cast descriptions for audiobook script parsing. |

## Lifecycle

1. `ideation` creates `seed.txt`, optionally `MYSTERY.md`, and initializes `state.json`.
2. `foundation` reads `seed.txt`, `MYSTERY.md` and `voice.md`; generates `world.md`, `characters.md`, `outline.md` and `canon.md`.
3. `book_generation` reads `outline.md`, `world.md`, `characters.md`, `canon.md` and `voice.md`; writes chapters and updates `state.json`.
4. `editorial_revision` reads `editorial.md` and existing chapters; rewrites selected chapters.
5. `evaluate.py` and `verify_continuity.py` read these files to produce scores and diagnostics.

## Practical Contracts

- `outline.md` must contain chapter headers recognized by the parsers, such as
  `### Ch 1: Title`, in continuous sequence starting at 1.
- `book_generation` no longer uses a fixed fallback chapter count; if no
  recognizable chapter header is found, execution fails explicitly.
- `world.md`, `characters.md`, `canon.md` and `voice.md` are required inputs
  for `book_generation`; missing files interrupt the flow instead of becoming
  empty context.
- `book_generation` searches for the `**Beats:**` section to generate scenes
  modularly; without beats, it falls back to a full chapter draft.
- `state.json` controls where sequential generation resumes.
- `editorial.md` may contain general and per-chapter directives; the semantic
  parser tries to convert this to JSON and has a regex fallback.
- `workspace.json` is optional, but when it exists it must follow the schema
  validated by `workspace/project.py`: `schema_version` 1, `title`, branch in
  `autobook/<slug>` format and ISO 8601 `created_at`.
- `audiobook_cast.json` is optional. When absent, the audiobook script uses a
  generic narrator; when present, it must be a JSON object
  `{ "SPEAKER": "voice description" }`.
- The wizard initializes templates from `templates/book_data/` without
  overwriting existing local files.
- Even though `book_data/*`, `seed.txt` and `chapters/*.md` are ignored by
  default, pipelines use controlled `git add --force` through `workspace/git.py`
  to explicitly register these artifacts on book branches.

## Care

- `book_data/` is the book workspace. On main branches it should contain only
  `.gitkeep`; real artifacts should be generated on `autobook/<slug>` branches.
- Editing `state.json` manually may make the pipeline skip or overwrite
  chapters.
- `foundation.py` looks for the craft reference at `docs/en/others/CRAFT.md`.
