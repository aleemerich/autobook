# Genre Strategy

`genre_strategy.py` loads genre and language style rules from the `genres/`
folder.

## Inputs

Environment variables:

- `AUTOBOOK_LANGUAGE`: active language. Current values include `EN`, `PT-BR`.
- `AUTOBOOK_GENRE`: active genre. Existing examples include `drama`,
  `crime_mystery`, `cyber_horror`, `light_novel`.

Files:

- `genres/EN/*.txt`
- `genres/PT-BR/*.txt`

## Fallback

`GenreStrategy` tries to load in this order:

1. `genres/{AUTOBOOK_LANGUAGE}/{AUTOBOOK_GENRE}.txt`
2. `genres/EN/{AUTOBOOK_GENRE}.txt`
3. `genres/{AUTOBOOK_LANGUAGE}/drama.txt`
4. `genres/EN/drama.txt`

If no final file exists, it raises `FileNotFoundError`.

## Usage In Code

`prompt_loader.load_genre_rules()` instantiates `GenreStrategy` and returns the
full style guidelines. The generation pipeline uses these rules when
instantiating agents and building prompts.

## Relevant API

- `get_style_guidelines()`: returns the full loaded rules.
- `get_anti_patterns()`: tries to extract lines from sections named
  `PADROES A EVITAR` or `PATTERNS TO AVOID`.

## Current State

Functional and covered indirectly by language, prompt and pipeline tests. The
most useful future improvement is standardizing the internal editorial contract
of each genre file, but this does not block the current flow.
