#!/usr/bin/env python3
"""
pipelines/ideation.py — Ideation Pipeline.
Allows interactive questionnaire and concept selection, generating seed.txt and MYSTERY.md.
"""

import re
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any

from pipelines.base import Step, Pipeline
from llm import call_llm

BASE_DIR = Path(__file__).parent.parent.resolve()
BOOK_DATA_DIR = BASE_DIR / "book_data"
SEED_PATH = BASE_DIR / "seed.txt"
MYSTERY_PATH = BOOK_DATA_DIR / "MYSTERY.md"
STATE_FILE = BOOK_DATA_DIR / "state.json"

SYSTEM_PROMPT = (
    "You are a fantasy novelist with deep knowledge of the genre's "
    "best works -- Tolkien, Le Guin, Rothfuss, Wolfe, Jemisin, Peake, "
    "Susanna Clarke, Andrew Peterson, Sofia Samatar. You generate "
    "novel concepts that are SPECIFIC, SURPRISING, and STRUCTURALLY "
    "SOUND. You never propose generic medieval Europe + elves. Each "
    "concept should make a reader think 'I've never seen THAT before.'"
)

GENERATE_PROMPT = """Generate {count} fantasy novel seed concepts. Each should be
a complete premise you could build a novel from.

For EACH concept, provide:

NUMBER. TITLE (a working title, evocative, not generic)
HOOK: One sentence that would make someone pick up the book. Specific
  and surprising, not "In a world where..."
WORLD: What makes this world different? Not just "there's magic" but
  what specific, unusual thing defines this place? Be concrete --
  salt flats, inverted towers, cities that migrate, a sea that
  remembers, whatever. Make it SENSORY.
MAGIC/COST: What is the core speculative element and what does it
  COST? Per Sanderson's Second Law, limitations > powers. The cost
  should create interesting dilemmas.
TENSION: What's the central conflict? It must be both PERSONAL (one
  character's specific problem) and COSMIC (affects the world).
  These two must be in tension with each other.
THEME: What question does this story explore? Not a message -- a
  genuine question with no easy answer.
WHY IT'S NOT GENERIC: One sentence on what makes this different from
  standard fantasy fare.

Aim for DIVERSITY across the {count} concepts:
  - At least one with a non-human-centric world
  - At least one that's more literary/quiet than epic
  - At least one with an unusual narrative structure idea
  - At least one set outside the typical European-inspired setting
  - Mix of tones: dark, warm, weird, melancholy, whimsical

DO NOT generate:
  - Chosen one prophecies (unless subverted in an interesting way)
  - Dark lord / ultimate evil as the main antagonist
  - Medieval Europe + elves/dwarves/orcs
  - "Academy" or "school for magic" settings
  - Love triangles as the central plot
"""

class BypassOrRunStep(Step):
    def __init__(self):
        super().__init__("Check seed.txt existence and prompt bypass")

    def run(self, context: Dict[str, Any]) -> None:
        context["skip_ideation"] = False
        if SEED_PATH.exists():
            print(f"\n[Ideation] Um arquivo seed.txt já existe em {SEED_PATH}.")
            choice = input("Deseja pular (bypass) a ideação e usar a semente existente? [S/N] (default: S): ").strip().upper()
            if choice != "N":
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
        
        genre = input("1. Gênero/Estilo (ex: Sci-fi noir, High fantasy) [default: Fantasy]: ").strip() or "Fantasy"
        spark = input("2. Centelha criativa (Spark - ideia central) [default: any]: ").strip() or "any"
        cost = input("3. Custo da magia/speculative element [default: physical toll]: ").strip() or "physical toll"
        protagonist = input("4. Protagonista (POV/Conflito) [default: scholar]: ").strip() or "scholar"
        
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
            f"{GENERATE_PROMPT.format(count=3)}"
        )
        
        concepts = call_llm(
            prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT,
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
        
        choice = input("Opção desejada (1-3 ou C): ").strip().upper()
        
        if choice in ["1", "2", "3"]:
            # Parse the selected option from generated_concepts
            concepts_text = context.get("generated_concepts", "")
            # Simple heuristic split by number patterns
            parts = re.split(r'^\s*(\d+)\.\s+', concepts_text, flags=re.MULTILINE)
            selected_text = ""
            for idx in range(1, len(parts), 2):
                if parts[idx] == choice:
                    selected_text = f"{parts[idx]}. {parts[idx+1].strip()}"
                    break
            
            if not selected_text:
                selected_text = concepts_text  # fallback to whole text if parse failed
                
            SEED_PATH.write_text(selected_text, encoding="utf-8")
            print(f"[Ideation] Semente do conceito {choice} salva com sucesso em {SEED_PATH}.")
        else:
            custom_seed = input("\nDigite/cole o seu próprio conceito completo:\n").strip()
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
        choice = input("Deseja gerar a Bíblia de Mistérios (MYSTERY.md)? [S/N] (default: N): ").strip().upper()
        
        if choice == "S":
            print("[Ideation] Gerando mistério central...")
            seed = SEED_PATH.read_text(encoding="utf-8")
            
            mystery_system = (
                "You are a master of plots and plot twists. You establish a structural mystery. "
                "You respond strictly with a markdown document starting with '# THE CENTRAL MYSTERY'."
            )
            
            mystery_prompt = (
                f"Com base na seguinte semente de romance:\n\n{seed}\n\n"
                f"Gere um mistério central detalhado estruturado. Inclua:\n"
                f"- A pergunta/mistério que o protagonista investiga.\n"
                f"- O segredo oculto (The Answer - o que de fato aconteceu, conspirações, culpados).\n"
                f"- Como o mistério é plantado e revelado nos atos."
            )
            
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
                template = (
                    "# THE CENTRAL MYSTERY\n"
                    "### Author's Eyes Only — Not for AI agent context during drafting\n\n"
                    "---\n\n"
                    "<!-- Define the central secret... -->\n"
                )
                MYSTERY_PATH.write_text(template, encoding="utf-8")

class UpdateStateStep(Step):
    def __init__(self):
        super().__init__("Initialize book state in state.json")

    def run(self, context: Dict[str, Any]) -> None:
        BOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        state = {"chapters_drafted": 0, "phase": "foundation", "current_focus": "planning"}
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
