#!/usr/bin/env python3
"""
skills/redundancy_detector.py — Active redundancy and repetition detection skill.
"""

import re
from typing import Dict, List, Optional

ROLE_NAME = "redundancy_detector"

class RedundancyDetector:
    """Skill utility class to scan and flag repeating patterns, equations, and clichés."""
    
    def __init__(self, target_words: Optional[List[str]] = None):
        self.target_words = target_words or ["0,001", "0.001", "boltzmann", "entropia", "granito", "pedra", "rocha"]

    def scan_text(self, text: str) -> Dict[str, int]:
        """Count occurrences of target words in the provided text (case-insensitive)."""
        results = {}
        cleaned = text.lower()
        
        for word in self.target_words:
            # Use regex to find word matches (accounting for decimals)
            pattern = re.escape(word)
            matches = re.findall(pattern, cleaned)
            results[word] = len(matches)
            
        return results

    def get_redundancy_report(self, text: str, threshold: int = 4) -> List[str]:
        """Returns a list of warnings for any keywords exceeding the threshold density."""
        report = []
        counts = self.scan_text(text)
        
        for word, count in counts.items():
            if count > threshold:
                report.append(
                    f"Redundancy Warning: The term '{word}' appeared {count} times, "
                    f"which exceeds the healthy limit of {threshold}."
                )
        return report

def register(factory):
    """Registers the redundancy detector logic or wraps it inside an agent role if needed."""
    # This is a passive utility class but register interface is required for dynamic factory inclusion
    factory.register_agent(ROLE_NAME, lambda **kwargs: RedundancyDetector(**kwargs))
