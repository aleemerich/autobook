#!/usr/bin/env python3
"""
evaluate.py -- Novel evaluation harness.

Usage:
  python evaluate.py --phase=foundation    # Score planning docs only
  python evaluate.py --chapter=5           # Score a single chapter
  python evaluate.py --full                # Score the entire novel

Output: structured scores to stdout + eval_logs/<timestamp>.json

This file is READ-ONLY during autonomous runs. The human edits it
to tune what "good" means. The agent treats it as a black box.
"""

import argparse
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).parent

# Load .env file if present
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# Judge uses Opus 4.6 (harsh, critical). Writer uses Sonnet 4.6 (fast, long context).
# Intentionally different to avoid self-congratulation.

CHAPTERS_DIR = BASE_DIR / "chapters"
EVAL_LOG_DIR = BASE_DIR / "logs" / "eval_logs"
EVAL_LOG_DIR.mkdir(parents=True, exist_ok=True)


from evaluation.io import (
    load_file as _load_file,
    load_layer_files as _load_layer_files,
    load_chapter as _load_chapter,
    load_all_chapters as _load_all_chapters
)
from evaluation.judge import call_judge
from evaluation.json_utils import parse_json_response, validate_and_repair_json
from evaluation.prompts import FOUNDATION_PROMPT, CHAPTER_PROMPT, CHAPTER_PROMPT_REDUCED, CHAPTER_PROMPT_MINIMAL, FULL_NOVEL_PROMPT
from evaluation.reports import save_chapter_evaluation_logs
from evaluation.slop import slop_score


def load_file(path):
    """Compatibility wrapper for loading a text file."""
    return _load_file(path)


def load_layer_files():
    """Compatibility wrapper using evaluate.BASE_DIR."""
    return _load_layer_files(BASE_DIR)


def load_chapter(n):
    """Compatibility wrapper using evaluate.CHAPTERS_DIR."""
    return _load_chapter(n, CHAPTERS_DIR)


def load_all_chapters():
    """Compatibility wrapper using evaluate.CHAPTERS_DIR."""
    return _load_all_chapters(CHAPTERS_DIR)


# --- Foundation Evaluation ---



def evaluate_foundation():
    layers = load_layer_files()
    prompt = FOUNDATION_PROMPT.format(**layers)
    raw = call_judge(prompt, max_tokens=16000)
    return parse_json_response(raw)


# --- Chapter Evaluation ---



