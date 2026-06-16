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
        with patch("run.get_pipeline_spec") as mock_get_spec:
            mock_spec = MagicMock()
            mock_spec.requires_work_branch = False
            mock_get_spec.return_value = mock_spec
            
            run.main(["--pipeline", "ideation"])
            
            mock_wizard_main.assert_not_called()
            mock_get_spec.assert_called_once_with("ideation")
            mock_spec.factory.return_value.run.assert_called_once()

def test_run_chapter_argument_is_parsed() -> None:
    """Valida que argumentos opcionais como --chapter são processados e injetados no context."""
    with patch("run.get_pipeline_spec") as mock_get_spec:
        mock_spec = MagicMock()
        mock_spec.requires_work_branch = False
        mock_get_spec.return_value = mock_spec
        
        run.main(["--pipeline", "book_generation", "--chapter", "1,2"])
        
        mock_get_spec.assert_called_once_with("book_generation")
        mock_spec.factory.return_value.run.assert_called_once()
        
        called_context = mock_spec.factory.return_value.run.call_args[0][0]
        assert called_context["chapters"] == [1, 2]

def test_invalid_argument_raises_system_exit() -> None:
    """Valida que argumentos inválidos disparam a falha do argparse (SystemExit)."""
    with pytest.raises(SystemExit):
        run.main(["--invalid-argument"])

def test_run_pipeline_requires_branch_and_passes() -> None:
    """Valida que ensure_not_main_for_generation é chamado e a execução continua se a branch for válida."""
    with patch("run.get_pipeline_spec") as mock_get_spec:
        mock_spec = MagicMock()
        mock_spec.requires_work_branch = True
        mock_get_spec.return_value = mock_spec

        with patch("workspace.branching.ensure_not_main_for_generation") as mock_ensure:
            run.main(["--pipeline", "book_generation"])

            mock_ensure.assert_called_once()
            mock_spec.factory.return_value.run.assert_called_once()

def test_run_pipeline_requires_branch_and_fails() -> None:
    """Valida que se ensure_not_main_for_generation falhar, a execução aborta com SystemExit(1) e não roda pipeline."""
    with patch("run.get_pipeline_spec") as mock_get_spec:
        mock_spec = MagicMock()
        mock_spec.requires_work_branch = True
        mock_get_spec.return_value = mock_spec

        with patch("workspace.branching.ensure_not_main_for_generation", side_effect=ValueError("Branch principal nao permitida")):
            with patch("sys.stderr", new_callable=MagicMock) as mock_stderr:
                with pytest.raises(SystemExit) as excinfo:
                    run.main(["--pipeline", "book_generation"])

                assert excinfo.value.code == 1
                # A fábrica e o run não devem ser chamados
                mock_spec.factory.assert_not_called()
                mock_spec.factory.return_value.run.assert_not_called()
