#!/usr/bin/env python3
"""
pipelines/ideation.py — Ideation Pipeline.
Allows interactive questionnaire and concept selection, generating seed.txt and MYSTERY.md.
"""

import json
from pathlib import Path
from typing import Dict, Any

from pipelines.base import Step, Pipeline
from llm import call_llm
from pipelines.ideation_steps import (
    select_concept_text,
    default_mystery_template,
    build_initial_ideation_state,
    load_ideation_prompt
)

BASE_DIR = Path(__file__).parent.parent.resolve()
BOOK_DATA_DIR = BASE_DIR / "book_data"
SEED_PATH = BASE_DIR / "seed.txt"
MYSTERY_PATH = BOOK_DATA_DIR / "MYSTERY.md"
STATE_FILE = BOOK_DATA_DIR / "state.json"

def _ideation_config(context: Dict[str, Any]) -> Dict[str, Any]:
    config = context.get("ideation", {})
    return config if isinstance(config, dict) else {}


def _context_answer(context: Dict[str, Any], key: str) -> Any:
    config = _ideation_config(context)
    if key in config:
        return config[key]
    return context.get(key)


def _answer_or_prompt(context: Dict[str, Any], key: str, prompt: str, default: str = "") -> str:
    answer = _context_answer(context, key)
    if answer is None:
        answer = input(prompt)
    answer = str(answer).strip()
    return answer or default


def _boolean_answer(context: Dict[str, Any], key: str, prompt: str, default: bool) -> bool:
    answer = _context_answer(context, key)
    if isinstance(answer, bool):
        return answer
    if answer is None:
        answer = input(prompt)
    normalized = str(answer).strip().upper()
    if not normalized:
        return default
    return normalized in {"S", "SIM", "Y", "YES", "TRUE", "1"}

class BypassOrRunStep(Step):
    def __init__(self):
        super().__init__("Check seed.txt existence and prompt bypass")

    def run(self, context: Dict[str, Any]) -> None:
        context["skip_ideation"] = False
        if SEED_PATH.exists():
            print(f"\n[Ideation] Um arquivo seed.txt já existe em {SEED_PATH}.")
            should_bypass = _boolean_answer(
                context,
                "bypass_existing_seed",
                "Deseja pular (bypass) a ideação e usar a semente existente? [S/N] (default: S): ",
                default=True
            )
            if should_bypass:
                print("[Ideation] Pulando fase de ideação. Semente existente será preservada.")
                context["skip_ideation"] = True

class QuestionnaireStep(Step):
    def __init__(self):
        super().__init__("Interactive Ideation Questionnaire")

    def run(self, context: Dict[str, Any]) -> None:
        if context.get("skip_ideation"):
            return
        
        print("\n--- QUESTIONÁRIO DE IDEAÇÃO INICIAL ---")
        print("Pressione Enter para usar o valor padrão ou insira sua preferência:")
        
        genre = _answer_or_prompt(
            context,
            "genre",
            "1. Gênero/Estilo (ex: Sci-fi noir, High fantasy) [default: Fantasy]: ",
            "Fantasy"
        )
        spark = _answer_or_prompt(
            context,
            "spark",
            "2. Centelha criativa (Spark - ideia central) [default: any]: ",
            "any"
        )
        cost = _answer_or_prompt(
            context,
            "cost",
            "3. Custo da magia/speculative element [default: physical toll]: ",
            "physical toll"
        )
        protagonist = _answer_or_prompt(
            context,
            "protagonist",
            "4. Protagonista (POV/Conflito) [default: scholar]: ",
            "scholar"
        )
        
        context["genre"] = genre
        context["spark"] = spark
        context["cost"] = cost
        context["protagonist"] = protagonist

