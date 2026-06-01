#!/usr/bin/env python3
"""
run_pipeline.py — Fully automated novel pipeline orchestrator.

Runs the complete autobook pipeline from seed concept to finished novel.
Manages state, git commits, evaluation, and retry logic.

Usage:
  python run_pipeline.py                    # run from current state
  python run_pipeline.py --from-scratch     # start fresh from seed.txt
  python run_pipeline.py --phase foundation # run only foundation
  python run_pipeline.py --phase drafting   # run only drafting
  python run_pipeline.py --phase revision   # run only revision
  python run_pipeline.py --phase export     # run only export
  python run_pipeline.py --max-cycles 4     # limit revision cycles
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

STATE_FILE = BASE_DIR / "state.json"
RESULTS_FILE = BASE_DIR / "results.tsv"
CHAPTERS_DIR = BASE_DIR / "chapters"
BRIEFS_DIR = BASE_DIR / "briefs"
EDIT_LOGS_DIR = BASE_DIR / "edit_logs"
EVAL_LOGS_DIR = BASE_DIR / "eval_logs"

PIPELINE_TIMEOUT = int(os.environ.get("AUTOBOOK_PIPELINE_TIMEOUT", "3600"))

# Fine-grained timeouts, scaling based on AUTOBOOK_PIPELINE_TIMEOUT or manually configured
DRAFT_TIMEOUT = int(os.environ.get("AUTOBOOK_DRAFT_TIMEOUT", str(max(PIPELINE_TIMEOUT, 1200))))
EVAL_TIMEOUT = int(os.environ.get("AUTOBOOK_EVAL_TIMEOUT", str(max(PIPELINE_TIMEOUT // 2, 600))))
REVISION_TIMEOUT = int(os.environ.get("AUTOBOOK_REVISION_TIMEOUT", str(max(PIPELINE_TIMEOUT, 1200))))
ADVERSARIAL_TIMEOUT = int(os.environ.get("AUTOBOOK_ADVERSARIAL_TIMEOUT", str(max(PIPELINE_TIMEOUT, 1800))))
READER_PANEL_TIMEOUT = int(os.environ.get("AUTOBOOK_READER_PANEL_TIMEOUT", str(max(PIPELINE_TIMEOUT, 1200))))
REVIEW_TIMEOUT = int(os.environ.get("AUTOBOOK_REVIEW_TIMEOUT", str(max(PIPELINE_TIMEOUT, 1800))))
EXPORT_TIMEOUT = int(os.environ.get("AUTOBOOK_EXPORT_TIMEOUT", str(max(PIPELINE_TIMEOUT // 2, 600))))

FOUNDATION_THRESHOLD = 7.5
CHAPTER_THRESHOLD = 6.0
MAX_FOUNDATION_ITERS = 20
MAX_CHAPTER_ATTEMPTS = 5
MIN_REVISION_CYCLES = 3
MAX_REVISION_CYCLES = 6
PLATEAU_DELTA = 0.3

PHASE_ORDER = ["ideation", "foundation", "drafting", "revision", "export"]


# ---------------------------------------------------------------------------
# Helpers: state management
# ---------------------------------------------------------------------------

def load_state() -> dict:
    """Load pipeline state from state.json, creating defaults if missing."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return default_state()


def default_state() -> dict:
    return {
        "phase": "ideation",
        "current_focus": "planning",
        "iteration": 0,
        "foundation_score": 0.0,
        "lore_score": 0.0,
        "chapters_drafted": 0,
        "chapters_total": 0,
        "novel_score": 0.0,
        "revision_cycle": 0,
        "debts": [],
        "completed_tasks": [],
        "current_task": ""
    }


def save_state(state: dict):
    """Write state to state.json."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Helpers: logging
# ---------------------------------------------------------------------------

def log_result(commit: str, phase: str, score, word_count: int,
               status: str, description: str):
    """Append a row to results.tsv."""
    header = "commit\tphase\tscore\tword_count\tstatus\tdescription\n"
    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text(header)
    elif RESULTS_FILE.stat().st_size == 0:
        RESULTS_FILE.write_text(header)
    with open(RESULTS_FILE, "a") as f:
        f.write(f"{commit}\t{phase}\t{score}\t{word_count}\t{status}\t{description}\n")


LOG_FILE = BASE_DIR / "pipeline.log"
LOG_TRUNCATE_LIMIT = int(os.environ.get("AUTOBOOK_LOG_TRUNCATE_LIMIT", "300"))

def log_msg(msg: str, level: str = "INFO", truncate: bool = False):
    """
    Unified timestamped logger.
    Appends the full, untruncated message with a timestamp to `pipeline.log`.
    Prints the formatted (and optionally truncated with '...') message to standard output.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clean_msg = str(msg).strip()
    full_log_line = f"[{timestamp}] [{level}] {clean_msg}"
    
    # Always append the full, untruncated message to pipeline.log
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(full_log_line + "\n")
    except Exception as e:
        print(f"[{timestamp}] [WARNING] Failed to write to pipeline.log: {e}", file=sys.stderr)

    # For standard screen output, format and optionally truncate
    screen_line = f"[{timestamp}] {clean_msg}"
    if truncate and len(clean_msg) > LOG_TRUNCATE_LIMIT:
        screen_line = f"[{timestamp}] {clean_msg[:LOG_TRUNCATE_LIMIT]}..."
        
    print(screen_line)


def banner(text: str, char: str = "=", width: int = 60):
    """Log a visual banner with timestamps."""
    border = char * width
    log_msg(border)
    log_msg(f"  {text}")
    log_msg(border)


def step(text: str):
    """Log a step message with a timestamp and visual indicator."""
    log_msg(f"  {text}")


# ---------------------------------------------------------------------------
# Helpers: subprocess execution
# ---------------------------------------------------------------------------

def run_tool(cmd: str, timeout: int = PIPELINE_TIMEOUT, check: bool = False) -> subprocess.CompletedProcess:
    """
    Run a tool as a subprocess, capturing and streaming output in real-time.
    Uses shell=True so callers can pass full command strings.
    Returns CompletedProcess; never raises unless check=True.
    """
    import time
    import select
    
    step(f"RUN: {cmd}")
    start_time = time.time()
    
    try:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(BASE_DIR)
        )
        
        stdout_lines = []
        while True:
            # Check timeout expiration
            elapsed = time.time() - start_time
            if elapsed > timeout:
                process.kill()
                process.wait()
                print(f"    ERROR: timed out after {timeout}s")
                fake = subprocess.CompletedProcess(cmd, returncode=-1, stdout="".join(stdout_lines), stderr="TIMEOUT")
                return fake
                
            # Wait for data to be ready to read, with a 1-second timeout
            rlist, _, _ = select.select([process.stdout], [], [], 1.0)
            
            if process.stdout in rlist:
                line = process.stdout.readline()
                if not line:  # EOF reached
                    break
                stdout_lines.append(line)
                log_msg(line.rstrip('\n'), level="SUBPROCESS", truncate=True)
            elif process.poll() is not None:
                # Process finished and no more data
                break
                
        process.wait()
        stdout = "".join(stdout_lines)
        
        if process.returncode != 0:
            print(f"    WARN: exit code {process.returncode}")
            
        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(
                process.returncode, cmd, stdout, "")
                
        return subprocess.CompletedProcess(cmd, returncode=process.returncode, stdout=stdout, stderr="")
        
    except Exception as e:
        print(f"    FATAL ERROR during subprocess execution: {e}")
        raise


