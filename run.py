#!/usr/bin/env python3
"""
run.py — Unified pipeline executor for the autobook project.
Supports launching book generation or editorial revision pipelines.
"""

import sys
import argparse
import datetime
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

from pipelines.registry import list_pipelines, get_pipeline_spec

class Tee:
    def __init__(self, filename, stream):
        self.file = open(filename, 'a', encoding='utf-8')
        self.stream = stream

    def write(self, data):
        self.file.write(data)
        self.file.flush()
        self.stream.write(data)
        self.stream.flush()

    def flush(self):
        self.file.flush()
        self.stream.flush()

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

def main(argv: list[str] | None = None) -> None:
    # Setup logging to logs/pipeline.log
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pipeline.log"
    
    # Write a run header
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n--- Pipeline Run Started at {datetime.datetime.now().isoformat()} ---\n")
        
    if not isinstance(sys.stdout, Tee):
        sys.stdout = Tee(str(log_file), sys.stdout)
    if not isinstance(sys.stderr, Tee):
        sys.stderr = Tee(str(log_file), sys.stderr)

    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0:
        from cli.wizard import main as wizard_main
        wizard_main()
        return

    parser = argparse.ArgumentParser(description="Unified Autobook Pipeline Orchestrator")
    parser.add_argument(
        "--pipeline",
        choices=list(list_pipelines().keys()),
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

    args = parser.parse_args(argv)

    # Build execution context
    context = {
        "from_scratch": args.from_scratch,
        "yes": args.yes,
    }
    
    if args.chapter:
        context["chapters"] = parse_chapters(args.chapter)

    # Instantiate the selected pipeline and check branch guards
    try:
        spec = get_pipeline_spec(args.pipeline)
    except KeyError:
        print(f"[Error] Unknown pipeline: '{args.pipeline}'", file=sys.stderr)
        sys.exit(1)

    if spec.requires_work_branch:
        try:
            from workspace.branching import ensure_not_main_for_generation
            ensure_not_main_for_generation()
        except ValueError as e:
            print(f"[Error] {e}", file=sys.stderr)
            sys.exit(1)

    pipeline = spec.factory()

    try:
        pipeline.run(context)
    except Exception as e:
        print(f"[Error] Pipeline execution failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