class GenerateConceptsStep(Step):
    def __init__(self):
        super().__init__("Generate diverse concepts via LLM")

    def run(self, context: Dict[str, Any]) -> None:
        if context.get("skip_ideation"):
            return
        
        print("\n[Ideation] Solicitando ideias inovadoras ao LLM...")
        
        user_prompt = (
            f"Gere 3 conceitos de romance de fantasia/ficção científica baseados nos seguintes critérios:\n"
            f"- Gênero/Estilo: {context.get('genre')}\n"
            f"- Centelha Criativa (Spark): {context.get('spark')}\n"
            f"- Custo/Elemento especulativo: {context.get('cost')}\n"
            f"- Protagonista: {context.get('protagonist')}\n\n"
            f"{load_ideation_prompt('generate_concepts').format(count=3)}"
        )
        
        concepts = call_llm(
            prompt=user_prompt,
            system_prompt=load_ideation_prompt("concept_system"),
            temperature=1.0,
            is_judge=False
        )
        
        context["generated_concepts"] = concepts
        print("\n=== CONCEITOS GERADOS PELO LLM ===")
        print(concepts)

class SelectConceptStep(Step):
    def __init__(self):
        super().__init__("Select and save concept to seed.txt")

    def run(self, context: Dict[str, Any]) -> None:
        if context.get("skip_ideation"):
            return
        
        print("\n=== SELEÇÃO DE CONCEITO ===")
        print("Digite [1], [2] ou [3] para selecionar uma das opções acima.")
        print("Digite [C] para inserir um conceito inteiramente customizado.")
        
        choice = _answer_or_prompt(context, "concept_choice", "Opção desejada (1-3 ou C): ").upper()
        
        if choice in ["1", "2", "3"]:
            concepts_text = context.get("generated_concepts", "")
            selected_text = select_concept_text(concepts_text, choice)
            SEED_PATH.write_text(selected_text, encoding="utf-8")
            print(f"[Ideation] Semente do conceito {choice} salva com sucesso em {SEED_PATH}.")
        else:
            custom_seed = _answer_or_prompt(context, "custom_concept", "\nDigite/cole o seu próprio conceito completo:\n")
            if not custom_seed:
                custom_seed = "Conceito padrão vazio"
            SEED_PATH.write_text(custom_seed, encoding="utf-8")
            print(f"[Ideation] Semente customizada salva com sucesso em {SEED_PATH}.")

class MysteryGeneratorStep(Step):
    def __init__(self):
        super().__init__("Optionally generate central plot mystery")

    def run(self, context: Dict[str, Any]) -> None:
        if context.get("skip_ideation"):
            return
        
        print("\n=== MISTÉRIO CENTRAL ===")
        should_generate = _boolean_answer(
            context,
            "generate_mystery",
            "Deseja gerar a Bíblia de Mistérios (MYSTERY.md)? [S/N] (default: N): ",
            default=False
        )
        
        if should_generate:
            print("[Ideation] Gerando mistério central...")
            seed = SEED_PATH.read_text(encoding="utf-8")
            
            mystery_system = load_ideation_prompt("mystery_system")
            mystery_prompt = load_ideation_prompt("mystery_user").format(seed=seed)
            
            mystery_text = call_llm(
                prompt=mystery_prompt,
                system_prompt=mystery_system,
                temperature=0.7,
                is_judge=False
            )
            
            BOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)
            MYSTERY_PATH.write_text(mystery_text, encoding="utf-8")
            print(f"[Ideation] Bíblia de Mistérios salva em {MYSTERY_PATH}.")
        else:
            # Re-fill standard empty template if not generated
            if not MYSTERY_PATH.exists():
                MYSTERY_PATH.write_text(default_mystery_template(), encoding="utf-8")

class UpdateStateStep(Step):
    def __init__(self):
        super().__init__("Initialize book state in state.json")

    def run(self, context: Dict[str, Any]) -> None:
        BOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        state = build_initial_ideation_state()
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        print("[Ideation] state.json inicializado com sucesso.")


class IdeationPipeline(Pipeline):
    def __init__(self):
        super().__init__("Ideation Pipeline")
        self.add_step(BypassOrRunStep())
        self.add_step(QuestionnaireStep())
        self.add_step(GenerateConceptsStep())
        self.add_step(SelectConceptStep())
        self.add_step(MysteryGeneratorStep())
        self.add_step(UpdateStateStep())
