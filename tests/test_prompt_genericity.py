from pathlib import Path

import pytest

import evaluate
import gen_revision
from workspace.project import write_workspace_metadata


BASE_DIR = Path(__file__).parent.parent.resolve()


PROMPT_FILES = [
    BASE_DIR / "prompts" / "EN" / "draft_chapter_user.txt",
    BASE_DIR / "prompts" / "PT-BR" / "draft_chapter_user.txt",
    BASE_DIR / "prompts" / "EN" / "gen_revision_user.txt",
    BASE_DIR / "prompts" / "PT-BR" / "gen_revision_user.txt",
]

FORBIDDEN_STORY_TERMS = [
    "The Second Son of the House of Bells",
    "Cass",
    "Bellwright",
    "Maret",
    "Eddan",
    "Perin",
    "Cantamura",
    "Tonal Law",
    "ECO-9",
    "Marina",
]


@pytest.mark.parametrize("prompt_path", PROMPT_FILES)
def test_operational_prompts_do_not_pin_specific_book_title(prompt_path: Path) -> None:
    content = prompt_path.read_text(encoding="utf-8")

    assert "The Second Son of the House of Bells" not in content
    assert "{book_title}" in content


@pytest.mark.parametrize(
    "prompt_path,format_args",
    [
        (
            BASE_DIR / "prompts" / "EN" / "draft_chapter_user.txt",
            {
                "chapter_num": 3,
                "book_title": "A Cidade de Vidro",
                "voice": "VOICE",
                "chapter_outline": "OUTLINE",
                "next_chapter": "NEXT",
                "prev_tail": "PREV",
                "world": "WORLD",
                "characters": "CHARACTERS",
                "genre_rules": "GENRE",
                "slop_rules": "SLOP",
            },
        ),
        (
            BASE_DIR / "prompts" / "PT-BR" / "draft_chapter_user.txt",
            {
                "chapter_num": 3,
                "book_title": "A Cidade de Vidro",
                "voice": "VOICE",
                "chapter_outline": "OUTLINE",
                "next_chapter": "NEXT",
                "prev_tail": "PREV",
                "world": "WORLD",
                "characters": "CHARACTERS",
                "genre_rules": "GENRE",
                "slop_rules": "SLOP",
            },
        ),
        (
            BASE_DIR / "prompts" / "EN" / "gen_revision_user.txt",
            {
                "ch_num": 3,
                "book_title": "A Cidade de Vidro",
                "brief": "BRIEF",
                "voice": "VOICE",
                "characters": "CHARACTERS",
                "world": "WORLD",
                "prev_tail": "PREV",
                "next_head": "NEXT",
                "old_text": "OLD",
                "genre_rules": "GENRE",
                "slop_rules": "SLOP",
            },
        ),
        (
            BASE_DIR / "prompts" / "PT-BR" / "gen_revision_user.txt",
            {
                "ch_num": 3,
                "book_title": "A Cidade de Vidro",
                "brief": "BRIEF",
                "voice": "VOICE",
                "characters": "CHARACTERS",
                "world": "WORLD",
                "prev_tail": "PREV",
                "next_head": "NEXT",
                "old_text": "OLD",
                "genre_rules": "GENRE",
                "slop_rules": "SLOP",
            },
        ),
    ],
)
def test_prompt_templates_format_with_book_title(
    prompt_path: Path,
    format_args: dict,
) -> None:
    content = prompt_path.read_text(encoding="utf-8")
    rendered = content.format(**format_args)

    assert "{book_title}" not in rendered
    assert "A Cidade de Vidro" in rendered


def test_load_book_title_uses_fallback_when_workspace_is_absent(tmp_path: Path) -> None:
    assert gen_revision._load_book_title(tmp_path) == "Untitled Book"


def test_load_book_title_uses_workspace_metadata(tmp_path: Path) -> None:
    write_workspace_metadata(
        "A Cidade de Vidro",
        "autobook/a-cidade-de-vidro",
        base_dir=tmp_path,
    )

    assert gen_revision._load_book_title(tmp_path) == "A Cidade de Vidro"


def test_foundation_and_evaluation_prompts_do_not_pin_story_terms() -> None:
    prompts = [
        evaluate.FOUNDATION_PROMPT,
        evaluate.CHAPTER_PROMPT,
        evaluate.CHAPTER_PROMPT_REDUCED,
        evaluate.CHAPTER_PROMPT_MINIMAL,
        evaluate.FULL_NOVEL_PROMPT,
    ]

    for prompt in prompts:
        for term in FORBIDDEN_STORY_TERMS:
            assert term not in prompt
