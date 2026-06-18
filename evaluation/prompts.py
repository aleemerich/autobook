"""Prompt templates used by evaluation workflows."""

from prompt_loader import load_prompt


def load_evaluation_prompt(prompt_name: str) -> str:
    """Load an evaluation prompt template from prompts/{LANG}/evaluation."""
    return load_prompt(f"evaluation/{prompt_name}.txt")


FOUNDATION_PROMPT = load_evaluation_prompt("foundation")
CHAPTER_PROMPT = load_evaluation_prompt("chapter")
CHAPTER_PROMPT_REDUCED = load_evaluation_prompt("chapter_reduced")
CHAPTER_PROMPT_MINIMAL = load_evaluation_prompt("chapter_minimal")
FULL_NOVEL_PROMPT = load_evaluation_prompt("full_novel")
