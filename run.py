#!/usr/bin/env python3
"""
run.py — Unified pipeline executor for the autobook project.
Supports launching book generation or editorial revision pipelines.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from pipelines.book_generation import BookGenerationPipeline
from pipelines.editorial_revision import EditorialRevisionPipeline

def parse_chapters(ch_str: str) -> list:
    """Parse comma-separated integers or ranges (e.g. '1-3,5,7')."""
    if not ch_str:
        return []
    nums = set()
    for part in ch_str.split(','):
        part = part.strip()
        if not part:
            continue
        if '-' in part:
            try:
                start, end = part.split('-', 1)
                for i in range(int(start.strip()), int(end.strip()) + 1):
                    nums.add(i)
            except ValueError:
                print(f"[Error] Invalid range: '{part}'", file=sys.stderr)
        else:
            try:
                nums.add(int(part))
            except ValueError:
                print(f"[Error] Invalid chapter: '{part}'", file=sys.stderr)
    return sorted(list(nums))

def main():
    parser = argparse.ArgumentParser(description="Unified Autobook Pipeline Orchestrator")
    parser.add_argument(
        "--pipeline",
        choices=["book_generation", "editorial_revision"],
        required=True,
        help="Pipeline workflow to execute"
    )
    parser.add_argument(
        "--from-scratch",
        action="store_true",
        help="Reset progress and start writing/planning from scratch"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Bypass confirmation prompts and auto-approve tasks"
    )
    parser.add_argument(
        "--chapter",
        type=str,
        default=None,
        help="Specific chapter(s) to run (e.g., '1-4', '5,7')"
    )

    args = parser.parse_args()

    # Build execution context
    context = {
        "from_scratch": args.from_scratch,
        "yes": args.yes,
    }
    
    if args.chapter:
        context["chapters"] = parse_chapters(args.chapter)

    # Instantiate the selected pipeline
    if args.pipeline == "book_generation":
        pipeline = BookGenerationPipeline()
    elif args.pipeline == "editorial_revision":
        pipeline = EditorialRevisionPipeline()
    else:
        print(f"[Error] Unknown pipeline: '{args.pipeline}'", file=sys.stderr)
        sys.exit(1)

    try:
        pipeline.run(context)
    except Exception as e:
        print(f"[Error] Pipeline execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
