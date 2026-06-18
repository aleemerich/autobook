from typing import Any

from prompt_loader import load_prompt


def load_foundation_prompt(prompt_name: str) -> str:
    """Load a foundation prompt template from prompts/{LANG}/foundation."""
    return load_prompt(f"foundation/{prompt_name}.txt")


def render_foundation_prompt(prompt_name: str, values: dict[str, Any]) -> str:
    """Render known placeholders while leaving unrelated braces untouched."""
    prompt = load_foundation_prompt(prompt_name)
    for key, value in values.items():
        prompt = prompt.replace("{" + key + "}", str(value))
    return prompt
