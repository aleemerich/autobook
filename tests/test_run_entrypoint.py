import pytest
from unittest.mock import patch, MagicMock
import run

def test_run_without_arguments_calls_wizard() -> None:
    """Valida que chamar run.main com argv vazio redireciona para o stub do wizard."""
    with patch("cli.wizard.main") as mock_wizard_main:
        run.main([])
        mock_wizard_main.assert_called_once()

def test_run_with_arguments_does_not_call_wizard() -> None:
    """Valida que chamadas com argumentos válidos não disparam o wizard e chamam o registry."""
    with patch("cli.wizard.main") as mock_wizard_main:
        with patch("run.get_pipeline") as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_get_pipeline.return_value = mock_pipeline
            
            run.main(["--pipeline", "ideation"])
            
            mock_wizard_main.assert_not_called()
            mock_get_pipeline.assert_called_once_with("ideation")
            mock_pipeline.run.assert_called_once()

def test_run_chapter_argument_is_parsed() -> None:
    """Valida que argumentos opcionais como --chapter são processados e injetados no context."""
    with patch("run.get_pipeline") as mock_get_pipeline:
        mock_pipeline = MagicMock()
        mock_get_pipeline.return_value = mock_pipeline
        
        run.main(["--pipeline", "book_generation", "--chapter", "1,2"])
        
        mock_get_pipeline.assert_called_once_with("book_generation")
        mock_pipeline.run.assert_called_once()
        
        called_context = mock_pipeline.run.call_args[0][0]
        assert called_context["chapters"] == [1, 2]

def test_invalid_argument_raises_system_exit() -> None:
    """Valida que argumentos inválidos disparam a falha do argparse (SystemExit)."""
    with pytest.raises(SystemExit):
        run.main(["--invalid-argument"])