def uv_run(script: str, timeout: int = PIPELINE_TIMEOUT) -> subprocess.CompletedProcess:
    """Shorthand for 'uv run python <script>' from project root."""
    return run_tool(f"uv run python {script}", timeout=timeout)


# ---------------------------------------------------------------------------
# Helpers: git operations
# ---------------------------------------------------------------------------

def git_add_commit(message: str) -> str:
    """Stage all changes and commit. Returns short hash or empty string."""
    run_tool("git add -A")
    result = run_tool(f'git commit -m "{message}" --allow-empty')
    if result.returncode == 0:
        hash_result = run_tool("git rev-parse --short HEAD")
        commit_hash = hash_result.stdout.strip()
        step(f"GIT COMMIT: {commit_hash} — {message}")
        return commit_hash
    else:
        step("GIT: nothing to commit or commit failed")
        return ""


def git_reset_hard(ref: str = "HEAD~1"):
    """Hard reset to discard bad changes."""
    step(f"GIT RESET: {ref}")
    run_tool(f"git reset --hard {ref}")


def git_short_hash() -> str:
    """Get current HEAD short hash."""
    r = run_tool("git rev-parse --short HEAD")
    return r.stdout.strip() if r.returncode == 0 else "unknown"


# ---------------------------------------------------------------------------
# Helpers: score parsing
# ---------------------------------------------------------------------------

def parse_score(stdout: str, key: str = "overall_score") -> float:
    """
    Parse a score from evaluate.py YAML-like stdout output.
    Looks for lines like 'overall_score: 8.0' or 'novel_score: 7.5'.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith(f"{key}:"):
            val = line.split(":", 1)[1].strip()
            try:
                return float(val)
            except ValueError:
                continue
    return -1.0


def parse_lore_score(stdout: str) -> float:
    """Parse lore_score from foundation evaluation output."""
    return parse_score(stdout, "lore_score")


def count_words_in_chapters() -> int:
    """Sum word count across all chapter files."""
    total = 0
    if CHAPTERS_DIR.exists():
        for f in CHAPTERS_DIR.glob("ch_*.md"):
            total += len(f.read_text().split())
    return total


def count_chapter_files() -> int:
    """Count the number of chapter files."""
    if not CHAPTERS_DIR.exists():
        return 0
    return len(list(CHAPTERS_DIR.glob("ch_*.md")))


def get_total_chapters(state: dict) -> int:
    """Determine total chapter count from state or outline."""
    if state.get("chapters_total", 0) > 0:
        return state["chapters_total"]
    # Try to infer from outline.md
    outline = BASE_DIR / "outline.md"
    if outline.exists():
        text = outline.read_text()
        matches = re.findall(r'###\s*Ch(?:apter)?\s*(\d+)', text)
        if matches:
            return max(int(m) for m in matches)
    return 24  # sensible default


# ---------------------------------------------------------------------------
# PHASE 0 — IDEATION (CALDEIRÃO DE IDEIAS)
# ---------------------------------------------------------------------------

def run_ideation(state: dict) -> dict:
    """
    Phase 0: Ideation (Interactive Ideation Cauldron).
    Bypasses if seed.txt exists, or asks 4 interactive questions,
    generates 3 robust concepts, and provides a refinement loop.
    """
    banner("PHASE 0: INTERACTIVE IDEATION CAULDRON", "=")
    
    seed_file = BASE_DIR / "seed.txt"
    
    # 1. Bypass check if seed.txt already exists
    if seed_file.exists() and seed_file.stat().st_size > 10:
        print(f"\n[INFO] Detected existing seed.txt in the directory.")
        try:
            choice = input("Do you want to use this existing seed.txt for generation? [Y/n] ").strip()
            if choice == "" or choice.lower() in ['y', 'yes', 's', 'sim']:
                step("Bypass activated! Using existing seed.txt.")
                state["phase"] = "foundation"
                state["current_focus"] = "planning"
                save_state(state)
                banner("IDEATION COMPLETE — seed.txt preserved")
                return state
        except (KeyboardInterrupt, EOFError):
            print("\n[INFO] Bypass ignored due to cancellation.")
            
    # 2. Pre-generation Questionnaire
    print("\nAnswer the 4 questions below to calibrate your Ideation Cauldron.")
    print("(Simply press Enter to use the default suggestions written in brackets)\n")
    
    try:
        genre_ans = input("1. Genre, Tone & Atmosphere [Cyberpunk biotechnical horror with suspense]: ").strip()
        if not genre_ans:
            genre_ans = "Cyberpunk biotechnical horror with suspense"
            
        spark_ans = input("2. Starting Spark / Image [A biomechanical sea that remembers corpses]: ").strip()
        if not spark_ans:
            spark_ans = "A biomechanical sea that remembers corpses"
            
        cost_ans = input("3. Cost of the Extraordinary [Neural short-circuit and tragic loss of memories]: ").strip()
        if not cost_ans:
            cost_ans = "Neural short-circuit and tragic loss of memories"
            
        protagonist_ans = input("4. Protagonist Focus [A cynical ex-soldier with a corrupted optical implant]: ").strip()
        if not protagonist_ans:
            protagonist_ans = "A cynical ex-soldier with a corrupted optical implant"
    except (KeyboardInterrupt, EOFError):
        print("\nInterview interrupted. Using default parameters.")
        genre_ans = "Cyberpunk biotechnical horror with suspense"
        spark_ans = "A biomechanical sea that remembers corpses"
        cost_ans = "Neural short-circuit and tragic loss of memories"
        protagonist_ans = "A cynical ex-soldier with a corrupted optical implant"

    # 3. Generation Loop (supports Riffing/Regeneration)
    from llm import call_llm
    from seed import SYSTEM_PROMPT
    
    current_prompt = f"""Generate 3 extremely addictive, robust sci-fi/fantasy novel seed concepts based on these user preferences:
- Genre, Tone & Atmosphere: {genre_ans}
- Starting Spark / Image: {spark_ans}
- Speculative Cost: {cost_ans}
- Protagonist Archetype: {protagonist_ans}

Each concept must use elite page-turner and narrative hooking techniques:
1. Hook of Paradox: A compelling hook that sets up an immediate choice/paradox.
2. Curiosity Loops: An underlying conspiracy/secret that forces readers to keep turning pages.
3. Wound/Want/Need/Lie: Backstory trauma (Wound) that shapes a tragic character goal (Want).
4. High Speculative Cost: Limits > powers, severe and irreversible costs of power.

Provide EXACTLY this format for EACH concept:

NUMBER. TITLE
HOOK: [One sentence paradox/compelling hook]
WORLD: [Gritty, sensory details of the hostile world]
MAGIC/COST: [The speculative element and its tragic cost]
TENSION: [Personal vs cosmic conflict driven by Wound and Want]
THE CONSPIRACY: [The underlying mystery/curiosity loop that drives the pages]
THEME: [A deep thematic question with no easy answer]
"""

    while True:
        step("Generating 3 premium seeds with addictive writing techniques...")
        
        result = call_llm(
            prompt=current_prompt,
            system_prompt=SYSTEM_PROMPT,
            temperature=1.0,
            is_judge=False
        )
        
        # Save cauldron file
        cauldron_path = BASE_DIR / "cauldron.txt"
        cauldron_path.write_text(result, encoding="utf-8")
        
        print("\n" + "="*60)
        print("🔥 YOUR IDEATION CAULDRON CONCEPTS 🔥")
        print("="*60)
        print(result)
        print("="*60)
        
        # Parse concepts
        concepts = {}
        pattern = r'(?:^|\n)(\d+)\.\s*(.*?)(?=\n\d+\.\s*|$)'
        matches = re.findall(pattern, result, re.DOTALL)
        
        for num, content in matches:
            concepts[int(num)] = f"{num}. {content.strip()}"
            
        print("\nMenu Options:")
        if concepts:
            for num, content in sorted(concepts.items()):
                lines = content.split('\n')
                title = lines[0]
                hook = next((l for l in lines if l.strip().startswith("HOOK:")), "")
                print(f"  [{num}] Select: {title} — {hook.replace('HOOK:', '').strip()}")
            for num in sorted(concepts.keys()):
                print(f"  [R{num}] Refine/Riff: Make fine adjustments and variations to Idea {num}")
        print("  [C] Customize: Input a completely custom seed concept.")
        
        try:
            choice = input("\nYour choice > ").strip()
            
            if choice.lower() in ['c', 'custom']:
                print("\nType your complete custom seed (press Enter to finish):")
                custom_idea = input("> ").strip()
                if custom_idea:
                    seed_file.write_text(custom_idea, encoding="utf-8")
                    step(f"Custom seed successfully written to {seed_file.name}!")
                    break
            elif choice.isdigit() and int(choice) in concepts:
                selected = concepts[int(choice)]
                seed_file.write_text(selected, encoding="utf-8")
                step(f"Selected seed successfully written to {seed_file.name}!")
                break
            elif len(choice) >= 2 and choice[0].upper() == 'R' and choice[1].isdigit() and int(choice[1]) in concepts:
                target_num = int(choice[1])
                target_concept = concepts[target_num]
                
                print(f"\nYou chose to refine Idea {target_num}:")
                print(f"  {target_concept.split('\n')[0]}")
                refine_feedback = input("What would you like to refine or change in this idea? > ").strip()
                
                if refine_feedback:
                    current_prompt = f"""We are refining a novel seed concept.
Here is the selected base concept:
{target_concept}

Here is the user's specific feedback/refinement request:
"{refine_feedback}"

Generate 3 new variations of this concept incorporating the feedback. Keep the elite writing principles:
1. Hook of Paradox: compelling one-sentence paradox.
2. Curiosity Loops: deep conspiracy/mystery layer.
3. Wound/Want/Need/Lie: backstory trauma in tension with goal.
4. Speculative Cost: powers have high tragic costs.

Provide EXACTLY the same format:

NUMBER. TITLE
HOOK: [One sentence paradox]
WORLD: [Gritty sensory details]
MAGIC/COST: [Speculative element and tragic cost]
TENSION: [Personal vs cosmic conflict]
THE CONSPIRACY: [The underlying mystery/curiosity loop]
THEME: [Deep thematic question]
"""
                    continue
            else:
                print("Invalid option. Choose a number from 1 to 3, R1-R3 to refine, or C.")
        except (KeyboardInterrupt, EOFError):
            print("\nIdeation interrupted. Using concept 1 by default.")
            if concepts:
                seed_file.write_text(concepts[1], encoding="utf-8")
            else:
                seed_file.write_text(result, encoding="utf-8")
            break
            
    # 4. Generate MYSTERY.md (Optional automation based on selected concept)
    mystery_file = BASE_DIR / "MYSTERY.md"
    seed_content = seed_file.read_text(encoding="utf-8")
    
    print("\n" + "="*60)
    print("🔮 CENTRAL MYSTERY GENERATION (MYSTERY.md) 🔮")
    print("="*60)
    try:
        choice = input("Do you want to generate a deep Central Mystery (MYSTERY.md) based on this concept? [Y/n] ").strip().lower()
        if choice == "" or choice in ["y", "yes", "s", "sim"]:
            step("Generating structured and ambiguous MYSTERY.md with AI...")
            
            mystery_prompt = f"""Based on this sci-fi/fantasy novel seed concept, build a deep, high-stakes, and morally ambiguous "Author's Eyes Only" central mystery.
This is the MYSTERY.MD file -- the definitive reference for the underlying conspiracy and the recontextualizing reveal that will happen at the climax.

SEED CONCEPT:
{seed_content}

Structure the document with exactly these sections:

# THE CENTRAL MYSTERY
### Author's Eyes Only — Not for AI agent context during drafting

---

## The Question
State the central question/enigma of the novel in one single, compelling sentence.

## The Answer
What is the core secret? The hidden truth that the protagonist discovers at the climax that recontextualizes the entire story.

## Moral Ambiguity
Explain why there is no "clean" or "right" moral answer. What are the competing, valid ethical claims of both sides? How does it avoid being a generic "good vs evil" plot?

## Physical Manifestation
What physical objects, files, or structures in the world hold or embody this mystery? (e.g. locked journals, tuning forks, acoustic anomalies, forbidden records). How do characters interact with them before the reveal?

