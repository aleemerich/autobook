#!/usr/bin/env python3
"""
pipelines/book_generation.py — Book Generation Pipeline.
Resets the chapter files if --from-scratch is set and drafts chapters sequentially
using the cascading Drafting, Stylist, and Technical Editor agents.
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List

from pipelines.base import Step, Pipeline
from agents import AgentFactory
from genre_strategy import GenreStrategy
from prompt_loader import load_prompt, load_genre_rules, load_slop_rules_instruction
from evaluate import evaluate_chapter
from pipelines.book_generation_steps import (
    load_state,
    load_outline,
    count_total_chapters,
    extract_chapter_outline,
    extract_chapter_title,
    extract_next_chapter_outline,
    extract_chapter_beats,
    load_previous_chapter_tail,
    load_lore_files,
    build_lore_data,
    run_beat_drafting,
    run_chapter_fallback_drafting,
    run_critic_agents,
    run_sequential_synthesis
)

BASE_DIR = Path(__file__).parent.parent.resolve()
CHAPTERS_DIR = BASE_DIR / "chapters"
BOOK_DATA_DIR = BASE_DIR / "book_data"

class ResetStep(Step):
    def __init__(self):
        super().__init__("Reset Chapters and State")

    def run(self, context: Dict[str, Any]) -> None:
        if context.get("from_scratch"):
            print("[ResetStep] Clearing all chapter files in chapters/...")
            CHAPTERS_DIR.mkdir(exist_ok=True)
            for f in CHAPTERS_DIR.glob("ch_*.md"):
                f.unlink()
            
            state_file = BOOK_DATA_DIR / "state.json"
            if state_file.exists():
                state_file.unlink()
            print("[ResetStep] Reset complete.")


class DraftChaptersStep(Step):
    def __init__(self, critics_roles: List[str] = None):
        super().__init__("Draft Chapters sequentially")
        env_critics = os.environ.get("AUTOBOOK_CRITICS")
        if env_critics:
            self.critics_roles = [r.strip() for r in env_critics.split(",") if r.strip()]
        else:
            self.critics_roles = critics_roles or ["canon_critic", "style_critic", "flow_critic"]

    def run(self, context: Dict[str, Any]) -> None:
        # Load state or start new
        state_file = BOOK_DATA_DIR / "state.json"
        state = load_state(BOOK_DATA_DIR)

        start_chapter = state["chapters_drafted"] + 1

        # Read outline
        outline_text = load_outline(BOOK_DATA_DIR)

        # Parse total chapters
        total_chapters = count_total_chapters(outline_text)

        print(f"[DraftChaptersStep] Starting from Chapter {start_chapter} to {total_chapters}")

        # Setup Agent Factory
        factory = AgentFactory()

        # Load style guidelines and slop instructions
        genre_rules = load_genre_rules()
        slop_rules = load_slop_rules_instruction()

        # Load global lore references
        lore_files = load_lore_files(BOOK_DATA_DIR)
        world_text = lore_files["world"]
        canon_text = lore_files["canon"]
        characters_text = lore_files["characters"]
        voice_text = lore_files["voice"]

        lore_data = build_lore_data(world_text, canon_text, characters_text)

        # Agents instantiation
        drafting_agent = factory.get_agent("drafting")
        stylist_agent = factory.get_agent("stylist", genre_rules=genre_rules)
        tech_editor_agent = factory.get_agent("technical_editor", lore_data=lore_data, slop_rules=slop_rules)

        # Max attempts and threshold
        max_attempts = int(os.environ.get("MAX_CHAPTER_ATTEMPTS", 3))
        threshold = float(os.environ.get("CHAPTER_THRESHOLD", 6.0))

        target_chapters = context.get("chapters")
        if target_chapters:
            start_chapter = min(min(target_chapters), start_chapter)

        for ch in range(start_chapter, total_chapters + 1):
            if target_chapters and ch not in target_chapters:
                print(f"[DraftChaptersStep] Skipping Chapter {ch} (not in target chapters: {target_chapters})")
                continue

            print(f"\n======================================")
            print(f"Drafting Chapter {ch}/{total_chapters}")
            print(f"======================================")

            # Extract outline entry for this chapter
            ch_outline = extract_chapter_outline(outline_text, ch)

            # Extract chapter title
            ch_title = extract_chapter_title(ch_outline, ch)

            # Next chapter info for continuity
            next_ch_outline = extract_next_chapter_outline(outline_text, ch)

            # Parse beats
            beats = extract_chapter_beats(ch_outline)

            # Setup previous tail context
            prev_tail = load_previous_chapter_tail(CHAPTERS_DIR, ch)

            import shutil
            drafted = False
            best_draft_text = ""
            best_draft_score = -1.0
            
            for attempt in range(1, max_attempts + 1):
                print(f"\n--- Chapter {ch} - Attempt {attempt}/{max_attempts} ---")
                
                # Ensure clean tmp_dir for this attempt
                tmp_dir = BASE_DIR / "logs" / "tmp_draft"
                if tmp_dir.exists():
                    shutil.rmtree(tmp_dir)
                tmp_dir.mkdir(parents=True, exist_ok=True)
                
                chapter_raw_text = ""
                
                # Phase 1: Modular Beat Generation (Drafting ONLY)
                if beats:
                    chapter_raw_text = run_beat_drafting(
                        tmp_dir=tmp_dir,
                        ch=ch,
                        ch_title=ch_title,
                        beats=beats,
                        prev_tail=prev_tail,
                        voice_text=voice_text,
                        world_text=world_text,
                        canon_text=canon_text,
                        characters_text=characters_text,
                        drafting_agent=drafting_agent
                    )
                else:
                    chapter_raw_text = run_chapter_fallback_drafting(
                        tmp_dir=tmp_dir,
                        ch=ch,
                        ch_outline=ch_outline,
                        prev_tail=prev_tail,
                        characters_text=characters_text,
                        drafting_agent=drafting_agent
                    )

                # Phase 2: Run Independent Critics
                run_critic_agents(
                    tmp_dir=tmp_dir,
                    critics_roles=self.critics_roles,
                    chapter_raw_text=chapter_raw_text,
                    lore_data=lore_data,
                    slop_rules=slop_rules,
                    factory=factory
                )

                # Phase 3: Sequential Synthesis
                current_text, plan = run_sequential_synthesis(
                    tmp_dir=tmp_dir,
                    chapter_raw_text=chapter_raw_text,
                    factory=factory
                )
                
                # Clean up title and metadata from Python side just in case
                lines = current_text.split("\n")
                clean_lines = []
                title_kept = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        if stripped.startswith("# ") and not title_kept:
                            clean_lines.append(line)
                            title_kept = True
                    else:
                        clean_lines.append(line)
                final_chapter_text = "\n".join(clean_lines).strip()
                
                # Write to target chapter file
                ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
                ch_file.parent.mkdir(exist_ok=True)
                ch_file.write_text(final_chapter_text, encoding="utf-8")
                
                # Archive the attempt directory to logs/generation_attempts/
                attempts_dir = BASE_DIR / "logs" / "generation_attempts" / f"ch{ch:02d}_attempt{attempt:02d}"
                if attempts_dir.exists():
                    shutil.rmtree(attempts_dir)
                attempts_dir.mkdir(parents=True, exist_ok=True)
                for item in tmp_dir.glob("*"):
                    if item.is_file():
                        shutil.copy(item, attempts_dir / item.name)
                # Also save the final version we got in that attempts directory
                (attempts_dir / f"ch_{ch:02d}_final_attempt.md").write_text(final_chapter_text, encoding="utf-8")
                
                # Phase 4: Evaluate
                print(f"[DraftChaptersStep] Evaluating Chapter {ch}...")
                eval_res = evaluate_chapter(ch)
                score = eval_res.get("overall_score", 0.0)
                print(f"[DraftChaptersStep] Chapter {ch} Evaluation Score: {score}")
                
                # Save evaluation result to the attempt log
                (attempts_dir / "evaluation.json").write_text(json.dumps(eval_res, indent=2, ensure_ascii=False), encoding="utf-8")
                
                if score > best_draft_score:
                    best_draft_score = score
                    best_draft_text = final_chapter_text
                    
                if score >= threshold:
                    # Run continuity validation via subprocess
                    print("[DraftChaptersStep] Running global continuity validation...")
                    cont_res = subprocess.run(
                        [sys.executable, "verify_continuity.py", "--strict", "--threshold", "7.0"],
                        capture_output=True,
                        text=True,
                        cwd=str(BASE_DIR)
                    )
                    
                    if cont_res.returncode == 0:
                        print(f"[DraftChaptersStep] Continuity passed for Chapter {ch}!")
                        subprocess.run(["git", "add", f"chapters/ch_{ch:02d}.md"], cwd=str(BASE_DIR))
                        
                        # Update state
                        state["chapters_drafted"] = ch
                        state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
                        subprocess.run(["git", "add", "book_data/state.json"], cwd=str(BASE_DIR))
                        
                        commit_msg = f"ch{ch:02d}: score {score} (attempt {attempt})"
                        subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(BASE_DIR))
                        
                        print("[DraftChaptersStep] Pushing to remote...")
                        subprocess.run(["git", "push"], cwd=str(BASE_DIR))
                        
                        drafted = True
                        break
                    else:
                        print(f"[DraftChaptersStep] Continuity failed (exit {cont_res.returncode}). Output: {cont_res.stdout}")
                else:
                    print(f"[DraftChaptersStep] Score {score} < threshold {threshold}. Discarding attempt.")
                    
            if not drafted:
                print(f"[DraftChaptersStep] WARNING: Chapter {ch} failed to reach threshold after {max_attempts} attempts.")
                print(f"[DraftChaptersStep] Keeping best attempt (score: {best_draft_score})")
                ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
                ch_file.write_text(best_draft_text, encoding="utf-8")
                
                subprocess.run(["git", "add", f"chapters/ch_{ch:02d}.md"], cwd=str(BASE_DIR))
                state["chapters_drafted"] = ch
                state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
                subprocess.run(["git", "add", "book_data/state.json"], cwd=str(BASE_DIR))
                
                commit_msg = f"ch{ch:02d}: forced score {best_draft_score} (fallback)"
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(BASE_DIR))
                subprocess.run(["git", "push"], cwd=str(BASE_DIR))


class BookGenerationPipeline(Pipeline):
    def __init__(self):
        super().__init__("Book Generation Pipeline")
        self.add_step(ResetStep())
        self.add_step(DraftChaptersStep())
