#!/usr/bin/env python3
"""
Rebuild outline.md from the actual chapters.
Reads each chapter, calls the LLM for a structured summary,
and assembles into an outline that reflects the novel as-written.
"""
import os
import sys
import json
import re
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# API and models are handled unified via llm.py
CHAPTERS_DIR = BASE_DIR / "chapters"

def parse_json_response(text):
    """Extract JSON from a response that might have markdown fences or trailing text."""
    text = text.strip()
    
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
    if text.endswith("```"):
        text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass
        
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end < start:
        raise ValueError("No valid JSON object found in response")
        
    json_candidate = text[start:end+1]
    
    try:
        return json.loads(json_candidate, strict=False)
    except json.JSONDecodeError:
        pass
        
    json_candidate = re.sub(r',\s*([}\]])', r'\1', json_candidate)
    
    repaired = repair_json_quotes(json_candidate)
    
    try:
        return json.loads(repaired, strict=False)
    except json.JSONDecodeError as e:
        fixed = re.sub(r'(?<!\\)\n', '\\n', repaired)
        try:
            return json.loads(fixed, strict=False)
        except json.JSONDecodeError:
            raise e

def repair_json_quotes(s):
    result = []
    in_string = False
    escape = False
    i = 0
    n = len(s)
    
    while i < n:
        c = s[i]
        if escape:
            result.append(c)
            escape = False
            i += 1
            continue
            
        if c == '\\':
            result.append(c)
            escape = True
            i += 1
            continue
            
        if c == '"':
            is_structural = False
            
            if not in_string:
                is_structural = True
            else:
                next_non_ws = ""
                j = i + 1
                while j < n:
                    if not s[j].isspace():
                        next_non_ws = s[j]
                        break
                    j += 1
                
                if next_non_ws in [':', '}', ']', ','] or next_non_ws == "":
                    is_structural = True
            
            if is_structural:
                in_string = not in_string
                result.append(c)
            else:
                result.append('\\"')
        else:
            result.append(c)
        i += 1
        
    return "".join(result)

def call_model(prompt, max_tokens=1500):
    """Call the unified judge LLM via llm.py and return response text."""
    from llm import call_llm
    system = (
        "You produce structured outline entries for novel chapters. "
        "Be precise about what HAPPENS, what CHANGES, and what threads are planted/harvested. "
        "Output valid JSON only."
    )
    raw = call_llm(prompt=prompt, system_prompt=system, temperature=0.1, is_judge=True)
    return parse_json_response(raw)

def main():
    # Load supporting docs for context
    characters = (BASE_DIR / "characters.md").read_text()[:3000]
    
    entries = []
    
    ch = 1
    while True:
        path = CHAPTERS_DIR / f"ch_{ch:02d}.md"
        if not path.exists():
            break
            
        text = path.read_text()
        wc = len(text.split())
        
        title_line = text.strip().split('\n')[0].lstrip('# ').strip()
        
        prompt = f"""Analyze this chapter and produce a structured outline entry.

CHAPTER {ch}: "{title_line}" ({wc} words)

{text}

Return JSON with these fields:
- "title": the chapter title (string)
- "location": primary setting (string)
- "characters": list of characters who appear (list of strings)
- "summary": 2-3 sentence summary of what happens (string)
- "beats": list of 3-5 key story beats in order (list of strings)
- "try_fail": the try-fail cycle type: "yes-but", "no-and", "yes-and", or "no-but" (string)
- "plants": foreshadowing threads PLANTED in this chapter (list of strings)
- "harvests": foreshadowing threads PAID OFF in this chapter (list of strings)
- "emotional_arc": one sentence describing the emotional movement (string)
- "chapter_question": the question left open at chapter's end (string)

JSON only, no other text."""

        data = call_model(prompt)
        data["num"] = ch
        data["words"] = wc
        entries.append(data)
        print(f"  {ch:2d}. {title_line} ({wc}w)")
        ch += 1
    
    # Load existing outline header info
    old_outline = (BASE_DIR / "outline.md").read_text()
    
    # Build new outline
    lines = []
    lines.append("# THE SECOND SON OF THE HOUSE OF BELLS")
    lines.append("## Chapter Outline (reflects actual novel as-written)")
    lines.append("")
    lines.append(f"**{len(entries)} chapters, {sum(e['words'] for e in entries):,} words**")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    for e in entries:
        lines.append(f"### Ch {e['num']}: {e['title']}")
        lines.append(f"**{e['words']} words** | **Location:** {e.get('location', 'N/A')}")
        lines.append(f"- **Characters:** {', '.join(e.get('characters', []))}")
        lines.append(f"- **Try-fail cycle:** {e.get('try_fail', 'N/A')}")
        lines.append(f"- **Emotional arc:** {e.get('emotional_arc', 'N/A')}")
        lines.append("")
        lines.append(f"**Summary:** {e.get('summary', 'N/A')}")
        lines.append("")
        lines.append("**Beats:**")
        for b in e.get("beats", []):
            lines.append(f"1. {b}")
        lines.append("")
        if e.get("plants"):
            lines.append("**Plants:**")
            for p in e["plants"]:
                lines.append(f"- {p}")
            lines.append("")
        if e.get("harvests"):
            lines.append("**Harvests:**")
            for h in e["harvests"]:
                lines.append(f"- {h}")
            lines.append("")
        lines.append(f"**Chapter question:** {e.get('chapter_question', 'N/A')}")
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Foreshadowing ledger
    lines.append("## FORESHADOWING LEDGER")
    lines.append("")
    lines.append("| Thread | Planted | Harvested |")
    lines.append("|--------|---------|-----------|")
    
    # Collect all plants and harvests
    all_plants = {}
    all_harvests = {}
    for e in entries:
        for p in e.get("plants", []):
            key = p[:60]
            if key not in all_plants:
                all_plants[key] = []
            all_plants[key].append(e["num"])
        for h in e.get("harvests", []):
            key = h[:60]
            if key not in all_harvests:
                all_harvests[key] = []
            all_harvests[key].append(e["num"])
    
    # Match plants to harvests by keyword overlap
    all_threads = set(list(all_plants.keys()) + list(all_harvests.keys()))
    for thread in sorted(all_threads):
        planted = ", ".join(f"Ch {n}" for n in all_plants.get(thread, []))
        harvested = ", ".join(f"Ch {n}" for n in all_harvests.get(thread, []))
        lines.append(f"| {thread} | {planted} | {harvested} |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Outline rebuilt from actual chapters, Cycle 5.*")
    
    out = '\n'.join(lines)
    (BASE_DIR / "outline.md").write_text(out)
    print(f"\nSaved outline.md ({len(out.split())} words)")

if __name__ == "__main__":
    main()
