#!/usr/bin/env python3
"""
resolve_continuity.py — Closed-loop continuity router.
Parses continuity_report.json and latest individual chapter evaluations,
generates a corrective editorial.md, backs up the old one, and triggers run_editorial.py.
"""
import os
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")

def get_latest_chapter_score(ch_num: int) -> float:
    eval_logs_dir = BASE_DIR / "logs" / "eval_logs"
    if not eval_logs_dir.exists():
        return 0.0
    log_files = sorted(eval_logs_dir.glob(f"*_ch{ch_num:02d}.json"))
    if not log_files:
        # Fallback to older chXX format or check for double digits
        log_files = sorted(eval_logs_dir.glob(f"*_ch{ch_num}.json"))
    if not log_files:
        return 0.0
    try:
        data = json.loads(log_files[-1].read_text(encoding="utf-8"))
        return data.get("overall_score", 0.0)
    except Exception:
        return 0.0

def backup_editorial():
    editorial_path = BASE_DIR / "book_data" / "editorial.md"
    if not editorial_path.exists():
        return
    edit_logs_dir = BASE_DIR / "logs" / "edit_logs"
    edit_logs_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = edit_logs_dir / f"editorial_cycle_{timestamp}.md"
    
    backup_path.write_text(editorial_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[INFO] Backed up current editorial.md to: {backup_path.name}")

def main():
    report_path = BASE_DIR / "logs" / "eval_logs" / "continuity_report.json"
    
    if not report_path.exists():
        print("[INFO] Continuity report not found. Running verify_continuity.py first...")
        res = subprocess.run(["uv", "run", "python", "verify_continuity.py"], capture_output=True, text=True)
        if not report_path.exists():
            print(f"[ERROR] Failed to generate continuity report: {res.stderr}")
            sys.exit(1)
            
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Failed to read/parse continuity report: {e}")
        sys.exit(1)
        
    score = report.get("continuity_score", 10.0)
    inconsistencies = report.get("inconsistencies", [])
    
    print(f"[INFO] Current global continuity score: {score:.1f}/10.0")
    
    # We allow running if score < 7.5 or if there are high/medium severity issues
    has_critical_issues = any(inc.get("severity") in ["high", "medium"] for inc in inconsistencies)
    if score >= 7.5 and not has_critical_issues:
        print("[SUCCESS] Continuity score is satisfactory (>= 7.5) and no critical issues exist. No corrections needed.")
        sys.exit(0)
        
    print(f"[INFO] Found {len(inconsistencies)} issues. Generating corrective editorial.md...")
    
    # Backup old editorial
    backup_editorial()
    
def load_continuity_config() -> dict:
    from prompt_loader import get_active_language, PROMPTS_DIR
    lang = get_active_language()
    config_file = PROMPTS_DIR / lang / "continuity.json"
    if not config_file.exists() and lang != "EN":
        config_file = PROMPTS_DIR / "EN" / "continuity.json"
    if not config_file.exists():
        # Minimal fallback
        return {
            "general_rules": [
                "- Ensure all chapter output is written in high-quality, standard English (EN) only.",
                "- Avoid common AI fiction tropes, structural repetitions, and rhetorical tics.",
                "- Maintain strict consistency of location names and character lore (Helena's apartment in Oerlikon on the 5th floor, door 5C; CERN hard drive safe at ETH room 3.17)."
            ],
            "divergence_rules": {
                "6_7": {
                    "6": "Focus strictly on the meeting with Mirela at the Kaffeehaus in Bern and obtain the confidential notes.",
                    "7": "Narrative Divergence: DO NOT repeat the train trip to Bern or the meeting with Mirela. The chapter must focus entirely on Elisa's return to Zurich that same afternoon, analyzing the physical notes on the train back, and conducting the full and tense video conference with Father Tomás Delgado."
                },
                "14_15": {
                    "14": "Focus on the discovery of Marcus's preprint and the dramatic physical/emotional confrontation in the office.",
                    "15": "Narrative Divergence: DO NOT repeat the confrontation with Marcus. The chapter must focus on Elisa deeply investigating Evromind and Yuki Tanaka to discover who bribed Marcus, expanding the corporate espionage subplot before the call from Dmitri Volsky."
                }
            },
            "templates": {
                "quality_improvement": "Quality Improvement: The previous draft received a low score ({score:.2f}). Eliminate AI writing tics, tropes, and improve pacing and Elisa's inner thoughts.",
                "continuity_correction": "Continuity Correction ({severity} Severity): {desc} -> {fix}",
                "general_directives_header": "# General Directives",
                "chapter_header": "# Chapter {ch}",
                "affects_downstream": "- affects_downstream: {downstream}",
                "generic_update": "- Apply general style and consistency corrections to this chapter."
            }
        }
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    report_path = BASE_DIR / "eval_logs" / "continuity_report.json"
    
    if not report_path.exists():
        print("[INFO] Continuity report not found. Running verify_continuity.py first...")
        res = subprocess.run(["uv", "run", "python", "verify_continuity.py"], capture_output=True, text=True)
        if not report_path.exists():
            print(f"[ERROR] Failed to generate continuity report: {res.stderr}")
            sys.exit(1)
            
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERROR] Failed to read/parse continuity report: {e}")
        sys.exit(1)
        
    score = report.get("continuity_score", 10.0)
    inconsistencies = report.get("inconsistencies", [])
    
    print(f"[INFO] Current global continuity score: {score:.1f}/10.0")
    
    # We allow running if score < 7.5 or if there are high/medium severity issues
    has_critical_issues = any(inc.get("severity") in ["high", "medium"] for inc in inconsistencies)
    if score >= 7.5 and not has_critical_issues:
        print("[SUCCESS] Continuity score is satisfactory (>= 7.5) and no critical issues exist. No corrections needed.")
        sys.exit(0)
        
    print(f"[INFO] Found {len(inconsistencies)} issues. Generating corrective editorial.md...")
    
    # Backup old editorial
    backup_editorial()
    
    # 1. Map directives and downstream impacts
    directives = {} # ch_num -> list of strings
    downstream = {} # ch_num -> set of ints
    affected_chapters = set()
    
    # Load continuity configuration
    config = load_continuity_config()
    general_rules = config.get("general_rules", [])
    divergence_rules_raw = config.get("divergence_rules", {})
    templates = config.get("templates", {})
    
    # Convert string keys like "6_7" to tuples (6, 7)
    divergence_rules = {}
    for k, v in divergence_rules_raw.items():
        try:
            parts = tuple(int(x) for x in k.split("_"))
            divergence_rules[parts] = {int(ch_k): ch_v for ch_k, ch_v in v.items()}
        except Exception:
            pass
    
    for inc in inconsistencies:
        severity = inc.get("severity", "low")
        if severity not in ["high", "medium"]:
            continue
            
        chapters = sorted(inc.get("chapters", []))
        if not chapters:
            continue
            
        ch_base = chapters[0]
        affected_chapters.update(chapters)
        
        if ch_base not in directives:
            directives[ch_base] = []
        if ch_base not in downstream:
            downstream[ch_base] = set()
            
        # Register downstream chapters
        for c in chapters[1:]:
            downstream[ch_base].add(c)
            
        desc = inc.get("description", "")
        fix = inc.get("suggested_fix", "")
        
        # Check if this is a known duplicate pair
        is_duplicate_pair = False
        for pair, rules in divergence_rules.items():
            if set(chapters) == set(pair):
                is_duplicate_pair = True
                # Inject custom narrative divergence instructions
                for ch_in_pair in pair:
                    if ch_in_pair not in directives:
                        directives[ch_in_pair] = []
                    directives[ch_in_pair].append(rules[ch_in_pair])
                    affected_chapters.add(ch_in_pair)
                break
                
        if not is_duplicate_pair:
            # Standard continuity directive
            continuity_correction_template = templates.get("continuity_correction", "Continuity Correction ({severity} Severity): {desc} -> {fix}")
            directive_msg = continuity_correction_template.format(
                severity=severity.upper(),
                desc=desc,
                fix=fix
            )
            directives[ch_base].append(directive_msg)
            
    # 2. Add chapters with low scores (< 7.0) to queue
    chapters_dir = BASE_DIR / "chapters"
    existing_chapters = []
    if chapters_dir.exists():
        for f in chapters_dir.glob("ch_*.md"):
            m = re.search(r"ch_(\d+)\.md", f.name)
            if m:
                existing_chapters.append(int(m.group(1)))
    existing_chapters = sorted(existing_chapters)
    
    for ch in existing_chapters:
        score = get_latest_chapter_score(ch)
        if score > 0.0 and score < 7.0:
            print(f"[INFO] Chapter {ch:02d} scheduled for style/quality correction (Score: {score:.2f} < 7.0)")
            affected_chapters.add(ch)
            if ch not in directives:
                directives[ch] = []
            quality_improvement_template = templates.get("quality_improvement", "Quality Improvement: The previous draft received a low score ({score:.2f}). Eliminate AI writing tics, tropes...")
            directives[ch].append(quality_improvement_template.format(score=score))

    if not affected_chapters:
        print("[INFO] No chapters affected by high/medium issues or low scores. Exiting.")
        sys.exit(0)
        
    # 3. Build editorial.md content
    general_directives_header = templates.get("general_directives_header", "# General Directives")
    editorial_lines = [
        general_directives_header,
    ] + general_rules + [""]
    
    for ch in sorted(list(affected_chapters)):
        chapter_header_template = templates.get("chapter_header", "# Chapter {ch}")
        editorial_lines.append(chapter_header_template.format(ch=ch))
        
        # affects_downstream
        ch_downstream = sorted(list(downstream.get(ch, [])))
        if ch_downstream:
            ds_str = ", ".join(str(c) for c in ch_downstream)
            affects_downstream_template = templates.get("affects_downstream", "- affects_downstream: {downstream}")
            editorial_lines.append(affects_downstream_template.format(downstream=ds_str))
            
        ch_directives = directives.get(ch, [])
        if ch_directives:
            for d in ch_directives:
                editorial_lines.append(f"- {d}")
        else:
            generic_update = templates.get("generic_update", "- Apply general style and consistency corrections to this chapter.")
            editorial_lines.append(generic_update)
            
        editorial_lines.append("")
        
    # Write to editorial.md
    editorial_path = BASE_DIR / "book_data" / "editorial.md"
    editorial_path.write_text("\n".join(editorial_lines), encoding="utf-8")
    print(f"[SUCCESS] New corrective editorial.md generated successfully at: {editorial_path.name}")
    
    # 4. Trigger run_editorial.py with affected chapters
    ch_list_str = ",".join(str(c) for c in sorted(list(affected_chapters)))
    cmd = ["uv", "run", "python", "run_editorial.py", "-c", ch_list_str]
    print(f"[INFO] Triggering reprocess queue: {' '.join(cmd)}")
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
