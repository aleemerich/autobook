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
        state = {}
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text(encoding="utf-8"))
            except Exception:
                state = {}
        
        # Initialize default state values
        if "chapters_drafted" not in state:
            state["chapters_drafted"] = 0
            
        start_chapter = state["chapters_drafted"] + 1
        
        # Read outline
        outline_file = BOOK_DATA_DIR / "outline.md"
        if not outline_file.exists():
            raise FileNotFoundError(f"Outline file outline.md not found in {BOOK_DATA_DIR}")
        outline_text = outline_file.read_text(encoding="utf-8")
        
        # Parse total chapters
        chapters_found = re.findall(r'^###\s*Ch(?:apter)?\s*(\d+)\b', outline_text, re.MULTILINE | re.IGNORECASE)
        total_chapters = len(chapters_found) if chapters_found else 22
        
        print(f"[DraftChaptersStep] Starting from Chapter {start_chapter} to {total_chapters}")
        
        # Setup Agent Factory
        factory = AgentFactory()
        
        # Load style guidelines and slop instructions
        genre_rules = load_genre_rules()
        slop_rules = load_slop_rules_instruction()
        
        # Load global lore references
        world_text = (BOOK_DATA_DIR / "world.md").read_text(encoding="utf-8") if (BOOK_DATA_DIR / "world.md").exists() else ""
        canon_text = (BOOK_DATA_DIR / "canon.md").read_text(encoding="utf-8") if (BOOK_DATA_DIR / "canon.md").exists() else ""
        characters_text = (BOOK_DATA_DIR / "characters.md").read_text(encoding="utf-8") if (BOOK_DATA_DIR / "characters.md").exists() else ""
        voice_text = (BOOK_DATA_DIR / "voice.md").read_text(encoding="utf-8") if (BOOK_DATA_DIR / "voice.md").exists() else ""
        
        lore_data = f"=== WORLD BIBLE ===\n{world_text}\n\n=== ESTABLISHED CANON ===\n{canon_text}\n\n=== CHARACTER REGISTRY ===\n{characters_text}"
        
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
            pattern = rf'###\s*Ch(?:apter)?\s*{ch}\b.*?(?=###\s*Ch(?:apter)?\s*{ch + 1}\b|## Act|## Foreshadowing|$)'
            ch_outline_match = re.search(pattern, outline_text, re.DOTALL | re.IGNORECASE)
            ch_outline = ch_outline_match.group(0).strip() if ch_outline_match else f"Capítulo {ch}"
            
            # Extract chapter title
            title_match = re.search(r'###\s*Ch(?:apter)?\s*\d+:\s*(.*?)$', ch_outline, re.MULTILINE)
            ch_title = title_match.group(1).strip() if title_match else f"Capítulo {ch}"
            
            # Next chapter info for continuity
            next_pattern = rf'###\s*Ch(?:apter)?\s*{ch + 1}\b.*?(?=###\s*Ch(?:apter)?\s*{ch + 2}\b|## Act|## Foreshadowing|$)'
            next_match = re.search(next_pattern, outline_text, re.DOTALL | re.IGNORECASE)
            next_ch_outline = next_match.group(0).strip() if next_match else "(Fim do romance)"
            
            # Parse beats
            beats_section = re.search(r'\*\*Beats:\*\*\s*(.*?)(?=\n\s*\*\*|$)', ch_outline, re.DOTALL | re.IGNORECASE)
            beats = []
            if beats_section:
                for line in beats_section.group(1).split('\n'):
                    line = line.strip()
                    if line:
                        clean_beat = re.sub(r'^\d+\.\s*|-\s*', '', line).strip()
                        if clean_beat:
                            beats.append(clean_beat)
                            
            # Setup previous tail context
            prev_tail = ""
            prev_path = CHAPTERS_DIR / f"ch_{ch - 1:02d}.md"
            if prev_path.exists():
                prev_text = prev_path.read_text(encoding="utf-8").strip()
                prev_words = prev_text.split()
                prev_tail_words = prev_words[-1000:] if len(prev_words) > 1000 else prev_words
                prev_tail = " ".join(prev_tail_words)
            else:
                prev_tail = "(Este é o primeiro capítulo do livro, não há contexto anterior)"
            
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
                    print(f"[DraftChaptersStep] Found {len(beats)} beats in outline. Generating raw beats.")
                    for b_idx, beat_text in enumerate(beats, 1):
                        print(f"  [Beat {b_idx}/{len(beats)}] Drafting raw beat...")
                        
                        # 1. sliding window context from the previous beat
                        previous_beat_context = ""
                        if b_idx > 1:
                            prev_beat_file = tmp_dir / f"beat_{b_idx-1:02d}_raw.md"
                            if prev_beat_file.exists():
                                last_beat_text = prev_beat_file.read_text(encoding="utf-8").strip()
                                paragraphs = [p.strip() for p in last_beat_text.split('\n\n') if p.strip()]
                                last_paragraphs = paragraphs[-3:] if len(paragraphs) > 3 else paragraphs
                                previous_beat_context = "\n\n".join(last_paragraphs)
                        else:
                            previous_beat_context = prev_tail
                            
                        # 2. Roadmap logic
                        roadmap = []
                        for i, b in enumerate(beats, 1):
                            if i < b_idx:
                                roadmap.append(f"- Beat {i} (CONCLUÍDO): {b}")
                            elif i == b_idx:
                                roadmap.append(f"- Beat {i} (ESCREVA AGORA): {b}")
                            elif i == b_idx + 1:
                                roadmap.append(f"- Beat {i} (PRÓXIMO - transicione em direção a este ponto no final): {b}")
                            else:
                                roadmap.append(f"- Beat {i} (FUTURO): [Não escreva ou mencione este evento ainda]")
                        roadmap_text = "\n".join(roadmap)
                        
                        # 3. Drafting prompt
                        title_instruction = ""
                        if b_idx == 1:
                            title_instruction = (
                                f"IMPORTANTE: Como este é o primeiro Beat do capítulo, inicie a sua resposta com o título formatado exatamente assim (incluindo o caractere '#'):\n"
                                f"# {ch_title}\n\n"
                            )
                            
                        draft_prompt = (
                            f"Você é o DraftingAgent. Escreva a cena correspondente ao Beat {b_idx} do Capítulo {ch}.\n\n"
                            f"{title_instruction}"
                            f"DEFINIÇÃO DE VOZ / VOICE Profile (siga exatamente):\n{voice_text}\n\n"
                            f"WORLD BIBLE / DICIONÁRIO DO MUNDO:\n{world_text}\n\n"
                            f"ESTABELECIDO CANON / ESTABLISHED CANON (não cometa violações):\n{canon_text}\n\n"
                            f"ESTE CAPÍTULO TEM O SEGUINTE DESIGN:\n{roadmap_text}\n\n"
                            f"ESTA É A SUA TAREFA ATUAL:\n"
                            f"Escreva a cena correspondente ao Beat {b_idx}: {beats[b_idx-1]}\n\n"
                            f"GANCHO DE TRANSIÇÃO DO TEXTO ANTERIOR:\n{previous_beat_context}\n\n"
                            f"REGISTRO DE PERSONAGENS:\n{characters_text}\n\n"
                            f"Escreva apenas a cena na íntegra (~450 palavras), focando em ação e diálogo.\n"
                            f"ATENÇÃO CRÍTICA (NÃO ADICIONE PLOTS NOVOS OU DETALHES DE CONSPIRAÇÃO FORA DO ESBOÇO):\n"
                            f"- Siga as diretrizes de voz e o canon estritamente.\n"
                            f"- Helena NÃO tem histórico de demência, Alzheimer ou qualquer comprometimento cognitivo (ela tem apenas hipertensão controlada por losartana, e artrose grau 2 nas articulações das mãos). Ela é lúcida e perfeitamente funcional.\n"
                            f"- Escreva APENAS a cena correspondente ao Beat {b_idx}. Não invente novos personagens, novas salas secretas, vozes misteriosas, nem deuses ex machina.\n"
                            f"- O texto deve terminar logo após os eventos do Beat {b_idx}.\n"
                            f"ATENÇÃO: Retorne APENAS o texto da prosa da cena, sem comentários, notas ou outros cabeçalhos adicionais além do '#' se for o Beat 1."
                        )
                        
                        raw_beat = drafting_agent.execute(draft_prompt)
                        
                        # Save raw beat to logs/tmp_draft/
                        beat_file = tmp_dir / f"beat_{b_idx:02d}_raw.md"
                        beat_file.write_text(raw_beat, encoding="utf-8")
                        
                    # Concatenate raw beats to logs/tmp_draft/chapter_raw.md
                    chapter_raw_file = tmp_dir / "chapter_raw.md"
                    beats_content = []
                    for b_idx in range(1, len(beats) + 1):
                        beat_file = tmp_dir / f"beat_{b_idx:02d}_raw.md"
                        if beat_file.exists():
                            beats_content.append(beat_file.read_text(encoding="utf-8").strip())
                    chapter_raw_text = "\n\n".join(beats_content)
                    chapter_raw_file.write_text(chapter_raw_text, encoding="utf-8")
                else:
                    # Single chapter write fallback
                    print("[DraftChaptersStep] No beats found. Writing the entire chapter in one go.")
                    draft_prompt = (
                        f"Escreva o Capítulo {ch} completo.\n\n"
                        f"ESBOÇO DO CAPÍTULO:\n{ch_outline}\n\n"
                        f"CONTEXTO ANTERIOR:\n{prev_tail}\n\n"
                        f"PERSONAGENS:\n{characters_text}\n\n"
                        f"Escreva o texto completo do capítulo (~3000 palavras)."
                    )
                    chapter_raw_text = drafting_agent.execute(draft_prompt)
                    chapter_raw_file = tmp_dir / "chapter_raw.md"
                    chapter_raw_file.write_text(chapter_raw_text, encoding="utf-8")

                # Phase 2: Run Independent Critics
                print("[DraftChaptersStep] Running active critic agents...")
                context_args = {
                    "lore_data": lore_data,
                    "slop_rules": slop_rules
                }
                
                for role in self.critics_roles:
                    clean_name = role.replace("_critic", "")
                    filename = f"critique_{clean_name}.md"
                    print(f"  Running {role}...")
                    critic_agent = factory.get_agent(role, **context_args)
                    
                    critic_prompt = (
                        f"Você é o {critic_agent.name}.\n"
                        f"Seu objetivo é analisar o seguinte rascunho bruto de capítulo e gerar um relatório de críticas detalhado.\n\n"
                        f"RASCUNHO BRUTO DO CAPÍTULO:\n{chapter_raw_text}\n\n"
                        f"Siga as suas instruções de persona e as regras do sistema."
                    )
                    critique = critic_agent.execute(critic_prompt)
                    (tmp_dir / filename).write_text(critique, encoding="utf-8")

                # Phase 3: Sequential Synthesis
                print("[DraftChaptersStep] Starting sequential synthesis...")
                # Dynamically scan the tmp_dir for critique files to ensure flexibility
                critique_files = sorted(list(tmp_dir.glob("critique_*.md")))
                print(f"  Found {len(critique_files)} critique files to apply sequentially: {[f.name for f in critique_files]}")
                
                current_text = chapter_raw_text
                synthesis_agent = factory.get_agent("synthesis")
                
                for idx, crit_file in enumerate(critique_files, 1):
                    crit_name = crit_file.name
                    print(f"  [Synthesis Step {idx}/{len(critique_files)}] Applying critique: {crit_name}...")
                    critique_content = crit_file.read_text(encoding="utf-8")
                    
                    synth_prompt = (
                        f"Você é o SynthesisAgent. Seu objetivo é revisar e reescrever o texto do capítulo "
                        f"com base estritamente no Relatório de Crítica a seguir.\n\n"
                        f"TEXTO DO CAPÍTULO:\n{current_text}\n\n"
                        f"RELATÓRIO DE CRÍTICA APLICADA ({crit_name}):\n{critique_content}\n\n"
                        f"Instruções cruciais:\n"
                        f"- Resolva todos os problemas listados no Relatório de Crítica de forma integrada, fluida e sutil.\n"
                        f"- Certifique-se de que a resposta final contenha APENAS o texto completo da prosa do capítulo.\n"
                        f"- Absolutamente nenhuma análise, nota, cabeçalho explicativo, ou comentário adicional deve estar no resultado."
                    )
                    
                    current_text = synthesis_agent.execute(synth_prompt)
                    # Save intermediate step log
                    (tmp_dir / f"chapter_step_{idx:02d}_{crit_name}").write_text(current_text, encoding="utf-8")
                
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