## The Protagonist's Choice
What is the final decision the protagonist must make regarding this mystery at the climax? What is the severe and permanent cost/loss associated with either choice he makes?
"""
            
            mystery_result = call_llm(
                prompt=mystery_prompt,
                system_prompt="You are a brilliant mystery novelist and literary structural architect. You design high-stakes, deeply personal, and cosmic conspiracies with moral depth.",
                temperature=0.7,
                is_judge=False
            )
            
            mystery_file.write_text(mystery_result, encoding="utf-8")
            step("MYSTERY.md successfully generated and saved!")
        else:
            step("Ignoring mystery generation. The default blank template is preserved.")
    except (KeyboardInterrupt, EOFError):
        print("\nIgnoring mystery generation. The default blank template is preserved.")
            
    # Save state and commit
    state["phase"] = "foundation"
    state["current_focus"] = "planning"
    save_state(state)
    
    git_add_commit("ideation: finalized seed.txt and generated MYSTERY.md")
    
    banner("IDEATION COMPLETE — seed.txt ready for Phase 1")
    return state


# ---------------------------------------------------------------------------
# PHASE 1 — FOUNDATION
# ---------------------------------------------------------------------------

def run_foundation(state: dict) -> dict:
    """
    Build planning documents (world, characters, outline, voice, canon).
    Loop until foundation_score > threshold or max iterations reached.
    """
    banner("PHASE 1: FOUNDATION", "=")

    best_score = state.get("foundation_score", 0.0)
    iteration = state.get("iteration", 0)

    for i in range(iteration + 1, MAX_FOUNDATION_ITERS + 1):
        banner(f"Foundation Iteration {i}", "-")
        state["iteration"] = i

        # 1. Generate planning documents
        step("Generating world bible...")
        uv_run("gen_world.py", timeout=PIPELINE_TIMEOUT)

        step("Generating characters...")
        uv_run("gen_characters.py", timeout=PIPELINE_TIMEOUT)

        step("Generating outline (part 1)...")
        uv_run("gen_outline.py", timeout=PIPELINE_TIMEOUT)

        step("Generating outline (part 2 — foreshadowing)...")
        uv_run("gen_outline_part2.py", timeout=PIPELINE_TIMEOUT)

        step("Generating canon...")
        uv_run("gen_canon.py", timeout=PIPELINE_TIMEOUT)

        step("Running voice fingerprint...")
        uv_run("voice_fingerprint.py", timeout=PIPELINE_TIMEOUT)

        # 2. Evaluate
        step("Evaluating foundation...")
        eval_result = uv_run("evaluate.py --phase=foundation", timeout=PIPELINE_TIMEOUT)
        score = parse_score(eval_result.stdout, "overall_score")
        lore = parse_lore_score(eval_result.stdout)

        step(f"Foundation score: {score}  (lore: {lore}, prev best: {best_score})")

        # 3. Keep or discard
        if score > best_score:
            commit_hash = git_add_commit(
                f"foundation iter {i}: score {score} (lore {lore})")
            log_result(commit_hash, "foundation", score, 0, "keep",
                       f"Iteration {i}: score improved {best_score} -> {score}")
            best_score = score
            state["foundation_score"] = score
            state["lore_score"] = lore
            save_state(state)
        else:
            step(f"Score did not improve ({score} <= {best_score}), discarding")
            git_reset_hard("HEAD")
            log_result("discarded", "foundation", score, 0, "discard",
                       f"Iteration {i}: no improvement ({score} <= {best_score})")

        # 4. Check exit condition
        if best_score >= FOUNDATION_THRESHOLD:
            step(f"Foundation score {best_score} >= {FOUNDATION_THRESHOLD} — PASSED")
            break
    else:
        step(f"WARNING: max iterations ({MAX_FOUNDATION_ITERS}) reached "
             f"with score {best_score}")

    # Determine total chapters from outline
    total = get_total_chapters(state)
    state["chapters_total"] = total
    state["phase"] = "drafting"
    state["current_focus"] = "chapter_drafting"
    save_state(state)

    banner(f"FOUNDATION COMPLETE — score {best_score}, {total} chapters planned")
    return state


# ---------------------------------------------------------------------------
# PHASE 2 — DRAFTING
# ---------------------------------------------------------------------------

def run_drafting(state: dict) -> dict:
    """
    Draft each chapter sequentially, evaluating and retrying as needed.
    """
    banner("PHASE 2: DRAFTING", "=")

    total = get_total_chapters(state)
    start_chapter = state.get("chapters_drafted", 0) + 1

    CHAPTERS_DIR.mkdir(exist_ok=True)

    for ch in range(start_chapter, total + 1):
        banner(f"Drafting Chapter {ch}/{total}", "-")
        drafted = False

        for attempt in range(1, MAX_CHAPTER_ATTEMPTS + 1):
            step(f"Attempt {attempt}/{MAX_CHAPTER_ATTEMPTS}")

            # Draft
            draft_result = uv_run(f"draft_chapter.py {ch}", timeout=DRAFT_TIMEOUT)
            if draft_result.returncode != 0:
                step(f"Draft failed (exit {draft_result.returncode}), retrying...")
                continue

            # Check the chapter file exists and has content
            ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
            if not ch_file.exists() or ch_file.stat().st_size < 100:
                step("Chapter file missing or too short, retrying...")
                continue

            word_count = len(ch_file.read_text().split())
            step(f"Drafted {word_count} words")

            # Evaluate
            eval_result = uv_run(f"evaluate.py --chapter={ch}", timeout=EVAL_TIMEOUT)
            score = parse_score(eval_result.stdout, "overall_score")
            step(f"Chapter {ch} score: {score}")

            if score >= CHAPTER_THRESHOLD:
                commit_hash = git_add_commit(
                    f"ch{ch:02d}: score {score}, {word_count}w")
                log_result(commit_hash, f"ch{ch:02d}", score, word_count,
                           "keep", f"Chapter {ch} (attempt {attempt})")
                state["chapters_drafted"] = ch
                save_state(state)
                drafted = True
                break
            else:
                step(f"Score {score} < {CHAPTER_THRESHOLD}, discarding attempt")
                log_result("discarded", f"ch{ch:02d}", score, word_count,
                           "discard", f"Chapter {ch} attempt {attempt}")
                # Remove the bad chapter file so next attempt starts fresh
                if ch_file.exists():
                    run_tool(f"git checkout -- chapters/ch_{ch:02d}.md 2>/dev/null || true")

        if not drafted:
            step(f"WARNING: Chapter {ch} failed all {MAX_CHAPTER_ATTEMPTS} attempts, "
                 f"keeping last attempt and moving on")
            # Keep whatever we have and commit it
            ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
            if ch_file.exists():
                word_count = len(ch_file.read_text().split())
                commit_hash = git_add_commit(
                    f"ch{ch:02d}: best-effort after {MAX_CHAPTER_ATTEMPTS} attempts")
                log_result(commit_hash, f"ch{ch:02d}", "?", word_count,
                           "forced", f"Chapter {ch}: kept after max attempts")
                state["chapters_drafted"] = ch
                save_state(state)

    # All chapters drafted
    state["phase"] = "revision"
    state["current_focus"] = "full_novel"
    state["chapters_drafted"] = total
    state["revision_cycle"] = 0
    save_state(state)

    total_words = count_words_in_chapters()
    banner(f"DRAFTING COMPLETE — {total} chapters, {total_words} words")
    return state


# ---------------------------------------------------------------------------
# PHASE 3 — REVISION
# ---------------------------------------------------------------------------

def parse_panel_consensus(panel_path: Path) -> list[dict]:
    """
    Parse reader_panel.json to find chapters with consensus issues.
    Returns list of dicts: {chapter, question, flagged_by, details}
    sorted by number of readers who flagged (descending).
    """
    if not panel_path.exists():
        return []
    with open(panel_path) as f:
        data = json.load(f)

    items = []

    # Look at disagreements — these are flagged by some but not all readers
    for d in data.get("disagreements", []):
        items.append({
            "chapter": d.get("chapter", 0),
            "question": d.get("question", ""),
            "flagged_by": d.get("flagged_by", []),
            "count": len(d.get("flagged_by", [])),
        })

    # Also scan readers for direct chapter mentions in key questions
    readers = data.get("readers", {})
    chapter_mentions = {}  # ch_num -> count of readers mentioning it

    for reader_key, answers in readers.items():
        for question in ["momentum_loss", "cut_candidate", "worst_scene",
                         "thinnest_character", "missing_scene"]:
            answer = answers.get(question, "")
            if not isinstance(answer, str):
                continue
            chs = re.findall(r'Ch(?:apter)?\s*(\d+)', answer, re.IGNORECASE)
            for ch_str in chs:
                ch_num = int(ch_str)
                key = (ch_num, question)
                if key not in chapter_mentions:
                    chapter_mentions[key] = {"chapter": ch_num, "question": question,
                                             "flagged_by": [], "count": 0}
                chapter_mentions[key]["flagged_by"].append(reader_key)
                chapter_mentions[key]["count"] += 1

    # Merge and deduplicate
    seen = set()
    for item in items:
        seen.add((item["chapter"], item["question"]))
    for key, item in chapter_mentions.items():
        if key not in seen:
            items.append(item)

    # Sort by count descending, take unique chapters
    items.sort(key=lambda x: -x["count"])

    # Deduplicate by chapter (keep highest-count issue per chapter)
    seen_chapters = set()
    unique = []
    for item in items:
        if item["chapter"] not in seen_chapters and item["chapter"] > 0:
            seen_chapters.add(item["chapter"])
            unique.append(item)

    return unique[:5]  # top 3-5 consensus items


def run_revision(state: dict, max_cycles: int = MAX_REVISION_CYCLES) -> dict:
    """
    Revision phase: adversarial editing, reader panel, targeted revisions.
    """
    banner("PHASE 3: REVISION", "=")

    BRIEFS_DIR.mkdir(exist_ok=True)
    EDIT_LOGS_DIR.mkdir(exist_ok=True)

    prev_score = state.get("novel_score", 0.0)
    start_cycle = state.get("revision_cycle", 0) + 1
    max_cycles = min(max_cycles, MAX_REVISION_CYCLES)

    for cycle in range(start_cycle, max_cycles + 1):
        banner(f"Revision Cycle {cycle}/{max_cycles}", "-")

        # -- Step 1: Adversarial editing pass --
        step("Running adversarial editing on all chapters...")
        uv_run("adversarial_edit.py all", timeout=ADVERSARIAL_TIMEOUT)

        # -- Step 2: Apply mechanical cuts (only if apply_cuts.py exists) --
        apply_cuts = BASE_DIR / "apply_cuts.py"
        if apply_cuts.exists():
            step("Applying mechanical cuts (OVER-EXPLAIN, REDUNDANT)...")
            run_tool("uv run python apply_cuts.py all "
                     "--types OVER-EXPLAIN REDUNDANT --min-fat 15", timeout=EXPORT_TIMEOUT)
        else:
            step("apply_cuts.py not found, skipping mechanical cuts")

        # -- Step 3: Reader panel --
        step("Running reader panel evaluation...")
        uv_run("reader_panel.py", timeout=READER_PANEL_TIMEOUT)

        # -- Step 4: Parse panel consensus --
        panel_path = EDIT_LOGS_DIR / "reader_panel.json"
        consensus_items = parse_panel_consensus(panel_path)

        if consensus_items:
            step(f"Found {len(consensus_items)} consensus items:")
            for item in consensus_items:
                print(f"    Ch {item['chapter']}: {item['question']} "
                      f"(flagged by {item['count']} readers)")
        else:
            step("No strong consensus items found from panel")

        # -- Step 5: Targeted revisions for consensus items --
        for idx, item in enumerate(consensus_items):
            ch_num = item["chapter"]
            question = item["question"]
            banner(f"  Revising Ch {ch_num} ({question}) [{idx+1}/{len(consensus_items)}]", ".")

            # Snapshot the current chapter score for comparison
            pre_eval = uv_run(f"evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
            pre_score = parse_score(pre_eval.stdout, "overall_score")

            # Generate revision brief
            brief_file = BRIEFS_DIR / f"ch{ch_num:02d}_cycle{cycle}_{question}.md"
            gen_brief = BASE_DIR / "gen_brief.py"
            if gen_brief.exists():
                step(f"Generating brief for Ch {ch_num}...")
                run_tool(f"uv run python gen_brief.py --panel {ch_num}", timeout=EVAL_TIMEOUT)
                # gen_brief.py may write to briefs/ — find the most recent brief
                brief_candidates = sorted(
                    BRIEFS_DIR.glob(f"ch{ch_num:02d}*.md"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
                if brief_candidates:
                    brief_file = brief_candidates[0]
            else:
                # Create a minimal brief from the panel data
                step(f"gen_brief.py not found, creating minimal brief for Ch {ch_num}...")
                brief_content = (
                    f"# Revision Brief: Chapter {ch_num}\n\n"
                    f"## Issue: {question}\n\n"
                    f"Panel consensus identified this chapter for revision.\n"
                    f"Focus: address the {question.replace('_', ' ')} issue.\n"
                    f"Preserve existing voice, character work, and essential beats.\n"
                )
                brief_file.write_text(brief_content)

            if not brief_file.exists():
                step(f"No brief file found for Ch {ch_num}, skipping")
                continue

            # Run revision
            step(f"Revising Ch {ch_num} with brief {brief_file.name}...")
            uv_run(f"gen_revision.py {ch_num} {brief_file}", timeout=REVISION_TIMEOUT)

            # Evaluate revised chapter
            post_eval = uv_run(f"evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
            post_score = parse_score(post_eval.stdout, "overall_score")

            ch_file = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
            word_count = len(ch_file.read_text().split()) if ch_file.exists() else 0

            step(f"Ch {ch_num}: {pre_score} -> {post_score}")

            if post_score >= pre_score:
                commit_hash = git_add_commit(
                    f"revision cycle {cycle}: ch{ch_num:02d} "
                    f"{question} {pre_score}->{post_score}")
                log_result(commit_hash, f"rev-ch{ch_num:02d}", post_score,
                           word_count, "keep",
                           f"Cycle {cycle}: {question} improved {pre_score}->{post_score}")
            else:
                step(f"Revision made it worse ({post_score} < {pre_score}), reverting")
                git_reset_hard("HEAD")
                log_result("reverted", f"rev-ch{ch_num:02d}", post_score,
                           word_count, "discard",
                           f"Cycle {cycle}: {question} regressed {pre_score}->{post_score}")

            # Clean up brief file
            if brief_file.exists():
                brief_file.unlink()

        # -- Step 6: Full novel evaluation --
        step("Running full novel evaluation...")
        full_eval = uv_run("evaluate.py --full", timeout=REVISION_TIMEOUT)
        novel_score = parse_score(full_eval.stdout, "novel_score")

        if novel_score < 0:
            # Fallback: try overall_score
            novel_score = parse_score(full_eval.stdout, "overall_score")

        total_words = count_words_in_chapters()
        step(f"Novel score: {novel_score}  (prev: {prev_score}, words: {total_words})")

        # Commit cycle results
        commit_hash = git_add_commit(
            f"revision cycle {cycle} complete: novel_score {novel_score}")
        log_result(commit_hash, f"revision-cycle-{cycle}", novel_score,
                   total_words, "cycle",
                   f"Cycle {cycle}: novel_score {prev_score}->{novel_score}")

        state["novel_score"] = novel_score
        state["revision_cycle"] = cycle
        save_state(state)

        # -- Step 7: Plateau detection --
        if cycle >= MIN_REVISION_CYCLES and abs(novel_score - prev_score) < PLATEAU_DELTA:
            step(f"Plateau detected (delta {abs(novel_score - prev_score):.2f} "
                 f"< {PLATEAU_DELTA}) after {cycle} cycles — stopping")
            break

        prev_score = novel_score

    # =========================================================
    # PHASE 3b: OPUS REVIEW LOOP (deep, prose-level refinement)
    # =========================================================
    review_py = BASE_DIR / "review.py"
    if review_py.exists():
        banner("PHASE 3b: OPUS REVIEW LOOP", "=")
        
        max_review_rounds = 4
        for rnd in range(1, max_review_rounds + 1):
            banner(f"Opus Review Round {rnd}/{max_review_rounds}", "-")
            
            # Step 1: Generate the review
            step("Sending manuscript to Opus for review...")
            review_result = uv_run(
                f"review.py --output reviews.md", timeout=REVIEW_TIMEOUT)
            
            # Step 2: Parse the review
            step("Parsing review...")
            parse_result = run_tool(
                "uv run python review.py --parse", timeout=EVAL_TIMEOUT)
            print(parse_result.stdout if parse_result else "")
            
            # Step 3: Check stopping condition
            review_logs = sorted(
                (EDIT_LOGS_DIR).glob("*_review.json"), reverse=True)
            if review_logs:

                review_data = json.loads(review_logs[0].read_text())
                stars = review_data.get("stars", 0) or 0
                total_items = review_data.get("total_items", 0)
                major_items = review_data.get("major_items", 0)
                qualified = review_data.get("qualified_items", 0)
                
                step(f"Stars: {stars}, Items: {total_items} "
                     f"({major_items} major, {qualified} qualified)")
                
                # Stop if: ≥4★, no major unqualified items, or >half qualified
                if stars >= 4.5 and major_items == 0:
                    step("★★★★½ with no major items — novel is ready.")
                    break
                if stars >= 4 and total_items > 0 and qualified / total_items > 0.5:
                    step(f"★{'★' * int(stars)} with majority qualified items — novel is ready.")
                    break
            
            # Step 4: Generate briefs from review items and fix
            step("Generating revision briefs from review...")
            gen_brief_py = BASE_DIR / "gen_brief.py"
            if gen_brief_py.exists():
                # Auto mode: picks weakest chapter, cross-references all sources
                run_tool("uv run python gen_brief.py --auto", timeout=EVAL_TIMEOUT)
                
                # Find any generated briefs and apply the top one
                recent_briefs = sorted(
                    BRIEFS_DIR.glob("*_auto.md"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
                if recent_briefs:
                    brief = recent_briefs[0]
                    # Extract chapter number from filename
                    ch_match = re.search(r'ch(\d+)', brief.name)
                    if ch_match:
                        ch_num = int(ch_match.group(1))
                        step(f"Revising Ch {ch_num} from review brief...")
                        uv_run(f"gen_revision.py {ch_num} {brief}", timeout=REVISION_TIMEOUT)
                        git_add_commit(
                            f"review round {rnd}: revise ch{ch_num:02d} from Opus feedback")
                        if brief.exists():
                            brief.unlink()
            
            # Step 5: Mechanical fixes from review
            # Run slop pass on any mentioned patterns
            step("Running mechanical cleanup pass...")
            apply_cuts_py = BASE_DIR / "apply_cuts.py"
            if apply_cuts_py.exists():
                run_tool(
                    "uv run python apply_cuts.py all --types OVER-EXPLAIN REDUNDANT --min-fat 15",
                    timeout=EXPORT_TIMEOUT)
                git_add_commit(f"review round {rnd}: mechanical cleanup")
            
            step(f"Review round {rnd} complete.")
        
        banner("OPUS REVIEW LOOP COMPLETE")
    
    state["phase"] = "export"
    state["current_focus"] = "export"
    save_state(state)

    banner(f"REVISION COMPLETE — {state.get('revision_cycle', 0)} cycles, "
           f"novel_score {state.get('novel_score', 0)}")
    return state


# ---------------------------------------------------------------------------
# PHASE 4 — EXPORT
# ---------------------------------------------------------------------------

def run_export(state: dict) -> dict:
    """
    Build final deliverables: outline, arc summary, manuscript, PDF.
    """
    banner("PHASE 4: EXPORT", "=")

    # 1. Rebuild outline from chapters
    build_outline = BASE_DIR / "build_outline.py"
    if build_outline.exists():
        step("Rebuilding outline from chapters...")
        uv_run("build_outline.py", timeout=EXPORT_TIMEOUT)

    # 2. Build arc summary
    build_arc = BASE_DIR / "build_arc_summary.py"
    if build_arc.exists():
        step("Building arc summary...")
        uv_run("build_arc_summary.py", timeout=EXPORT_TIMEOUT)

    # 3. Concatenate chapters into manuscript.md
    step("Building manuscript.md...")
    manuscript = BASE_DIR / "manuscript.md"
    chapter_files = sorted(CHAPTERS_DIR.glob("ch_*.md"))

    parts = []
    for ch_file in chapter_files:
        text = ch_file.read_text().strip()
        if text:
            parts.append(text)

    if parts:
        manuscript.write_text("\n\n---\n\n".join(parts) + "\n")
        word_count = sum(len(p.split()) for p in parts)
        step(f"Manuscript: {len(parts)} chapters, {word_count} words")
    else:
        step("WARNING: no chapter files found for manuscript")

    # 4. Build LaTeX
    build_tex = BASE_DIR / "typeset" / "build_tex.py"
    if build_tex.exists():
        step("Building LaTeX content...")
        run_tool(f"uv run python typeset/build_tex.py", timeout=EXPORT_TIMEOUT)

        # 5. Typeset with tectonic (if available)
        novel_tex = BASE_DIR / "typeset" / "novel.tex"
        if novel_tex.exists():
            tectonic_check = run_tool("which tectonic", timeout=max(EXPORT_TIMEOUT // 60, 10))
            if tectonic_check.returncode == 0:
                step("Typesetting PDF with tectonic...")
                result = run_tool("tectonic typeset/novel.tex", timeout=EXPORT_TIMEOUT)
                if result.returncode == 0:
                    step("PDF generated: typeset/novel.pdf")
                else:
                    step("WARNING: tectonic typesetting failed")
            else:
                step("tectonic not found, skipping PDF generation")
    else:
        step("typeset/build_tex.py not found, skipping LaTeX")

    # 6. Final commit
    commit_hash = git_add_commit("export: manuscript, outline, arc summary, PDF")
    total_words = count_words_in_chapters()
    log_result(commit_hash, "export", state.get("novel_score", "?"),
               total_words, "export", "Final export")

    state["phase"] = "complete"
    state["current_focus"] = "done"
    save_state(state)

    banner(f"EXPORT COMPLETE — {len(chapter_files)} chapters, {total_words} words")
    return state


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def get_current_branch() -> str:
    """Return the current active git branch name, or empty string on failure."""
    try:
        res = subprocess.run(
            "git rev-parse --abbrev-ref HEAD", shell=True,
            capture_output=True, text=True, cwd=str(BASE_DIR)
        )
        return res.stdout.strip() if res.returncode == 0 else ""
    except Exception:
        return ""


# Task List mapping
TASK_LIST = [
    "0_ideation",
    "1_world",
    "2_characters",
    "3_outline",
    "4_outline_p2",
    "5_canon",
    "6_voice",
    "7_foundation_eval",
    "8_draft_chapters",
    "9_adversarial_edit",
    "10_reader_panel",
    "11_opus_review",
    "12_export"
]

def task_ideation(state: dict) -> dict:
    banner("TASK 0: INTERACTIVE IDEATION CAULDRON")
    state = run_ideation(state)
    state["phase"] = "foundation"
    return state

def task_world(state: dict) -> dict:
    banner("TASK 1: GENERATE WORLD BIBLE")
    step("Generating world bible...")
    uv_run("gen_world.py", timeout=PIPELINE_TIMEOUT)
    return state

def task_characters(state: dict) -> dict:
    banner("TASK 2: GENERATE CHARACTER REGISTRY")
    step("Generating character registry...")
    uv_run("gen_characters.py", timeout=PIPELINE_TIMEOUT)
    return state

def task_outline(state: dict) -> dict:
    banner("TASK 3: GENERATE PARTIAL OUTLINE (PART 1)")
    step("Generating outline part 1...")
    uv_run("gen_outline.py", timeout=PIPELINE_TIMEOUT)
    return state

def task_outline_p2(state: dict) -> dict:
    banner("TASK 4: GENERATE COMPLETE OUTLINE (PART 2)")
    step("Generating outline part 2...")
    uv_run("gen_outline_part2.py", timeout=PIPELINE_TIMEOUT)
    return state

def task_canon(state: dict) -> dict:
    banner("TASK 5: GENERATE CANON")
    step("Generating canon...")
    uv_run("gen_canon.py", timeout=PIPELINE_TIMEOUT)
    return state

def task_voice(state: dict) -> dict:
    banner("TASK 6: GENERATE VOICE FINGERPRINT")
    step("Evaluating voice fingerprint...")
    uv_run("voice_fingerprint.py", timeout=PIPELINE_TIMEOUT)
    return state

def task_foundation_eval(state: dict) -> dict:
    banner("TASK 7: EVALUATE FOUNDATION DOCS")
    step("Evaluating foundation documents...")
    eval_result = uv_run("evaluate.py --phase=foundation", timeout=PIPELINE_TIMEOUT)
    score = parse_score(eval_result.stdout, "overall_score")
    lore_score = parse_lore_score(eval_result.stdout)
    
    state["foundation_score"] = score
    state["lore_score"] = lore_score
    
    log_msg(f"Foundation Score: {score} (Lore: {lore_score})")
    
    if score >= FOUNDATION_THRESHOLD and lore_score > 0.0:
        log_msg("Foundation approved! Proceeding to drafting.")
        state["phase"] = "drafting"
    else:
        log_msg(f"Foundation score {score} (Lore {lore_score}) below threshold. Please refine bibles.")
    return state

def task_draft_chapters(state: dict) -> dict:
    banner("TASK 8: DRAFT ALL CHAPTERS")
    state = run_drafting(state)
    state["phase"] = "revision"
    return state

def task_adversarial_edit(state: dict) -> dict:
    banner("TASK 9: ADVERSARIAL EDITING & CUTS")
    step("Running adversarial editing on all chapters...")
    uv_run("adversarial_edit.py all", timeout=ADVERSARIAL_TIMEOUT)

    apply_cuts = BASE_DIR / "apply_cuts.py"
    if apply_cuts.exists():
        step("Applying mechanical cuts (OVER-EXPLAIN, REDUNDANT)...")
        run_tool("uv run python apply_cuts.py all "
                 "--types OVER-EXPLAIN REDUNDANT --min-fat 15", timeout=EXPORT_TIMEOUT)
    else:
        step("apply_cuts.py not found, skipping mechanical cuts")
    return state

def task_reader_panel(state: dict) -> dict:
    banner("TASK 10: READER PANEL EVALUATION & REVISIONS")
    step("Running reader panel evaluation...")
    uv_run("reader_panel.py", timeout=READER_PANEL_TIMEOUT)

    panel_path = EDIT_LOGS_DIR / "reader_panel.json"
    consensus_items = parse_panel_consensus(panel_path)

    if consensus_items:
        step(f"Found {len(consensus_items)} consensus items:")
        for item in consensus_items:
            log_msg(f"    Ch {item['chapter']}: {item['question']} (flagged by {item['count']} readers)")
    else:
        step("No strong consensus items found from panel")

    for idx, item in enumerate(consensus_items):
        ch_num = item["chapter"]
        question = item["question"]
        banner(f"  Revising Ch {ch_num} ({question}) [{idx+1}/{len(consensus_items)}]", ".")

        pre_eval = uv_run(f"evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
        pre_score = parse_score(pre_eval.stdout, "overall_score")

        brief_file = BRIEFS_DIR / f"ch{ch_num:02d}_cycle1_{question}.md"
        gen_brief = BASE_DIR / "gen_brief.py"
        if gen_brief.exists():
            step(f"Generating brief for Ch {ch_num}...")
            run_tool(f"uv run python gen_brief.py --panel {ch_num}", timeout=EVAL_TIMEOUT)
            brief_candidates = sorted(
                BRIEFS_DIR.glob(f"ch{ch_num:02d}*.md"),
                key=lambda p: p.stat().st_mtime, reverse=True)
            if brief_candidates:
                brief_file = brief_candidates[0]
        else:
            step(f"gen_brief.py not found, creating minimal brief for Ch {ch_num}...")
            brief_content = (
                f"# Revision Brief: Chapter {ch_num}\n\n"
                f"## Issue: {question}\n\n"
                f"Panel consensus identified this chapter for revision.\n"
                f"Focus: address the {question.replace('_', ' ')} issue.\n"
                f"Preserve existing voice, character work, and essential beats.\n"
            )
            brief_file.write_text(brief_content)

        if not brief_file.exists():
            step(f"No brief file found for Ch {ch_num}, skipping")
            continue

        step(f"Revising Ch {ch_num} with brief {brief_file.name}...")
        uv_run(f"gen_revision.py {ch_num} {brief_file}", timeout=REVISION_TIMEOUT)

        post_eval = uv_run(f"evaluate.py --chapter={ch_num}", timeout=EVAL_TIMEOUT)
        post_score = parse_score(post_eval.stdout, "overall_score")

        ch_file = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
        word_count = len(ch_file.read_text().split()) if ch_file.exists() else 0

        log_msg(f"Ch {ch_num}: {pre_score} -> {post_score}")

        if post_score >= pre_score:
            commit_hash = git_add_commit(
                f"revision reader_panel: ch{ch_num:02d} "
                f"{question} {pre_score}->{post_score}")
            log_result(commit_hash, f"rev-ch{ch_num:02d}", post_score,
                       word_count, "keep",
                       f"Reader Panel: {question} improved {pre_score}->{post_score}")
        else:
            step(f"Revision made it worse ({post_score} < {pre_score}), reverting")
            git_reset_hard("HEAD")
            log_result("reverted", f"rev-ch{ch_num:02d}", post_score,
                       word_count, "discard",
                       f"Reader Panel: {question} regressed {pre_score}->{post_score}")

        if brief_file.exists():
            brief_file.unlink()
    return state

def task_opus_review(state: dict) -> dict:
    banner("TASK 11: OPUS HOLISTIC REVIEW LOOP")
    step("Running full novel evaluation...")
    full_eval = uv_run("evaluate.py --full", timeout=REVISION_TIMEOUT)
    novel_score = parse_score(full_eval.stdout, "novel_score")
    
    if novel_score >= 8.0:
        step(f"Novel Score is {novel_score} >= 8.0. Skipping Opus review loop.")
        state["phase"] = "export"
        return state

    max_review_rounds = 3
    for rnd in range(1, max_review_rounds + 1):
        banner(f"Opus Review Round {rnd}/{max_review_rounds}", "-")
        
        step("Sending manuscript to Opus for review...")
        review_result = uv_run(f"review.py --output reviews.md", timeout=REVIEW_TIMEOUT)
        
        step("Parsing review...")
        parse_result = run_tool("uv run python review.py --parse", timeout=EVAL_TIMEOUT)
        
        review_logs = sorted((EDIT_LOGS_DIR).glob("*_review.json"), reverse=True)
        if review_logs:
            review_data = json.loads(review_logs[0].read_text())
            stars = review_data.get("stars", 0) or 0
            total_items = review_data.get("total_items", 0)
            major_items = review_data.get("major_items", 0)
            qualified = review_data.get("qualified_items", 0)
            
            step(f"Stars: {stars}, Items: {total_items} ({major_items} major, {qualified} qualified)")
            
            if stars >= 4.5 and major_items == 0:
                step("★★★★½ with no major items — novel is ready.")
                break
            if stars >= 4 and total_items > 0 and qualified / total_items > 0.5:
                step(f"★★★★ with majority qualified items — novel is ready.")
                break
        
        step("Generating revision briefs from review...")
        gen_brief_py = BASE_DIR / "gen_brief.py"
        if gen_brief_py.exists():
            run_tool("uv run python gen_brief.py --auto", timeout=EVAL_TIMEOUT)
            
            recent_briefs = sorted(
                BRIEFS_DIR.glob("*_auto.md"),
                key=lambda p: p.stat().st_mtime, reverse=True)
            if recent_briefs:
                brief = recent_briefs[0]
                ch_match = re.search(r'ch(\d+)', brief.name)
                if ch_match:
                    ch_num = int(ch_match.group(1))
                    step(f"Revising Ch {ch_num} from review brief...")
                    uv_run(f"gen_revision.py {ch_num} {brief}", timeout=REVISION_TIMEOUT)
                    git_add_commit(f"review round {rnd}: revise ch{ch_num:02d} from Opus feedback")
                    if brief.exists():
                        brief.unlink()
        
        step("Running mechanical cleanup pass...")
        apply_cuts_py = BASE_DIR / "apply_cuts.py"
        if apply_cuts_py.exists():
            run_tool("uv run python apply_cuts.py all --types OVER-EXPLAIN REDUNDANT --min-fat 15", timeout=EXPORT_TIMEOUT)
            git_add_commit(f"review round {rnd}: mechanical cleanup")
        
        step(f"Review round {rnd} complete.")
        
    state["phase"] = "export"
    return state

def task_export(state: dict) -> dict:
    banner("TASK 12: EXPORT manuscript & COMPILATION")
    state = run_export(state)
    state["phase"] = "complete"
    return state


def run_pipeline(args):
    """Run the full pipeline or a specific phase."""
    # Safety Check: Prevent running on main/master to avoid repo pollution
    branch = get_current_branch()
    if branch in ["main", "master"]:
        print(f"\n[WARNING] You are currently on the '{branch}' branch.")
        print("Running the pipeline directly on main/master will pollute your repository history with automated commits.")
        try:
            choice = input("Would you like to automatically create and switch to a new branch for this generation? [Y/n] ").strip().lower()
            if choice == "" or choice in ["y", "yes", "s", "sim"]:
                book_name = input("Enter a name for your book (e.g., my-book): ").strip()
                if not book_name:
                    book_name = "book"
                sanitized_name = re.sub(r'[^a-zA-Z0-9_-]', '-', book_name).lower()
                branch_name = f"autobook/{sanitized_name}"
                
                print(f"[GIT] Creating and switching to new branch '{branch_name}'...")
                create_res = subprocess.run(f"git checkout -b {branch_name}", shell=True, capture_output=True, text=True, cwd=str(BASE_DIR))
                if create_res.returncode != 0:
                    print(f"ERROR: Failed to create branch '{branch_name}': {create_res.stderr.strip()}")
                    sys.exit(1)
                print(f"[GIT] Switched to branch '{branch_name}' successfully!")
            else:
                print("ERROR: Execution aborted. Please switch to a secondary branch manually before running the pipeline.")
                sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\nExecution aborted.")
            sys.exit(1)

    # Load or initialize state
    if args.from_scratch:
        banner("STARTING FROM SCRATCH")
        state = default_state()
        save_state(state)
    else:
        state = load_state()

    # Ensure directories exist
    CHAPTERS_DIR.mkdir(exist_ok=True)
    BRIEFS_DIR.mkdir(exist_ok=True)
    EDIT_LOGS_DIR.mkdir(exist_ok=True)
    EVAL_LOGS_DIR.mkdir(exist_ok=True)

    # Task mapping dict
    TASKS = {
        "0_ideation": task_ideation,
        "1_world": task_world,
        "2_characters": task_characters,
        "3_outline": task_outline,
        "4_outline_p2": task_outline_p2,
        "5_canon": task_canon,
        "6_voice": task_voice,
        "7_foundation_eval": task_foundation_eval,
        "8_draft_chapters": task_draft_chapters,
        "9_adversarial_edit": task_adversarial_edit,
        "10_reader_panel": task_reader_panel,
        "11_opus_review": task_opus_review,
        "12_export": task_export,
    }

    # Action 1: Handle Checklist Status check
    if args.status:
        completed = state.get("completed_tasks", [])
        banner("AUTOBOOK PIPELINE - TASK STATUS CHECKLIST")
        for t in TASK_LIST:
            status_char = "[x]" if t in completed else "[ ]"
            log_msg(f"  {status_char} {t}")
        return

    # Action 2: Handle Rewinding
    if args.rewind:
        rewind_task = args.rewind
        if rewind_task not in TASK_LIST:
            log_msg(f"ERROR: Unknown task to rewind to: '{rewind_task}'", level="ERROR")
            sys.exit(1)
        idx = TASK_LIST.index(rewind_task)
        state["completed_tasks"] = TASK_LIST[:idx]
        state["current_task"] = rewind_task
        if idx <= 0:
            state["phase"] = "ideation"
        elif idx <= 7:
            state["phase"] = "foundation"
        elif idx <= 8:
            state["phase"] = "drafting"
        elif idx <= 11:
            state["phase"] = "revision"
        else:
            state["phase"] = "export"
        save_state(state)
        log_msg(f"Pipeline progress checkpoint successfully rewound to task: '{rewind_task}'")
        # Proceed with execution from rewound point forward

    # Action 3: Handle Single Task isolated execution
    if args.task:
        target_task = args.task
        if target_task not in TASK_LIST:
            log_msg(f"ERROR: Unknown task: '{target_task}'", level="ERROR")
            sys.exit(1)
        log_msg(f"Executing single isolated task: '{target_task}'")
        state = TASKS[target_task](state)
        save_state(state)
        log_msg(f"Single isolated task '{target_task}' completed successfully.")
        return

    # Action 4: Sequential Run Loop (Resume mode)
    completed = state.get("completed_tasks", [])
    if args.phase:
        # Legacy compatibility mapping
        phase_map = {
            "ideation": ["0_ideation"],
            "foundation": ["1_world", "2_characters", "3_outline", "4_outline_p2", "5_canon", "6_voice", "7_foundation_eval"],
            "drafting": ["8_draft_chapters"],
            "revision": ["9_adversarial_edit", "10_reader_panel", "11_opus_review"],
            "export": ["12_export"]
        }
        active_tasks = phase_map.get(args.phase, [])
    else:
        active_tasks = [t for t in TASK_LIST if t not in completed]
        if not active_tasks:
            log_msg("Pipeline already complete! Use --from-scratch to restart or --rewind <task> to roll back.")
            return

    banner(f"AUTOBOOK PIPELINE — executing tasks: {', '.join(active_tasks)}")
    print(f"  State: current_task={state.get('current_task')}, completed={len(completed)}/{len(TASK_LIST)}")

    start_time = datetime.now()

    for task_name in active_tasks:
        try:
            state["current_task"] = task_name
            save_state(state)
            
            state = TASKS[task_name](state)
            
            if "completed_tasks" not in state:
                state["completed_tasks"] = []
            if task_name not in state["completed_tasks"]:
                state["completed_tasks"].append(task_name)
            save_state(state)
            
        except KeyboardInterrupt:
            banner(f"INTERRUPTED during task '{task_name}' — state saved")
            save_state(state)
            sys.exit(130)
        except Exception as e:
            log_msg(f"FATAL ERROR in task '{task_name}': {e}", level="FATAL")
            save_state(state)
            raise

    elapsed = datetime.now() - start_time
    hours = elapsed.total_seconds() / 3600

    banner("PIPELINE EXECUTION COMPLETE")
    log_msg(f"  Time elapsed:    {hours:.2f} hours")
    log_msg(f"  Completed tasks: {', '.join(state.get('completed_tasks', []))}")


def main():
    parser = argparse.ArgumentParser(
        description="Autobook pipeline orchestrator — seed to finished novel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python run_pipeline.py                     # resume from current state
  python run_pipeline.py --status            # view pipeline checklist status
  python run_pipeline.py --from-scratch      # start fresh from seed.txt
  python run_pipeline.py --task 1_world      # run only task 1_world in isolation
  python run_pipeline.py --rewind 3_outline  # roll back progress checklist to task 3_outline
""")

    parser.add_argument(
        "--from-scratch", action="store_true",
        help="Reset state and start from seed.txt")
    parser.add_argument(
        "--phase", choices=PHASE_ORDER,
        help="Run only a specific legacy phase")
    parser.add_argument(
        "--max-cycles", type=int, default=None,
        help=f"Maximum revision cycles (default: {MAX_REVISION_CYCLES})")
    parser.add_argument(
        "--status", action="store_true",
        help="Display the visual status checklist of tasks")
    parser.add_argument(
        "--task", type=str, default=None,
        help="Execute only the specified task name in isolation")
    parser.add_argument(
        "--rewind", type=str, default=None,
        help="Roll back the pipeline progress checkpoint to the specified task")

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
