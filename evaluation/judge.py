def call_judge(prompt, max_tokens=2000, override_model=None):
    """Call the unified judge LLM via llm.py and return response text."""
    from llm import call_llm
    system = ("You are a literary critic and novel editor. "
              "You evaluate fiction with precision. Always respond with valid JSON. "
              "No markdown fences, no preamble -- just the JSON object.")
    return call_llm(prompt=prompt, system_prompt=system, temperature=0.3, is_judge=True, override_model=override_model)
