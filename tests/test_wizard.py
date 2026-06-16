import io
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import run
from cli.wizard import main as wizard_main
from cli.discovery import ProjectState
from pipelines.registry import PipelineSpec

class SequenceInput:
    def __init__(self, responses):
        self.responses = list(responses)
        self.index = 0

    def __call__(self, prompt):
        if self.index < len(self.responses):
            val = self.responses[self.index]
            self.index += 1
            return val
        return ""

@pytest.fixture
def mock_project_state() -> ProjectState:
    return ProjectState(
        current_branch="feature/wizard-test",
        pipelines=["ideation", "book_generation"],
        available_languages=["PT-BR", "EN"],
        available_genres={"PT-BR": ["mystery", "fantasy"]},
        has_seed=True,
        book_data_files=["world.md", "characters.md"],
        foundation_complete=False,
        chapter_numbers=[1],
        logs_present=["step_ideation.log"],
        production_artifacts_present=[],
        recommended_next_steps=["foundation"]
    )

@pytest.fixture
def mock_pipelines_spec() -> dict:
    return {
        "ideation": PipelineSpec(
            name="ideation",
            description="Ideation description",
            factory=MagicMock(),
            supports_chapter=False,
            supports_from_scratch=True,
            requires_work_branch=True,
        ),
        "book_generation": PipelineSpec(
            name="book_generation",
            description="Generation description",
            factory=MagicMock(),
            supports_chapter=True,
            supports_from_scratch=True,
            requires_work_branch=False,
        ),
        "foundation": PipelineSpec(
            name="foundation",
            description="Foundation description",
            factory=MagicMock(),
            supports_chapter=False,
            supports_from_scratch=True,
            requires_work_branch=True,
        )
    }

@pytest.fixture(autouse=True)
def mock_load_workspace_metadata():
    with patch("cli.wizard.load_workspace_metadata", return_value=None) as mock_load:
        yield mock_load

