#!/usr/bin/env python3
"""
agents.py — Literary multi-agent system for novel generation.

Defines the Agent base class, specialized agents (Drafting, Stylist, Technical Editor),
and the dynamic AgentFactory singleton.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from llm import call_llm

class Agent:
    """Base class for all literary agents in the pipeline."""
    
    def __init__(self, name: str, system_prompt: str, temperature: float = 0.7):
        self.name = name
        self.system_prompt = system_prompt
        self.temperature = temperature

    def execute(self, prompt: str) -> str:
        """Call the underlying LLM with the agent's specific persona/instructions."""
        try:
            return call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=self.temperature,
                is_judge=False
            )
        except Exception as e:
            print(f"[{self.name}] Error during execution: {e}", file=sys.stderr)
            raise


class DraftingAgent(Agent):
    """Agent responsible for writing the raw, structural narrative draft of a chapter."""
    
    def __init__(self, temperature: float = 0.8):
        super().__init__(
            name="DraftingAgent",
            system_prompt=(
                "You are an elite novelist drafting the raw, foundational scenes of a chapter.\n"
                "Your focus is on building solid narrative structure, hitting the specific planned beat, "
                "and setting up the raw story. Write the FULL text of the scene without shortcuts or summaries.\n\n"
                "CRITICAL OUTPUT FORMAT CONSTRAINT:\n"
                "Return ONLY the raw prose of the draft scene. Do NOT include any intro/outro comments, "
                "notes, headers, or metadata. Output the story text and nothing else."
            ),
            temperature=temperature
        )


class StylistAgent(Agent):
    """Agent responsible for refining the draft, injecting genre-specific action, tone, and cliffhangers."""
    
    def __init__(self, genre_rules: str, temperature: float = 0.7):
        system_prompt = (
            "You are a master stylist and editor of high-tension speculative fiction.\n"
            "Your task is to take a raw chapter draft and rewrite it to apply the specific "
            "genre, pace, tension, and style rules below. Inject physical action, dynamic dialogues, "
            "and strong hooks.\n\n"
            "CRITICAL OUTPUT FORMAT CONSTRAINT:\n"
            "Return ONLY the refined prose of the scene. Do NOT include any explanations, notes, "
            "preambles, or markdown commentary. Your output must consist strictly of the revised story text.\n\n"
            f"GENRE SPECIFIC RULES:\n{genre_rules}"
        )
        super().__init__(
            name="StylistAgent",
            system_prompt=system_prompt,
            temperature=temperature
        )


class TechnicalEditorAgent(Agent):
    """Agent responsible for calibrating scientific data, verifying lore, and enforcing PT-BR localization."""
    
    def __init__(self, lore_data: str, slop_rules: str, temperature: float = 0.3):
        system_prompt = (
            "You are a meticulous technical editor and localization expert.\n"
            "Your sole focus is to review the chapter text and refine it for absolute consistency "
            "with the world lore, scientific facts, and language guidelines.\n\n"
            "Apply the following rules strictly:\n"
            "1. LORE CONSISTENCY: Ensure all names, objects, dates, and locations match the lore reference below. "
            "Keep the Faraday chamber at exactly 20.0°C. Ensure Lena has blonde hair in a functional ponytail. "
            "Ensure Helena has light-blue, almost translucent eyes and white hair cut at the chin, tied with a wooden peg. "
            "Ensure Helena has NO history of dementia, Alzheimer's, or cognitive impairment (she has no relevant neurological history, just hypertension controlled with losartan, and mild osteoarthritis in her hands). Do NOT introduce any diagnosis of dementia frontotemporal or MMSE scores.\n"
            "2. ANTI-SLOP GUARDRAILS: Strip any clichéd AI writing structures or forbidden words.\n"
            "3. DIALECT LOCALIZATION: Translate any residual European Portuguese (PT-PT) terms into natural, formal Brazilian Portuguese (PT-BR) (e.g. 'ecrã' -> 'tela', 'bata' -> 'jaleco', 'contacto' -> 'contato', 'actividade' -> 'atividade', 'portátil' -> 'laptop', 'registou' -> 'registrou', 'repiti' -> 'repeti', and ensure correct gender agreement for female characters like 'Dra. Lena Hartmann' or 'Doutora Hartmann', NOT 'Doutor Hartmann').\n"
            "4. POETIC AMBIGUITY & TONAL INTEGRITY: The novel is a Speculative Thriller, not a fantasy or supernatural story. "
            "Strictly maintain third-person limited POV (only Elisa's perspective). "
            "Under no circumstances should the anomaly or transcendence be explained or confirmed as magical or supernatural. "
            "Do NOT allow electronic devices to speak, messages from deceased characters to appear on unplugged screens, "
            "or glowing diagrams to appear on walls. Keep the phenomenon subtle, thermodynamic, and physical.\n\n"
            "CRITICAL OUTPUT FORMAT CONSTRAINT:\n"
            "Return ONLY the final, polished, and localized prose of the scene. "
            "Do NOT include any technical review reports, summary of edits, preambles, remarks, or explanations. "
            "Your response must be 100% pure story prose.\n\n"
            f"LORE REFERENCE DATA:\n{lore_data}\n\n"
            f"ANTI-SLOP & STYLE CONSTRAINTS:\n{slop_rules}"
        )
        super().__init__(
            name="TechnicalEditorAgent",
            system_prompt=system_prompt,
            temperature=temperature
        )


class AgentFactory:
    """Singleton Factory to register, create, and load literary agents dynamically."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentFactory, cls).__new__(cls)
            cls._instance._agents_registry = {}
        return cls._instance

    def register_agent(self, role: str, agent_class):
        """Register a new agent class dynamically."""
        self._agents_registry[role.lower()] = agent_class

    def get_agent(self, role: str, **kwargs) -> Agent:
        """Create and return an agent instance based on registered classes."""
        role_key = role.lower()
        
        # Internal default classes fallback
        if role_key == "drafting":
            return DraftingAgent(temperature=kwargs.get("temperature", 0.8))
        elif role_key == "stylist":
            return StylistAgent(
                genre_rules=kwargs.get("genre_rules", ""),
                temperature=kwargs.get("temperature", 0.7)
            )
        elif role_key == "technical_editor":
            return TechnicalEditorAgent(
                lore_data=kwargs.get("lore_data", ""),
                slop_rules=kwargs.get("slop_rules", ""),
                temperature=kwargs.get("temperature", 0.3)
            )
            
        if role_key in self._agents_registry:
            return self._agents_registry[role_key](**kwargs)
            
        raise ValueError(f"Agent role '{role}' is not registered and has no default class.")

    def load_skill_agent(self, skill_name: str, **kwargs) -> Agent:
        """
        Dynamically load a specialized agent defined via a skill configuration.
        This allows importing scripts dynamically in runtime.
        """
        skills_dir = Path(__file__).parent / "skills"
        skill_file = skills_dir / f"{skill_name}.py"
        
        if not skill_file.exists():
            raise FileNotFoundError(f"Skill file '{skill_name}.py' not found under: {skills_dir}")
            
        # Dynamically import and register the skill module
        import importlib.util
        spec = importlib.util.spec_from_file_location(skill_name, str(skill_file))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register"):
                module.register(self)
                # Re-fetch from registry after dynamic import
                role_name = getattr(module, "ROLE_NAME", skill_name)
                return self.get_agent(role_name, **kwargs)
                
        raise ImportError(f"Failed to load or register skill agent from '{skill_file}'")
