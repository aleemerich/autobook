#!/usr/bin/env python3
"""
pipelines/editorial_revision.py — Editorial Revision Pipeline.
Parses editorial.md, performs dynamic and corrective chapter rewriting,
and validates improvements against the evaluation harness.
"""

import os
from pathlib import Path
from typing import Dict, Any

from pipelines.base import Step, Pipeline
from evaluate import evaluate_chapter
from pipelines.editorial_revision_steps import (
    load_chapter_text,
    list_chapter_files,
    filter_chapter_files,
    parse_chapter_number,
    format_eval_feedback,
    build_initial_brief,
    build_corrective_brief,
    write_temp_brief,
    remove_temp_brief,
    execute_gen_revision,
    is_revision_size_acceptable,
    build_size_guard_eval_data,
    is_quality_target_reached,
    is_better_than_fallback,
    commit_revised_chapter,
    run_final_maintenance,
    load_editorial_config,  # noqa: F401 - re-exported for backward compatibility
    get_retry_temperature,
    load_editorial_markdown,
)

BASE_DIR = Path(__file__).parent.parent.resolve()
CHAPTERS_DIR = BASE_DIR / "chapters"


class LoadEditorialStep(Step):
    def __init__(self):
        super().__init__("Load and Parse editorial.md")

    def run(self, context: Dict[str, Any]) -> None:
        print("[LoadEditorialStep] Parsing editorial.md...")
        parsed = load_editorial_markdown()
        context["general_notes"] = parsed.get("general_notes", "")
        context["chapters_briefs"] = parsed.get("chapters", {})
        print(f"[LoadEditorialStep] Found general notes and {len(context['chapters_briefs'])} chapter-specific brief(s).")


