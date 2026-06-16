#!/usr/bin/env python3
"""
pipelines/base.py — Base Step and Pipeline classes.
Provides the Command/Composite pattern for modular workflows.
"""

from typing import Dict, Any, List, Optional

class Step:
    """Base class for atomic pipeline steps."""
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        requires: Optional[List[str]] = None,
        produces: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.requires = list(requires) if requires is not None else []
        self.produces = list(produces) if produces is not None else []

    def run(self, context: Dict[str, Any]) -> None:
        raise NotImplementedError("Subclasses must implement run(context)")

class Pipeline(Step):
    """Composite step that executes a sequence of other steps."""
    def __init__(
        self,
        name: str,
        steps: Optional[List[Step]] = None,
        description: Optional[str] = None,
        requires: Optional[List[str]] = None,
        produces: Optional[List[str]] = None,
    ):
        super().__init__(
            name=name,
            description=description,
            requires=requires,
            produces=produces,
        )
        self.steps = steps or []

    def add_step(self, step: Step):
        self.steps.append(step)

    def run(self, context: Dict[str, Any]) -> None:
        print(f"\n>>> Starting Pipeline: {self.name}")
        for step in self.steps:
            print(f"--- Running Step: {step.name} ---")
            step.run(context)
        print(f">>> Finished Pipeline: {self.name}\n")
