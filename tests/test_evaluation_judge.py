from unittest.mock import patch

from evaluation.judge import call_judge


@patch("llm.call_llm")
def test_call_judge_delegates_to_unified_llm(mock_call_llm) -> None:
    """Valida que o juiz usa o cliente LLM unificado com papel de judge."""
    mock_call_llm.return_value = '{"overall_score": 8}'

    result = call_judge("Evaluate this", override_model="judge-model")

    assert result == '{"overall_score": 8}'
    mock_call_llm.assert_called_once()
    kwargs = mock_call_llm.call_args.kwargs
    assert kwargs["prompt"] == "Evaluate this"
    assert kwargs["temperature"] == 0.3
    assert kwargs["is_judge"] is True
    assert kwargs["override_model"] == "judge-model"
    assert "Always respond with valid JSON" in kwargs["system_prompt"]
    assert "Your first character must be '{'" in kwargs["system_prompt"]
    assert "return only the JSON object" in kwargs["system_prompt"]
