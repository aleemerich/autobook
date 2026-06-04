#!/usr/bin/env python3
"""
skills/create_agent.py — Dynamic agent registration skill.
"""

from agents import Agent

ROLE_NAME = "custom_localizer"

class CustomLocalizerAgent(Agent):
    """Dynamically loaded agent specializing in custom localization adjustments."""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="CustomLocalizerAgent",
            system_prompt=(
                "You are a specialized localization reviewer. "
                "Ensure the dialect is absolutely clean, natural, and free "
                "of any cross-dialect contamination."
            ),
            temperature=0.3
        )

def register(factory):
    """Registers the custom localizer agent class into the factory."""
    factory.register_agent(ROLE_NAME, CustomLocalizerAgent)
