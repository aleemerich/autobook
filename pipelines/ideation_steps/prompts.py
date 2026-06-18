from prompt_loader import load_prompt


def load_ideation_prompt(prompt_name: str) -> str:
    """Load an ideation prompt template from prompts/{LANG}/ideation."""
    return load_prompt(f"ideation/{prompt_name}.txt")