def evaluate_chapter(chapter_num):
    layers = load_layer_files()
    chapter_text = load_chapter(chapter_num)
    if not chapter_text.strip():
        return {"error": f"Chapter {chapter_num} is empty or missing",
                "overall_score": 0.0}

    # Resolve list of judge models
    judge_models_str = os.environ.get("AUTOBOOK_JUDGE_MODEL", "openrouter/free")
    models_list = [m.strip() for m in judge_models_str.split(",") if m.strip()]
    if not models_list:
        models_list = ["openrouter/free"]

    # Extract this chapter's outline entry (rough heuristic)
    outline = layers["outline"]
    ch_pattern = rf'###\s*Ch\s*{chapter_num}\b.*?(?=###\s*Ch\s*\d|## Act|## Foreshadowing|$)'
    ch_match = re.search(ch_pattern, outline, re.DOTALL)
    chapter_outline = ch_match.group(0) if ch_match else "(outline entry not found)"

    # Prepare prompt data for different cycles
    voice_full = layers["voice"]
    voice_reduced = voice_full[:1500] if len(voice_full) > 1500 else voice_full

    world_full = layers["world"]
    world_c1 = world_full[:4000] if len(world_full) > 4000 else world_full
    world_c2 = world_full[:1500] if len(world_full) > 1500 else world_full

    chars_full = layers["characters"]
    chars_reduced = chars_full[:1500] if len(chars_full) > 1500 else chars_full

    canon_full = layers["canon"]
    canon_reduced = canon_full[:1500] if len(canon_full) > 1500 else canon_full

    prev_text = load_chapter(chapter_num - 1) if chapter_num > 1 else "(first chapter)"
    prev_tail_c1 = prev_text[-3000:] if len(prev_text) > 3000 else prev_text
    prev_tail_c2 = prev_text[-1000:] if len(prev_text) > 1000 else prev_text

    result = None

    # Nested Loop: 3 Cycles of Degradation, each trying the models in list order
    for cycle in range(1, 4):
        print(f"[INFO] Beginning evaluation Cycle {cycle} for Chapter {chapter_num}...", file=sys.stderr)
        
        # Build prompt based on current cycle
        if cycle == 1:
            prompt = CHAPTER_PROMPT.format(
                voice=voice_full,
                world=world_c1,
                characters=chars_full,
                canon=canon_full,
                chapter_outline=chapter_outline,
                prev_chapter_tail=prev_tail_c1,
                chapter_text=chapter_text,
            )
        elif cycle == 2:
            prompt = CHAPTER_PROMPT_REDUCED.format(
                voice=voice_reduced,
                world=world_c2,
                characters=chars_reduced,
                canon=canon_reduced,
                chapter_outline=chapter_outline,
                prev_chapter_tail=prev_tail_c2,
                chapter_text=chapter_text,
            )
        else:
            prompt = CHAPTER_PROMPT_MINIMAL.format(
                chapter_outline=chapter_outline,
                chapter_text=chapter_text,
            )

        for model in models_list:
            print(f"[INFO] Trying model '{model}' in Cycle {cycle}...", file=sys.stderr)
            try:
                raw = call_judge(prompt, override_model=model)
                parsed = validate_and_repair_json(raw, "overall_score")
                if parsed is not None:
                    print(f"[INFO] Successfully obtained valid evaluation from model '{model}' (Cycle {cycle})!", file=sys.stderr)
                    result = parsed
                    break
            except Exception as e:
                print(f"WARNING: Model '{model}' failed in Cycle {cycle}: {e}", file=sys.stderr)
            
            # Rotation is immediate: no sleep/delay of 60s
            print(f"[INFO] Model '{model}' failed or returned invalid JSON. Rotating to next model...", file=sys.stderr)
            
        if result is not None:
            break

    if result is None:
        raise RuntimeError(f"FATAL ERROR: All evaluation cycles and models failed for Chapter {chapter_num}.")

    # Mechanical slop check -- adjusts score independently of judge
    slop = slop_score(chapter_text)
    result["slop"] = slop
    if "overall_score" in result:
        adjusted = max(0, result["overall_score"] - slop["slop_penalty"])
        result["raw_judge_score"] = result["overall_score"]
        result["overall_score"] = round(adjusted, 2)

    save_chapter_evaluation_logs(BASE_DIR, chapter_num, result)

    return result


# --- Full Novel Evaluation ---



def evaluate_full():
    layers = load_layer_files()
    chapters = load_all_chapters()

    if not chapters:
        return {"error": "No chapters found", "novel_score": 0.0}

    # Build chapter summaries (first/last 500 chars of each)
    summaries = []
    for num in sorted(chapters.keys()):
        text = chapters[num]
        word_count = len(text.split())
        head = text[:500]
        tail = text[-500:] if len(text) > 500 else ""
        summaries.append(
            f"Chapter {num} ({word_count} words):\n"
            f"  Opening: {head}...\n"
            f"  Closing: ...{tail}\n"
        )

    prompt = FULL_NOVEL_PROMPT.format(
        voice=layers["voice"],
        world_summary=layers["world"][:3000],
        characters=layers["characters"],
        outline=layers["outline"],
        chapter_summaries="\n".join(summaries),
    )
    raw = call_judge(prompt)
    return parse_json_response(raw)


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Evaluate the novel")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--phase", choices=["foundation"],
                       help="Evaluate planning documents")
    group.add_argument("--chapter", type=int,
                       help="Evaluate a specific chapter number")
    group.add_argument("--full", action="store_true",
                       help="Evaluate the entire novel")
    args = parser.parse_args()

    if args.phase == "foundation":
        result = evaluate_foundation()
        score_key = "overall_score"
    elif args.chapter is not None:
        result = evaluate_chapter(args.chapter)
        score_key = "overall_score"
    elif args.full:
        result = evaluate_full()
        score_key = "novel_score"

    # Print structured output
    print("---")
    if score_key in result:
        print(f"{score_key}: {result[score_key]}")
    for key, val in result.items():
        if key == score_key:
            continue
        if isinstance(val, dict):
            score_val = val.get('score')
            if score_val is None and 'slop_penalty' in val:
                score_val = f"Penalty: {val['slop_penalty']}"
            if score_val is None:
                score_val = 'N/A'
            print(f"{key}: {score_val} -- {val.get('note', '')}")
        else:
            print(f"{key}: {val}")

    # Save full eval log
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = args.phase or (f"ch{args.chapter:02d}" if args.chapter else "full")
    log_path = EVAL_LOG_DIR / f"{timestamp}_{mode}.json"
    with open(log_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\neval_log: {log_path}")


if __name__ == "__main__":
    main()