def test_wizard_prints_branch_and_general_info(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard imprime o branch atual e os dados gerais corretamente."""
    stdout_stream = io.StringIO()
    input_func = lambda _: ""
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    
    # 1. Verifica branch atual
    assert "Branch atual: feature/wizard-test" in output
    # Não deve imprimir aviso de branch principal
    assert "Aviso: Voce esta no branch principal" not in output
    
    # 2. Verifica dados gerais do estado do livro
    assert "Semente (seed.txt): Presente" in output
    assert "Fundacao do livro: Incompleta" in output
    assert "Capitulos gerados: 1" in output
    assert "Logs presentes: step_ideation.log" in output

def test_wizard_warning_on_main_branch(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard imprime aviso se o branch atual for main ou master."""
    input_func = lambda _: ""
    for branch_name in ("main", "master"):
        mock_project_state.current_branch = branch_name
        stdout_stream = io.StringIO()
        
        with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
            with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
                wizard_main(stdout=stdout_stream, input_func=input_func)
                
        output = stdout_stream.getvalue()
        assert f"Branch atual: {branch_name}" in output
        assert "Aviso: Voce esta no branch principal (main/master)." in output

def test_wizard_lists_pipelines_correctly(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard lista pipelines com flags e descricoes."""
    stdout_stream = io.StringIO()
    input_func = lambda _: ""
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    
    assert "--- Pipelines Disponiveis ---" in output
    assert "- ideation: Ideation description (suporta --from-scratch, requer branch de obra)" in output
    assert "- book_generation: Generation description (suporta --chapter, suporta --from-scratch)" in output

def test_wizard_lists_languages_and_genres(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard lista os idiomas e generos por idioma."""
    stdout_stream = io.StringIO()
    input_func = lambda _: ""
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    
    assert "Idiomas disponiveis: EN, PT-BR" in output
    assert "Generos por idioma:" in output
    assert "  - PT-BR: fantasy, mystery" in output

def test_wizard_shows_recommended_next_steps(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard exibe os proximos passos recomendados."""
    stdout_stream = io.StringIO()
    input_func = lambda _: ""
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    
    assert "--- Proximos Passos Recomendados ---" in output
    assert "- foundation" in output

def test_wizard_does_not_execute_pipelines(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard e apenas leitura e nao instancia nem roda nenhuma pipeline."""
    stdout_stream = io.StringIO()
    input_func = lambda _: ""
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    # As fabricas dos pipelines nao devem ser chamadas (o factory e um MagicMock)
    mock_pipelines_spec["ideation"].factory.assert_not_called()
    mock_pipelines_spec["book_generation"].factory.assert_not_called()

def test_run_main_empty_args_calls_wizard(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que run.main([]) invoca o wizard e nao dispara erros."""
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.main") as mock_wizard_main:
                run.main([])
                mock_wizard_main.assert_called_once()

def test_run_main_with_args_goes_to_classic_pipeline(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que run.main com argumentos executa a pipeline diretamente via registry."""
    with patch("run.get_pipeline_spec") as mock_get_spec:
        mock_spec = MagicMock()
        mock_spec.requires_work_branch = False
        mock_get_spec.return_value = mock_spec

        with patch("cli.wizard.main") as mock_wizard_main:
            run.main(["--pipeline", "book_generation"])

            mock_wizard_main.assert_not_called()
            mock_get_spec.assert_called_once_with("book_generation")
            mock_spec.factory.return_value.run.assert_called_once()

# --- Novos testes do incremento interativo ---

def test_wizard_empty_input_exits(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que entrada vazia sai do wizard sem sugerir comando."""
    stdout_stream = io.StringIO()
    input_func = SequenceInput([""])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    assert "Saindo..." in output
    assert "Comando sugerido:" not in output

def test_wizard_exit_option_exits(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que opcao 0 sai do wizard sem sugerir comando."""
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["0"])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    assert "Saindo..." in output
    assert "Comando sugerido:" not in output

def test_wizard_invalid_option(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que opcao invalida exibe erro e nao sugere comando."""
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["99"])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    assert "Erro: Opcao invalida '99'" in output
    assert "Comando sugerido:" not in output

def test_wizard_recommended_step_suggests_command(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que escolher proximo passo recomendado imprime comando correspondente."""
    # O mock_project_state recomenda "foundation", que mapeia para a pipeline "foundation".
    # Menu recomendara: [1] [Recomendado] foundation.
    # Responderemos "1" (opcao recomendada) e depois "n" (executar do zero? nao).
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["1", "n"])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    suggested_line = [line for line in output.splitlines() if "Comando sugerido:" in line][0]
    assert "Comando sugerido: python run.py --pipeline foundation" in suggested_line
    assert "--from-scratch" not in suggested_line

def test_wizard_from_scratch_flag(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que escolher pipeline e responder 's' para from-scratch adiciona a flag no comando."""
    # Selecionamos a opcao recomendada [1] ("foundation") e respondemos "s" (do zero: sim).
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["1", "s"])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    assert "Comando sugerido: python run.py --pipeline foundation --from-scratch" in output

def test_wizard_chapter_flag(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que escolher pipeline e informar capitulo adiciona --chapter no comando."""
    # Vamos recomendar "book_generation" para testar capitulos.
    mock_project_state.recommended_next_steps = ["book_generation"]
    # Selecionamos a opcao recomendada [1] ("book_generation")
    # Respondemos "n" para from-scratch, e "3" para capitulo.
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["1", "n", "3"])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    assert 'Comando sugerido: python run.py --pipeline book_generation --chapter 3' in output

def test_wizard_list_all_pipelines_flow(mock_project_state, mock_pipelines_spec) -> None:
    """Valida o fluxo de listar todas as pipelines e selecionar uma delas."""
    # No menu principal, "Listar/usar qualquer pipeline disponivel" sera a opcao [2] (ja que so ha 1 recomendacao).
    # No sub-menu, as pipelines disponiveis ordenadas sao: "book_generation", "foundation", "ideation".
    # Escolheremos a opcao [1] ("book_generation" no sub-menu).
    # Respondemos "s" para from-scratch e "5-7" para capitulo.
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["2", "1", "s", "5-7"])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    assert "--- Selecione uma Pipeline ---" in output
    assert 'Comando sugerido: python run.py --pipeline book_generation --from-scratch --chapter 5-7' in output

def test_wizard_chapter_flag_escaping(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que valores de capitulo com espacos ou aspas sao escapados com seguranca usando shlex."""
    import shlex
    
    # Caso 1: Espaços "1, 3" -> deve virar --chapter '1, 3'
    mock_project_state.recommended_next_steps = ["book_generation"]
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["1", "n", "1, 3"])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)
            
    output = stdout_stream.getvalue()
    expected_val = shlex.quote("1, 3")
    assert f"Comando sugerido: python run.py --pipeline book_generation --chapter {expected_val}" in output

    # Caso 2: Aspas 'capitulo "especial"' -> deve virar escape correto
    stdout_stream_2 = io.StringIO()
    input_func_2 = SequenceInput(["1", "n", 'capitulo "especial"'])
    
    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream_2, input_func=input_func_2)
            
    output_2 = stdout_stream_2.getvalue()
    expected_val_2 = shlex.quote('capitulo "especial"')
    assert f"Comando sugerido: python run.py --pipeline book_generation --chapter {expected_val_2}" in output_2

def test_wizard_branch_prep_accepted_but_not_created(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard sugere branch e comando se o usuario aceitar preparar mas nao criar."""
    mock_project_state.current_branch = "main"
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["s", "O Meu Fantastico Livro", "n", "0"])

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.create_book_branch") as mock_create:
                with patch("cli.wizard.write_workspace_metadata") as mock_write:
                    wizard_main(stdout=stdout_stream, input_func=input_func)
                    mock_create.assert_not_called()
                    mock_write.assert_not_called()

    output = stdout_stream.getvalue()
    assert "Deseja preparar uma branch de obra agora? [s/N]:" in output
    assert "Titulo ou slug da obra:" in output
    assert "Branch sugerida: autobook/o-meu-fantastico-livro" in output
    assert "Comando sugerido: git switch -c autobook/o-meu-fantastico-livro" in output
    assert "Criar esta branch agora? [s/N]:" in output
    assert "Branch criada:" not in output
    assert "Saindo..." in output

def test_wizard_branch_creation_accepted(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que quando o usuario aceita criar a branch, create_book_branch e write_workspace_metadata sao chamados."""
    mock_project_state.current_branch = "main"
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["s", "O Meu Fantastico Livro", "s", "0"])

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.create_book_branch", return_value="autobook/o-meu-fantastico-livro") as mock_create:
                with patch("cli.wizard.write_workspace_metadata") as mock_write:
                    wizard_main(stdout=stdout_stream, input_func=input_func)
                    mock_create.assert_called_once_with("O Meu Fantastico Livro")
                    mock_write.assert_called_once_with(title="O Meu Fantastico Livro", branch="autobook/o-meu-fantastico-livro", base_dir=None)

    output = stdout_stream.getvalue()
    assert "Branch criada: autobook/o-meu-fantastico-livro" in output
    assert "Workspace registrado em: book_data/workspace.json" in output
    assert "Saindo..." in output

def test_wizard_branch_creation_write_metadata_failure(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que erros ao escrever os metadados do workspace sao tratados amigavelmente."""
    mock_project_state.current_branch = "main"
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["s", "O Meu Fantastico Livro", "s", "0"])

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.create_book_branch", return_value="autobook/o-meu-fantastico-livro") as mock_create:
                with patch("cli.wizard.write_workspace_metadata", side_effect=OSError("Falha de I/O simulada")) as mock_write:
                    wizard_main(stdout=stdout_stream, input_func=input_func)
                    mock_create.assert_called_once()
                    mock_write.assert_called_once()

    output = stdout_stream.getvalue()
    assert "Branch criada: autobook/o-meu-fantastico-livro" in output
    assert "Erro: Falha de I/O simulada" in output
    assert "Saindo..." in output

def test_wizard_branch_creation_error_handling(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que erros de criacao da branch impedem a escrita de metadados e sao capturados amigavelmente."""
    mock_project_state.current_branch = "main"
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["s", "O Meu Fantastico Livro", "s", "0"])

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.create_book_branch", side_effect=ValueError("Worktree sujo de teste")) as mock_create:
                with patch("cli.wizard.write_workspace_metadata") as mock_write:
                    wizard_main(stdout=stdout_stream, input_func=input_func)
                    mock_create.assert_called_once_with("O Meu Fantastico Livro")
                    mock_write.assert_not_called()

    output = stdout_stream.getvalue()
    assert "Erro: Worktree sujo de teste" in output
    assert "Workspace registrado em:" not in output
    assert "Saindo..." in output

def test_wizard_branch_prep_declined(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard nao sugere branch, nao cria e nao grava metadados se o usuario recusar a preparacao no main."""
    mock_project_state.current_branch = "main"
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["n", "0"])

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.create_book_branch") as mock_create:
                with patch("cli.wizard.write_workspace_metadata") as mock_write:
                    wizard_main(stdout=stdout_stream, input_func=input_func)
                    mock_create.assert_not_called()
                    mock_write.assert_not_called()

    output = stdout_stream.getvalue()
    assert "Deseja preparar uma branch de obra agora? [s/N]:" in output
    assert "Titulo ou slug da obra:" not in output
    assert "Branch sugerida:" not in output
    assert "git switch -c" not in output
    assert "Saindo..." in output

def test_wizard_branch_prep_invalid_title(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard exibe erro simples se o titulo for invalido, nao cria branch e nao grava metadados."""
    mock_project_state.current_branch = "main"
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["s", "???", "0"])

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.create_book_branch") as mock_create:
                with patch("cli.wizard.write_workspace_metadata") as mock_write:
                    wizard_main(stdout=stdout_stream, input_func=input_func)
                    mock_create.assert_not_called()
                    mock_write.assert_not_called()

    output = stdout_stream.getvalue()
    assert "Deseja preparar uma branch de obra agora? [s/N]:" in output
    assert "Titulo ou slug da obra:" in output
    assert "Erro: O título ou slug '???' resultou em um nome de branch vazio inválido." in output
    assert "Saindo..." in output

def test_wizard_branch_prep_not_on_main(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que o wizard nao pergunta preparacao de branch, nao cria e nao grava metadados se nao estiver no main/master."""
    mock_project_state.current_branch = "feature/my-own-branch"
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["0"])

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("cli.wizard.create_book_branch") as mock_create:
                with patch("cli.wizard.write_workspace_metadata") as mock_write:
                    wizard_main(stdout=stdout_stream, input_func=input_func)
                    mock_create.assert_not_called()
                    mock_write.assert_not_called()

    output = stdout_stream.getvalue()
    assert "Deseja preparar uma branch de obra agora?" not in output
    assert "Saindo..." in output

def test_wizard_workspace_absent(mock_project_state, mock_pipelines_spec, mock_load_workspace_metadata) -> None:
    """Valida que o wizard exibe Workspace registrado: Nenhum quando ausente."""
    mock_load_workspace_metadata.return_value = None
    stdout_stream = io.StringIO()
    input_func = lambda _: ""

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)

    output = stdout_stream.getvalue()
    assert "Workspace registrado: Nenhum" in output

def test_wizard_workspace_valid(mock_project_state, mock_pipelines_spec, mock_load_workspace_metadata) -> None:
    """Valida que o wizard exibe titulo e branch do workspace se existir e for valido."""
    mock_load_workspace_metadata.return_value = {
        "title": "O Senhor dos Aneis",
        "branch": "autobook/o-senhor-dos-aneis",
        "created_at": "2026-06-16T10:00:00",
        "schema_version": 1
    }
    stdout_stream = io.StringIO()
    input_func = lambda _: ""

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)

    output = stdout_stream.getvalue()
    assert "Obra registrada: O Senhor dos Aneis" in output
    assert "Branch da obra: autobook/o-senhor-dos-aneis" in output

def test_wizard_workspace_invalid(mock_project_state, mock_pipelines_spec, mock_load_workspace_metadata) -> None:
    """Valida que o wizard exibe aviso amigavel quando workspace.json for invalido e continua exibindo menu."""
    mock_load_workspace_metadata.side_effect = ValueError("schema_version invalido")
    stdout_stream = io.StringIO()
    input_func = SequenceInput(["0"]) # Sair do menu de opções

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            wizard_main(stdout=stdout_stream, input_func=input_func)

    output = stdout_stream.getvalue()
    assert "Aviso: workspace.json invalido: schema_version invalido" in output
    assert "=== Menu de Opcoes ===" in output
    assert "Saindo..." in output


# --- Testes de execucao opcional de pipelines pelo wizard ---

def test_wizard_execution_declined(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que quando o usuario recusa a execucao, run.main nao e chamado."""
    input_func = SequenceInput(["1", "n", "n"])
    stdout_stream = io.StringIO()

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("run.main") as mock_run_main:
                wizard_main(stdout=stdout_stream, input_func=input_func)
                mock_run_main.assert_not_called()

    output = stdout_stream.getvalue()
    assert "Executando pipeline..." not in output


def test_wizard_execution_accepted_simple(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que quando o usuario aceita a execucao, run.main e chamado com argv basico."""
    input_func = SequenceInput(["1", "n", "s"])
    stdout_stream = io.StringIO()

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("run.main") as mock_run_main:
                wizard_main(stdout=stdout_stream, input_func=input_func)
                mock_run_main.assert_called_once_with(["--pipeline", "foundation"])

    output = stdout_stream.getvalue()
    assert "Executando pipeline..." in output


def test_wizard_execution_accepted_with_flags(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que argv e montado corretamente com --from-scratch e --chapter preservando valores originais."""
    input_func = SequenceInput(["2", "1", "s", "1-3, 5", "s"])
    stdout_stream = io.StringIO()

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("run.main") as mock_run_main:
                wizard_main(stdout=stdout_stream, input_func=input_func)
                mock_run_main.assert_called_once_with([
                    "--pipeline", "book_generation",
                    "--from-scratch",
                    "--chapter", "1-3, 5"
                ])

    output = stdout_stream.getvalue()
    assert "Comando sugerido: python run.py --pipeline book_generation --from-scratch --chapter" in output
    assert "Executando pipeline..." in output


def test_wizard_execution_system_exit_handling(mock_project_state, mock_pipelines_spec) -> None:
    """Valida que se run.main levanta SystemExit(1), o wizard imprime mensagem amigavel sem estourar traceback."""
    input_func = SequenceInput(["1", "n", "s"])
    stdout_stream = io.StringIO()

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("run.main", side_effect=SystemExit(1)):
                wizard_main(stdout=stdout_stream, input_func=input_func)

    output = stdout_stream.getvalue()
    assert "Executando pipeline..." in output
    assert "Execucao abortada com codigo 1." in output


def test_wizard_execution_factories_not_called_directly(mock_project_state, mock_pipelines_spec) -> None:
    """Garante que as fabricas de pipelines do registry continuam nao sendo chamadas diretamente pelo wizard."""
    input_func = SequenceInput(["1", "n", "s"])
    stdout_stream = io.StringIO()

    with patch("cli.wizard.discover_project_state", return_value=mock_project_state):
        with patch("cli.wizard.list_pipelines", return_value=mock_pipelines_spec):
            with patch("run.main") as mock_run_main:
                wizard_main(stdout=stdout_stream, input_func=input_func)
                mock_run_main.assert_called_once()

    mock_pipelines_spec["foundation"].factory.assert_not_called()
