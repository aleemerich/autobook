#!/usr/bin/env python3
"""
pipelines/base.py — Base Step and Pipeline classes.
Provides the Command/Composite pattern for modular workflows.
"""

from typing import Dict, Any, List

class Step:
    """Base class for atomic pipeline steps."""
    def __init__(self, name: str):
        self.name = name

    def run(self, context: Dict[str, Any]) -> None:
        raise NotImplementedError("Subclasses must implement run(context)")

class Pipeline(Step):
    """Composite step that executes a sequence of other steps."""
    def __init__(self, name: str, steps: List[Step] = None):
        super().__init__(name)
        self.steps = steps or []

    def add_step(self, step: Step):
        self.steps.append(step)

    def run(self, context: Dict[str, Any]) -> None:
        print(f"\n>>> Starting Pipeline: {self.name}")
        for step in self.steps:
            print(f"--- Running Step: {step.name} ---")
            step.run(context)
        print(f">>> Finished Pipeline: {self.name}\n")
