#!/usr/bin/env python3
"""
Adversarial editing pass: ask the judge to CUT 500 words from each chapter.
What gets cut reveals what's weakest. The cut list IS the revision plan.

Usage: python adversarial_edit.py 1        # single chapter
       python adversarial_edit.py all      # all chapters
"""
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from evaluation.json_utils import parse_json_response
from prompt_loader import load_prompt

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# API and models are handled unified via llm.py
CHAPTERS_DIR = BASE_DIR / "chapters"
EDIT_LOG_DIR = BASE_DIR / "logs" / "edit_logs"
EDIT_LOG_DIR.mkdir(parents=True, exist_ok=True)

def call_judge(prompt, max_tokens=8000):
    """Call the unified judge LLM via llm.py and return response text."""
    from llm import call_llm
    system = load_prompt("tools/adversarial_edit_system.txt")
    return call_llm(prompt=prompt, system_prompt=system, temperature=0.3, is_judge=True)

def parse_json(text):
    return parse_json_response(text)

def edit_chapter(ch_num):
    ch_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
    text = ch_path.read_text(encoding="utf-8")
    word_count = len(text.split())
    
    prompt = load_prompt("tools/adversarial_edit_user.txt").format(chapter_text=text, word_count=word_count)
    raw = call_judge(prompt)
    result = parse_json(raw)
    
    # Save log
    log_path = EDIT_LOG_DIR / f"ch{ch_num:02d}_cuts.json"
    log_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    
    return result, word_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python adversarial_edit.py <chapter_num|all>")
        sys.exit(1)
    
    if sys.argv[1] == "all":
        chapters = list(range(1, 25))
    else:
        chapters = [int(sys.argv[1])]
    
    for ch in chapters:
        print(f"\n{'='*50}")
        print(f"EDITING CH {ch}")
        print(f"{'='*50}")
        
        try:
            result, wc = edit_chapter(ch)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        
        cuts = result.get("cuts", [])
        cuttable = result.get("total_cuttable_words", 0)
        fat_pct = result.get("overall_fat_percentage", 0)
        verdict = result.get("one_sentence_verdict", "")
        
        # Count by type
        type_counts = {}
        for c in cuts:
            t = c.get("type", "?")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        print(f"  Words: {wc}")
        print(f"  Cuts found: {len(cuts)}")
        print(f"  Cuttable words: ~{cuttable} ({fat_pct}% fat)")
        print(f"  By type: {type_counts}")
        print(f"  Verdict: {verdict}")
        print(f"  Tightest: {result.get('tightest_passage', '')[:100]}...")
        print(f"  Loosest:  {result.get('loosest_passage', '')[:100]}...")

if __name__ == "__main__":
    main()
