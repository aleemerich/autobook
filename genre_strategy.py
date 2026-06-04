#!/usr/bin/env python3
"""
genre_strategy.py — Strategy pattern for dynamic genre and style loading.

Decouples all genre-specific guidelines, structural rules, and anti-patterns 
from the main python codebase.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.resolve()

class GenreStrategy:
    """Strategy class that loads and formats writing style rules based on the active genre."""
    
    def __init__(self, genre: Optional[str] = None, language: Optional[str] = None):
        self.language = (language or os.environ.get("AUTOBOOK_LANGUAGE", "EN")).upper().strip()
        self.genre = (genre or os.environ.get("AUTOBOOK_GENRE", "drama")).lower().strip()
        self.genres_dir = BASE_DIR / "genres"
        self._rules_text = ""
        self._load_strategy()

    def _load_strategy(self):
        """Locates and loads the text configuration of the selected genre."""
        # 1. Try localizing the requested genre file
        genre_file = self.genres_dir / self.language / f"{self.genre}.txt"
        if genre_file.exists():
            self._rules_text = genre_file.read_text(encoding="utf-8")
            return
            
        # 2. Try falling back to the English (EN) version of the requested genre
        if self.language != "EN":
            fallback_file = self.genres_dir / "EN" / f"{self.genre}.txt"
            if fallback_file.exists():
                self._rules_text = fallback_file.read_text(encoding="utf-8")
                return
                
        # 3. Fallback to default 'drama' in active language
        default_file = self.genres_dir / self.language / "drama.txt"
        if default_file.exists():
            self._rules_text = default_file.read_text(encoding="utf-8")
            return
            
        # 4. Final emergency fallback to 'drama' in English
        final_file = self.genres_dir / "EN" / "drama.txt"
        if final_file.exists():
            self._rules_text = final_file.read_text(encoding="utf-8")
            return
            
        raise FileNotFoundError(
            f"Critical default genre file 'drama.txt' not found under EN fallback. "
            f"Please ensure genres/EN/drama.txt exists."
        )

    def get_style_guidelines(self) -> str:
        """Returns the full list of formatted constraints and style rules for the writer."""
        return self._rules_text

    def get_anti_patterns(self) -> List[str]:
        """
        Parses the loaded rules to extract lines under the 'PADRÕES A EVITAR' 
        or 'PATTERNS TO AVOID' section if present.
        """
        lines = self._rules_text.splitlines()
        anti_patterns = []
        is_anti_pattern_section = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Toggle parsing when finding section headers
            if any(h in stripped.upper() for h in ["PADRÕES A EVITAR", "PATTERNS TO AVOID"]):
                is_anti_pattern_section = True
                continue
            elif stripped.startswith("#") or (stripped.endswith(":") and len(stripped) < 40):
                # Another section starts
                is_anti_pattern_section = False
                
            if is_anti_pattern_section:
                # Clean up bullet numbers/hyphens (e.g. "9. SEM inícios morosos" -> "SEM inícios morosos")
                clean_line = re.sub(r'^\d+\.\s*|-\s*', '', stripped).strip()
                if clean_line:
                    anti_patterns.append(clean_line)
                    
        return anti_patterns