class ExecuteEditorialStep(Step):
    def __init__(self):
        super().__init__("Execute Editorial Rewrites")

    def run(self, context: Dict[str, Any]) -> None:
        chapters_briefs = context.get("chapters_briefs", {})
        general_notes = context.get("general_notes", "")

        # Discover and filter chapter files using helpers
        all_chapter_files = list_chapter_files(CHAPTERS_DIR)

        # Determine chapters to process
        target_chapters = context.get("chapters")
        if not target_chapters:
            # Fallback: process all chapters specified in editorial.md
            target_chapters = sorted(list(chapters_briefs.keys()))

        filtered_files = filter_chapter_files(all_chapter_files, target_chapters)
        filtered_set = {parse_chapter_number(f) for f in filtered_files}

        if not target_chapters:
            print("[ExecuteEditorialStep] No chapters specified and no chapters found in editorial.md. Skipping.")
            return

        print(f"[ExecuteEditorialStep] Chapters to process: {target_chapters}")

        num_retries = int(os.environ.get("NUM_EDITORIAL_RETRIES", 5))

        for ch_num in target_chapters:
            print("\n======================================")
            print(f"Processing Editorial Revision: Chapter {ch_num}")
            print("======================================")

            ch_file_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
            if ch_num not in filtered_set:
                print(f"[ExecuteEditorialStep] Chapter file {ch_file_path} does not exist. Skipping.")
                continue

            original_text = load_chapter_text(ch_file_path)
            temp_brief_path = BASE_DIR / f"ch{ch_num:02d}_brief_temp.txt"
            corrective_brief_path = BASE_DIR / f"ch{ch_num:02d}_corrective_temp.txt"

            try:
                # Evaluate baseline
                print("[ExecuteEditorialStep] Measuring pre-editorial baseline score...")
                eval_data = evaluate_chapter(ch_num)
                pre_score = eval_data.get("overall_score", 0.0)
                pre_slop = eval_data.get("slop", {}).get("slop_penalty", 0.0)
                print(f"[ExecuteEditorialStep] Baseline Score: {pre_score} (Slop: {pre_slop})")

                task = chapters_briefs.get(ch_num, {"brief": "Apply general directives.", "type": "punctual", "affects_downstream": []})

                # Create a temporary brief combining chapter-specific brief + general notes
                brief_content = build_initial_brief(task["brief"], general_notes)
                write_temp_brief(temp_brief_path, brief_content)

                # Initial run of revision
                print(f"[ExecuteEditorialStep] Generating initial rewrite for Chapter {ch_num}...")
                execute_gen_revision(ch_num, temp_brief_path, 0.8, BASE_DIR)

                # Evaluate the first draft
                candidate_text = load_chapter_text(ch_file_path)
                if not is_revision_size_acceptable(original_text, candidate_text):
                    print("[ExecuteEditorialStep] Attempt 1 rejected by size guard before evaluation.")
                    eval_data = build_size_guard_eval_data(original_text, candidate_text)
                    ch_file_path.write_text(original_text, encoding="utf-8")
                else:
                    eval_data = evaluate_chapter(ch_num)
                post_score = eval_data.get("overall_score", 0.0)
                slop_penalty = eval_data.get("slop", {}).get("slop_penalty", 0.0)

                success = False
                best_fallback_text = load_chapter_text(ch_file_path) if post_score > 0 else original_text
                best_fallback_score = post_score
                best_fallback_slop = slop_penalty

                print(f"[ExecuteEditorialStep] Attempt 1 Score: {post_score} (Slop: {slop_penalty})")

                if is_quality_target_reached(post_score, pre_score, slop_penalty):
                    success = True
                    print("[ExecuteEditorialStep] Attempt 1 reached target quality.")
                else:
                    # Start retry feedback loops
                    for retry_idx in range(1, num_retries + 1):
                        print(f"[ExecuteEditorialStep] Corrective Loop {retry_idx}/{num_retries} for Chapter {ch_num}...")

                        feedback_str = format_eval_feedback(eval_data, retry_idx)
                        corrective_brief_content = build_corrective_brief(
                            ch_num, retry_idx, feedback_str, task["brief"], general_notes
                        )

                        write_temp_brief(corrective_brief_path, corrective_brief_content)

                        retry_temp = get_retry_temperature(retry_idx)
                        execute_gen_revision(ch_num, corrective_brief_path, retry_temp, BASE_DIR)
                        remove_temp_brief(corrective_brief_path)

                        # Evaluate again
                        candidate_text = load_chapter_text(ch_file_path)
                        if not is_revision_size_acceptable(original_text, candidate_text):
                            print(
                                f"[ExecuteEditorialStep] Corrective Loop {retry_idx} rejected by size guard before evaluation."
                            )
                            eval_data = build_size_guard_eval_data(original_text, candidate_text)
                            ch_file_path.write_text(best_fallback_text, encoding="utf-8")
                        else:
                            eval_data = evaluate_chapter(ch_num)
                        post_score = eval_data.get("overall_score", 0.0)
                        slop_penalty = eval_data.get("slop", {}).get("slop_penalty", 0.0)
                        print(f"[ExecuteEditorialStep] Corrective Loop {retry_idx} Score: {post_score} (Slop: {slop_penalty})")

                        if is_quality_target_reached(post_score, pre_score, slop_penalty):
                            success = True
                            print("[ExecuteEditorialStep] Corrective loop successfully hit quality goals.")
                            break
                        else:
                            if is_better_than_fallback(post_score, best_fallback_score, slop_penalty, best_fallback_slop):
                                best_fallback_text = load_chapter_text(ch_file_path)
                                best_fallback_score = post_score
                                best_fallback_slop = slop_penalty
                            else:
                                # Revert to the best text so far before next iteration
                                ch_file_path.write_text(best_fallback_text, encoding="utf-8")

                # Finalize kept version
                if success or best_fallback_score >= pre_score:
                    final_score = post_score if success else best_fallback_score
                    if not success:
                        ch_file_path.write_text(best_fallback_text, encoding="utf-8")

                    commit_revised_chapter(ch_num, pre_score, final_score, BASE_DIR)
                else:
                    print("[ExecuteEditorialStep] All attempts failed to improve. Reverting to original pristine text.")
                    ch_file_path.write_text(original_text, encoding="utf-8")
            except Exception:
                ch_file_path.write_text(original_text, encoding="utf-8")
                raise
            finally:
                remove_temp_brief(temp_brief_path)
                remove_temp_brief(corrective_brief_path)

        # Consolidate outline and manuscript
        run_final_maintenance(BASE_DIR)


class EditorialRevisionPipeline(Pipeline):
    def __init__(self):
        super().__init__("Editorial Revision Pipeline")
        self.add_step(LoadEditorialStep())
        self.add_step(ExecuteEditorialStep())
