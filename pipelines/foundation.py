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
    write_foundation_state
)

BASE_DIR = Path(__file__).parent.parent.resolve()
BOOK_DATA_DIR = BASE_DIR / "book_data"
SEED_PATH = BASE_DIR / "seed.txt"
MYSTERY_PATH = BOOK_DATA_DIR / "MYSTERY.md"
STATE_FILE = BOOK_DATA_DIR / "state.json"
CRAFT_PATH = BASE_DIR / "docs" / "others" / "CRAFT.md"
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
        
        system = (
            "You are a setting designer and story-world architect with deep knowledge "
            "of narrative systems, social consequences, genre conventions, and concrete "
            "sensory worldbuilding. You write reference bibles that are specific, "
            "interconnected, and imply depth beyond what is stated. You never use AI "
            "slop words (delve, tapestry, myriad, etc). You write in clean, direct prose. "
            "Every rule has a cost. Every cultural detail implies a history. Every "
            "location has a sensory signature."
        )
        
        prompt = f"""Build a complete world bible for the current book. This is the WORLD.MD file --
the definitive reference for everything that EXISTS in this world. A writer should be able 
to resolve any worldbuilding question from this document alone.

SEED CONCEPT:
{seed}

VOICE IDENTITY (the tone and register of this novel):
{voice_p2}

CRAFT REQUIREMENTS (follow these):
- Any central system, institution, technology, magic, profession, law, or social structure needs HARD RULES with COSTS and LIMITATIONS
- Limitations must be at least as narratively prominent as capabilities
- Trace implications of the book's central systems through society, economy, law, religion, family, class, and daily life where relevant
- At least 2-3 societal implications of the central systems explored in depth
- History must create PRESENT-DAY TENSIONS that drive the plot (not just backdrop)
- Geography and built environments must be specific and sensory, not generic
- Iceberg principle: imply more than you state
- Interconnection: pulling one thread should move everything

STRUCTURE THE DOCUMENT WITH THESE SECTIONS:

## Cosmology & History
A timeline of major events. Focus on events that create PRESENT-DAY tensions.
Include the founding myth, key turning points, and recent events that matter to the plot.

## Core Systems, Rules & Constraints
### Hard / Operational Rules
Specific, testable rules for any central system in the book: magic, technology,
law, profession, crime, religion, economics, social codes, or other governing
logic. What actions are possible? What fails? What breaks? Include COSTS and
LIMITATIONS prominently.

### Exceptions, Edge Cases, and Unusual Abilities
If the story has unusual perception, abilities, tools, procedures, privileges,
or forbidden knowledge, define what is known, what is uncertain, and what it
costs the characters. Keep mystery where useful, but preserve internal logic.

### Societal Implications
How do the book's central systems shape governance, commerce, education, class
structure, crime, family life, childhood, aging, disability, labor, risk, and
status?

## Geography
The main setting's physical layout, districts, borders, routes, climate,
architecture, infrastructure, and sensory signatures. Include neighboring
places or adjacent social spaces when relevant.

## Factions & Politics
Who holds power, who wants it, who's being crushed by it.
At least 3-4 factions with opposing interests.

## Bestiary / Flora / Natural World
What's unique about the natural world, built environment, ecology, technology,
or material culture in and around the main setting?

## Cultural Details
Customs, taboos, festivals, food, clothing, coming-of-age rituals.
Things that make daily life feel SPECIFIC.

## Internal Consistency Rules
Hard constraints a writer must not violate. The physics, logistics, social rules,
technological limits, magical constraints, or institutional procedures that define
what is possible and what is not.

IMPORTANT:
- Be SPECIFIC. Not "the city has districts" but name them, describe them, 
  give them sensory signatures.
- Every rule should have a COST or LIMITATION stated alongside it.
- Include 2-3 facts per section that are unexplained, hinting at deeper systems 
  (iceberg depth).
- Facts should INTERCONNECT: central systems should shape politics, geography
  should shape culture, and history should explain current faction conflicts.
- Write in clean, direct prose. No AI slop. No "rich tapestry." No "delving."
- The world should feel grounded and LIVED-IN, not imagined.
- Target ~3000-4000 words. Dense, not padded.
"""
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
        
        system = (
            "You are a character designer for fiction with deep knowledge of "
            "wound/want/need/lie frameworks, Sanderson's three sliders, and dialogue "
            "distinctiveness. You create characters who feel like real people with "
            "contradictions, secrets, and speech patterns you can hear. "
            "You never use AI slop words. You write in clean, direct prose."
        )
        
        prompt = f"""Build a complete character registry for the current book. This is CHARACTERS.MD --
the definitive reference for WHO exists in this story, what drives them, how they speak,
and what secrets they carry.

SEED CONCEPT:
{seed}

WORLD BIBLE (the world these characters inhabit):
{world}

VOICE IDENTITY (the novel's tone):
{voice_p2}

CHARACTER CRAFT REQUIREMENTS:

### The Three Sliders (Sanderson)
Every character has three independent dials (0-10):
  PROACTIVITY -- Do they drive the plot or react to it?
  LIKABILITY  -- Does the reader empathize with them?
  COMPETENCE  -- Are they good at what they do?
Rule: compelling = HIGH on at least TWO, or HIGH on one with clear growth.

### Wound / Want / Need / Lie Framework
A causal chain:
  GHOST (backstory event) -> WOUND (ongoing damage) -> LIE (false belief to cope)
    -> WANT (external goal driven by Lie) -> NEED (internal truth, opposes Lie)
Rules: Want and Need must be IN TENSION. Lie statable in one sentence.
  Truth is its direct opposite.

### Dialogue Distinctiveness (8 dimensions)
1. Vocabulary level  2. Sentence length  3. Contractions/formality
4. Verbal tics  5. Question vs statement ratio  6. Interruption patterns
7. Metaphor domain  8. Directness vs indirectness
Test: Remove dialogue tags. Can you tell who's speaking?

BUILD THE REGISTRY WITH AT LEAST THESE ROLES:

1. **Protagonist / Primary POV character**
   - Full wound/want/need/lie chain
   - Three sliders with justification
   - Arc type (positive/negative/flat)
   - Detailed speech pattern (8 dimensions)
   - Physical habits and tells
   - At least 2 secrets
   - Key relationships mapped

2. **Primary relationship anchor**
   - Same depth as the protagonist when narratively important
   - The relationship pressure this person creates
   - What they know, need, hide, or misunderstand

3. **Missing, absent, threatened, or catalytic figure**
   - If someone is absent for much of the story, give them full depth anyway
   - What their absence changes
   - How their presence is felt indirectly

4. **Primary opposition force / antagonist**
   - Not a cartoon villain -- someone whose interests conflict with the protagonist's
   - Their own wound/want/need/lie
   - Why their choices are understandable from inside their worldview

5. **Institutional or systemic pressure figure**
   - A person who embodies a system, institution, family, market, law, class, or ideology
   - Why they believe they are preserving something necessary

6. **Outsider, reformer, witness, rival, or alternate worldview**
   - The perspective that exposes blind spots in the protagonist and setting
   - What this person represents thematically

7. **At least 1-3 additional characters** that the story needs
   - Peers, friends, rivals, witnesses, gatekeepers, family, professional contacts, or conspirators
   - Each must create pressure, reveal theme, or complicate the plot

FOR EACH CHARACTER INCLUDE:
- Name, age, role
- Ghost/Wound/Want/Need/Lie chain (for major characters)
- Three sliders (proactivity/likability/competence) with numbers and justification
- Arc type and arc trajectory
- Speech pattern (all 8 dimensions, with example lines)
- Physical appearance (specific, not generic)
- Physical habits and unconscious tells
- Secrets (what the reader doesn't learn immediately)
- Key relationships (mapped to other characters)
- Thematic role (what question does this character embody?)

IMPORTANT:
- Characters must INTERCONNECT. Their wants should conflict with each other.
- Every secret should be something that would CHANGE the story if revealed.
- Speech patterns must be distinct enough to pass the no-tags test.
- Give the protagonist habits that emerge from their body, work, wound, training, status, or unusual perception.
- Physical tells should connect to specific history, pressure, or coping mechanisms.
- The primary antagonist/opposition force should be as fully realized as the protagonist.
- Target ~3000-4000 words. Dense character work, not padding.
"""
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
        
        system = (
            "You are a novel architect with deep knowledge of Save the Cat beats, "
            "Sanderson's plotting principles, Dan Harmon's Story Circle, and MICE Quotient. "
            "You build outlines that an author can draft from without inventing structure "
            "on the fly. Every chapter has beats, emotional arc, and try-fail cycle type. "
            "You never use AI slop words. You write in clean, direct prose."
        )
        
        prompt = f"""Build a complete chapter outline for the current book. Size the chapter count
to the material instead of forcing a fixed number. Recommend a target total word count and
chapter count based on the seed, genre, world complexity, character arcs, mystery/subplot
density, and intended pacing.

SEED CONCEPT:
{seed}

THE CENTRAL MYSTERY (author's eyes only -- reader discovers gradually):
{mystery}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

VOICE (tone and register):
{voice_p2}

CRAFT REFERENCE:
{craft}

BUILD THE OUTLINE WITH:

## Act Structure
Map out Act I (0-23%), Act II Part 1 (23-50%), Act II Part 2 (50-77%), Act III (77-100%).
State the percentage marks for the key novel.

## Chapter-by-Chapter Outline

For EACH chapter, provide:
### Ch N: [Title]
- **POV:** viewpoint character and narrative distance
- **Location:** Which places or social spaces
- **Save the Cat beat:** Which beat this chapter serves (Opening Image, Setup, Catalyst, etc.)
- **% mark:** Where this falls in the novel
- **Emotional arc:** Starting emotion -> ending emotion
- **Try-fail cycle:** Yes-but / No-and / No-but / Yes-and
- **Beats:** 3-5 specific scene beats that must happen
- **Plants:** Foreshadowing elements planted in this chapter
- **Payoffs:** Foreshadowing elements that pay off here
- **Character movement:** What changes for the protagonist or other important characters by chapter's end
- **The lie / false belief:** How the relevant character's false belief is reinforced, challenged, or broken
- **~Word count target:** for pacing

## Foreshadowing Ledger

A table tracking every planted thread:
| Thread | Planted (Ch) | Reinforced (Ch) | Payoff (Ch) | Type |

Include at LEAST 15 threads. Types: object, dialogue, action, symbolic, structural.

KEY PLOT ARCHITECTURE:

Act I: Establish the protagonist, central pressure, ordinary world, first promises,
and the initial contradiction or wound. Plant the central question/mystery/conflict early.
Catalyst: something forces the protagonist into irreversible motion.

Act II Part 1: Escalation, investigation, training, pursuit, or deepening entanglement.
The protagonist tests an approach and forms alliances, rivalries, or dependencies.
Midpoint: a partial truth, false victory, or reversal changes the protagonist's approach.

Act II Part 2: Pressure mounts. Costs become personal. Secrets, betrayals, system limits,
or relationship fractures surface. All Is Lost: the protagonist loses the old strategy.

Act III: The protagonist understands the real question. The climax resolves through
rules, relationships, costs, and choices established earlier.

CONSTRAINTS:
- Climax must be mechanically and emotionally resolvable using rules and costs established earlier
- Vary try-fail types: 60%+ should be "yes-but" or "no-and"
- Foreshadowing ledger must have plant-to-payoff distances of at least 3 chapters
"""
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
        
        system = (
            "You are a continuity editor extracting hard facts from book "
            "planning documents. You are precise, exhaustive, and never invent facts "
            "that aren't in the source material. Every entry must be traceable to a "
            "specific statement in the source documents."
        )
        
        prompt = f"""Extract EVERY hard fact from these planning documents into a structured canon database.
A "hard fact" is anything a writer must not contradict: names, ages, dates, physical descriptions,
rules of central systems, geography, relationships, established events.

SOURCE DOCUMENTS:

=== SEED.TXT ===
{seed}

=== WORLD.MD ===
{world}

=== CHARACTERS.MD ===
{characters}

FORMAT THE OUTPUT AS CANON.MD with these categories:

## Geography
- Specific facts about locations, distances, physical properties

## Timeline
- Dated events, ages, durations

## Core System Rules
- Hard rules, constraints, costs, limitations, exceptions, and edge cases for any central system in the book

## Character Facts
- Ages, physical descriptions, habits, relationships
- One entry per fact (not paragraphs)

## Political / Factional
- Who controls what, alliances, conflicts, contracts

## Cultural
- Customs, taboos, laws, festivals, food, clothing

## Established In-Story
- Events that have already happened in the story's past
- Past events, promises, crimes, obligations, conflicts, losses, agreements, discoveries, or turning points that the story must not contradict

RULES:
- One fact per bullet point. Short. Specific. Checkable.
- Include the source (world.md or characters.md) in parentheses after each fact.
- Aim for 80-120 entries minimum. Be exhaustive.
- DO NOT invent facts. Only record what's explicitly stated.
"""
        canon_text = call_llm(prompt=prompt, system_prompt=system, temperature=0.2, is_judge=False)
        CANON_PATH.write_text(canon_text, encoding="utf-8")
        print(f"[Foundation] canon.md gerado e salvo em {CANON_PATH}.")

class CommitFoundationStep(Step):
    def __init__(self):
        super().__init__("Git add/commit and initialize state.json")

    def run(self, context: Dict[str, Any]) -> None:
        print("[Foundation] Commitando arquivos estruturais de planejamento no Git...")
        
        # Git add and commit
        try:
            commit_foundation_artifacts(BASE_DIR, MYSTERY_PATH.exists())
            print("[Foundation] Git commit concluído com sucesso.")
        except Exception as e:
            print(f"[Warning] Falha ao executar commits automáticos no Git: {e}", file=sys.stderr)

        # Reset state.json cursor to 0 chapters drafted
        write_foundation_state(STATE_FILE)
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
