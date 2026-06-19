#!/usr/bin/env python3
"""
pipelines/foundation.py — Foundation Planning Pipeline.
Generates world.md, characters.md, outline.md, and canon.md under book_data/ based on seed.txt.
"""

import sys
from pathlib import Path
from typing import Dict, Any

from pipelines.base import Step, Pipeline
from llm import call_llm
from pipelines.foundation_steps import (
    load_world_inputs,
    load_characters_inputs,
    load_outline_inputs,
    load_canon_inputs,
    commit_foundation_artifacts,
    write_foundation_state,
    load_foundation_prompt,
    render_foundation_prompt
)

BASE_DIR = Path(__file__).parent.parent.resolve()
BOOK_DATA_DIR = BASE_DIR / "book_data"
SEED_PATH = BASE_DIR / "seed.txt"
MYSTERY_PATH = BOOK_DATA_DIR / "MYSTERY.md"
STATE_FILE = BOOK_DATA_DIR / "state.json"
CRAFT_PATH = BASE_DIR / "docs" / "en" / "others" / "CRAFT.md"
VOICE_PATH = BOOK_DATA_DIR / "voice.md"

WORLD_PATH = BOOK_DATA_DIR / "world.md"
CHARACTERS_PATH = BOOK_DATA_DIR / "characters.md"
OUTLINE_PATH = BOOK_DATA_DIR / "outline.md"
CANON_PATH = BOOK_DATA_DIR / "canon.md"

class VerifySeedStep(Step):
    def __init__(self):
        super().__init__("Verify seed.txt existence")

    def run(self, context: Dict[str, Any]) -> None:
        if not SEED_PATH.exists():
            raise FileNotFoundError(
                f"[Foundation] Arquivo seed.txt não encontrado na raiz ({SEED_PATH}).\n"
                f"Por favor, execute a pipeline de ideação primeiro:\n"
                f"  python run.py --pipeline ideation"
            )
        print("[Foundation] seed.txt verificado com sucesso.")

class GenerateWorldStep(Step):
    def __init__(self):
        super().__init__("Generate world.md (World Bible)")

    def run(self, context: Dict[str, Any]) -> None:
        print("[Foundation] Gerando world.md...")
        inputs = load_world_inputs(SEED_PATH, VOICE_PATH)
        seed = inputs["seed"]
        voice_p2 = inputs["voice_part2"]
        
        system = load_foundation_prompt("world_system")
        prompt = render_foundation_prompt("world_user", {"seed": seed, "voice_p2": voice_p2})
        world_text = call_llm(prompt=prompt, system_prompt=system, temperature=0.7, is_judge=False)
        BOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)
        WORLD_PATH.write_text(world_text, encoding="utf-8")
        print(f"[Foundation] world.md gerado e salvo em {WORLD_PATH}.")

class GenerateCharactersStep(Step):
    def __init__(self):
        super().__init__("Generate characters.md (Character Registry)")

    def run(self, context: Dict[str, Any]) -> None:
        print("[Foundation] Gerando characters.md...")
        inputs = load_characters_inputs(SEED_PATH, WORLD_PATH, VOICE_PATH)
        seed = inputs["seed"]
        world = inputs["world"]
        voice_p2 = inputs["voice_part2"]
        
        system = load_foundation_prompt("characters_system")
        prompt = render_foundation_prompt("characters_user", {"seed": seed, "world": world, "voice_p2": voice_p2})
        chars_text = call_llm(prompt=prompt, system_prompt=system, temperature=0.7, is_judge=False)
        CHARACTERS_PATH.write_text(chars_text, encoding="utf-8")
        print(f"[Foundation] characters.md gerado e salvo em {CHARACTERS_PATH}.")

class GenerateOutlineStep(Step):
    def __init__(self):
        super().__init__("Generate outline.md (Chapter Outline & Beats)")

    def run(self, context: Dict[str, Any]) -> None:
        print("[Foundation] Gerando outline.md...")
        inputs = load_outline_inputs(
            SEED_PATH,
            WORLD_PATH,
            CHARACTERS_PATH,
            MYSTERY_PATH,
            CRAFT_PATH,
            VOICE_PATH
        )
        seed = inputs["seed"]
        world = inputs["world"]
        characters = inputs["characters"]
        mystery = inputs["mystery"]
        craft = inputs["craft"]
        voice_p2 = inputs["voice_part2"]
        
        system = load_foundation_prompt("outline_system")
        prompt = render_foundation_prompt(
            "outline_user",
            {
                "seed": seed,
                "mystery": mystery,
                "world": world,
                "characters": characters,
                "voice_p2": voice_p2,
                "craft": craft,
            }
        )
        outline_text = call_llm(prompt=prompt, system_prompt=system, temperature=0.5, is_judge=False)
        OUTLINE_PATH.write_text(outline_text, encoding="utf-8")
        print(f"[Foundation] outline.md gerado e salvo em {OUTLINE_PATH}.")

class GenerateCanonStep(Step):
    def __init__(self):
        super().__init__("Generate canon.md (Canon Fact Database)")

    def run(self, context: Dict[str, Any]) -> None:
        print("[Foundation] Gerando canon.md...")
        inputs = load_canon_inputs(SEED_PATH, WORLD_PATH, CHARACTERS_PATH)
        seed = inputs["seed"]
        world = inputs["world"]
        characters = inputs["characters"]
        
        system = load_foundation_prompt("canon_system")
        prompt = render_foundation_prompt("canon_user", {"seed": seed, "world": world, "characters": characters})
        canon_text = call_llm(prompt=prompt, system_prompt=system, temperature=0.2, is_judge=False)
        CANON_PATH.write_text(canon_text, encoding="utf-8")
        print(f"[Foundation] canon.md gerado e salvo em {CANON_PATH}.")

class CommitFoundationStep(Step):
    def __init__(self):
        super().__init__("Git add/commit and initialize state.json")

    def run(self, context: Dict[str, Any]) -> None:
        print("[Foundation] Commitando arquivos estruturais de planejamento no Git...")

        # Reset state.json cursor to 0 chapters drafted before committing so the
        # committed planning snapshot is immediately usable for writing.
        write_foundation_state(STATE_FILE)
        
        # Git add and commit
        try:
            commit_foundation_artifacts(BASE_DIR, MYSTERY_PATH.exists())
            print("[Foundation] Git commit concluído com sucesso.")
        except Exception as e:
            print(f"[Warning] Falha ao executar commits automáticos no Git: {e}", file=sys.stderr)

        print("[Foundation] Cursor em state.json inicializado para escrita (chapters_drafted: 0).")


class FoundationPipeline(Pipeline):
    def __init__(self):
        super().__init__("Foundation Planning Pipeline")
        self.add_step(VerifySeedStep())
        self.add_step(GenerateWorldStep())
        self.add_step(GenerateCharactersStep())
        self.add_step(GenerateOutlineStep())
        self.add_step(GenerateCanonStep())
        self.add_step(CommitFoundationStep())
