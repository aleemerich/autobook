import shlex
import sys
from pathlib import Path
from typing import Any

from cli.discovery import discover_project_state
from pipelines.registry import list_pipelines

def _prompt_input(prompt: str, input_func: Any, stdout: Any) -> str:
    """Helper para obter input garantindo que o prompt seja capturado em stdouts customizados."""
    if stdout is not sys.stdout:
        print(prompt, end="", file=stdout)
        stdout.flush()
        if input_func is input:
            return input_func("")
    return input_func(prompt)

def main(base_dir: Path | None = None, stdout: Any = None, input_func: Any = None) -> None:
    """
    Inicializa a visualização do estado atual do projeto no Autobook Wizard.
    Apresenta informações sobre branch, pipelines, idiomas, gêneros e próximos passos recomendados,
    permitindo que o usuário escolha interativamente uma intenção para receber o comando clássico correspondente.
    """
    if stdout is None:
        stdout = sys.stdout
    if input_func is None:
        input_func = input

    # 1. Obter estado consolidado do projeto
    state = discover_project_state(base_dir)

    # 2. Imprimir cabeçalho e informações do Branch
    print("=== AUTOBOOK WIZARD ===", file=stdout)
    print(f"Branch atual: {state.current_branch}", file=stdout)
    if state.current_branch in ("main", "master"):
        print("Aviso: Voce esta no branch principal (main/master). Recomendamos criar um branch de feature.", file=stdout)

    # 3. Imprimir resumo do estado do livro
    print(file=stdout)
    print("--- Estado do Projeto ---", file=stdout)
    print(f"Semente (seed.txt): {'Presente' if state.has_seed else 'Ausente'}", file=stdout)
    print(f"Fundacao do livro: {'Completa' if state.foundation_complete else 'Incompleta'}", file=stdout)

    ch_list = ", ".join(str(n) for n in state.chapter_numbers) if state.chapter_numbers else "Nenhum"
    print(f"Capitulos gerados: {ch_list}", file=stdout)

    logs_list = ", ".join(state.logs_present) if state.logs_present else "Nenhum"
    print(f"Logs presentes: {logs_list}", file=stdout)

    artifacts_list = ", ".join(state.production_artifacts_present) if state.production_artifacts_present else "Nenhum"
    print(f"Artefatos de producao: {artifacts_list}", file=stdout)

    # 4. Listar pipelines disponíveis
    print(file=stdout)
    print("--- Pipelines Disponiveis ---", file=stdout)
    pipelines_spec = list_pipelines()
    for name in state.pipelines:
        spec = pipelines_spec.get(name)
        if spec:
            flags = []
            if spec.supports_chapter:
                flags.append("suporta --chapter")
            if spec.supports_from_scratch:
                flags.append("suporta --from-scratch")
            flags_str = f" ({', '.join(flags)})" if flags else ""
            print(f"- {spec.name}: {spec.description}{flags_str}", file=stdout)
        else:
            print(f"- {name}", file=stdout)

    # 5. Idiomas disponíveis (ordenados)
    print(file=stdout)
    languages_str = ", ".join(sorted(state.available_languages)) if state.available_languages else "Nenhum"
    print(f"Idiomas disponiveis: {languages_str}", file=stdout)

    # 6. Gêneros por idioma
    print(file=stdout)
    print("Generos por idioma:", file=stdout)
    if state.available_genres:
        for lang, genres in sorted(state.available_genres.items()):
            print(f"  - {lang}: {', '.join(sorted(genres))}", file=stdout)
    else:
        print("  Nenhum genero cadastrado.", file=stdout)

    # 7. Próximos passos recomendados
    print(file=stdout)
    print("--- Proximos Passos Recomendados ---", file=stdout)
    if state.recommended_next_steps:
        for step in state.recommended_next_steps:
            print(f"- {step}", file=stdout)
    else:
        print("- Nenhum passo recomendado no momento.", file=stdout)

    # 8. Exemplos de comandos equivalentes
    print(file=stdout)
    print("--- Exemplos de Comandos Classicos ---", file=stdout)
    print("Para executar um pipeline manualmente, use os seguintes comandos:", file=stdout)
    print("  python run.py --pipeline ideation", file=stdout)
    print("  python run.py --pipeline foundation", file=stdout)
    print("  python run.py --pipeline book_generation", file=stdout)
    print("  python run.py --pipeline book_generation --chapter 1", file=stdout)
    print("  python run.py --pipeline editorial_revision --chapter 1", file=stdout)

    # 9. Menu de Opções Interativas
    print(file=stdout)
    print("=== Menu de Opcoes ===", file=stdout)

    option_idx = 1
    option_mapping = {}

    if state.recommended_next_steps:
        print("[Passos Recomendados]", file=stdout)
        for step in state.recommended_next_steps:
            # Tenta mapear o passo para uma pipeline existente
            pipeline_candidate = step.split(" ")[0] if " " in step else step
            pipeline_name = None
            if pipeline_candidate in pipelines_spec:
                pipeline_name = pipeline_candidate

            print(f"[{option_idx}] [Recomendado] {step}", file=stdout)
            option_mapping[str(option_idx)] = {
                "type": "recommended",
                "pipeline": pipeline_name,
                "step": step
            }
            option_idx += 1

    print(f"[{option_idx}] Listar/usar qualquer pipeline disponivel", file=stdout)
    option_mapping[str(option_idx)] = {
        "type": "list_all"
    }
    option_idx += 1

    print("[0] Sair", file=stdout)

    try:
        user_choice = _prompt_input("Escolha uma opcao: ", input_func, stdout).strip()
    except (KeyboardInterrupt, EOFError):
        print(file=stdout)
        print("Saindo...", file=stdout)
        return

    if not user_choice or user_choice == "0":
        print("Saindo...", file=stdout)
        return

    if user_choice not in option_mapping:
        print(f"Erro: Opcao invalida '{user_choice}'", file=stdout)
        return

    choice = option_mapping[user_choice]
    selected_pipeline = None

    if choice["type"] == "recommended":
        if choice["pipeline"]:
            selected_pipeline = choice["pipeline"]
        else:
            print(f"O passo '{choice['step']}' nao corresponde a um pipeline direto.", file=stdout)
            return
    elif choice["type"] == "list_all":
        print(file=stdout)
        print("--- Selecione uma Pipeline ---", file=stdout)
        sub_idx = 1
        sub_mapping = {}
        for name in sorted(pipelines_spec.keys()):
            spec = pipelines_spec[name]
            print(f"[{sub_idx}] {spec.name}: {spec.description}", file=stdout)
            sub_mapping[str(sub_idx)] = spec.name
            sub_idx += 1
        print("[0] Voltar", file=stdout)

        try:
            sub_choice = _prompt_input("Escolha uma pipeline: ", input_func, stdout).strip()
        except (KeyboardInterrupt, EOFError):
            print(file=stdout)
            print("Saindo...", file=stdout)
            return

        if not sub_choice or sub_choice == "0":
            return

        if sub_choice not in sub_mapping:
            print(f"Erro: Opcao invalida '{sub_choice}'", file=stdout)
            return

        selected_pipeline = sub_mapping[sub_choice]

    if selected_pipeline:
        spec = pipelines_spec.get(selected_pipeline)
        if not spec:
            print(f"Erro: Pipeline '{selected_pipeline}' nao encontrada.", file=stdout)
            return

        cmd_args = []

        if spec.supports_from_scratch:
            try:
                from_scratch_resp = _prompt_input("Executar do zero? [s/N]: ", input_func, stdout).strip().lower()
            except (KeyboardInterrupt, EOFError):
                print(file=stdout)
                print("Saindo...", file=stdout)
                return
            if from_scratch_resp in ("s", "sim"):
                cmd_args.append("--from-scratch")

        if spec.supports_chapter:
            try:
                chapter_resp = _prompt_input("Capitulo(s), ex: 1 ou 1-3 (vazio para todos): ", input_func, stdout).strip()
            except (KeyboardInterrupt, EOFError):
                print(file=stdout)
                print("Saindo...", file=stdout)
                return
            if chapter_resp:
                cmd_args.append(f'--chapter {shlex.quote(chapter_resp)}')

        args_str = f" {' '.join(cmd_args)}" if cmd_args else ""
        print(file=stdout)
        print(f"Comando sugerido: python run.py --pipeline {selected_pipeline}{args_str}", file=stdout)
