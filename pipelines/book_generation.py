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
    def __init__(self):
        super().__init__("Draft Chapters sequentially")

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
        
        lore_data = f"=== WORLD BIBLE ===\n{world_text}\n\n=== ESTABLISHED CANON ===\n{canon_text}"
        
        # Agents instantiation
        drafting_agent = factory.get_agent("drafting")
        stylist_agent = factory.get_agent("stylist", genre_rules=genre_rules)
        tech_editor_agent = factory.get_agent("technical_editor", lore_data=lore_data, slop_rules=slop_rules)
        
        # Max attempts and threshold
        max_attempts = int(os.environ.get("MAX_CHAPTER_ATTEMPTS", 3))
        threshold = float(os.environ.get("CHAPTER_THRESHOLD", 6.2))
        
        target_chapters = context.get("chapters")
        
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
                
            drafted = False
            best_draft_text = ""
            best_draft_score = -1.0
            
            for attempt in range(1, max_attempts + 1):
                print(f"\n--- Chapter {ch} - Attempt {attempt}/{max_attempts} ---")
                
                chapter_content = []
                
                # Dynamic cascading beat-by-beat generation
                if beats:
                    print(f"[DraftChaptersStep] Found {len(beats)} beats in outline. Writing beat by beat.")
                    for b_idx, beat_text in enumerate(beats, 1):
                        print(f"  [Beat {b_idx}/{len(beats)}] Generating...")
                        
                        # 1. Preparar contexto do beat anterior (Janela Deslizante)
                        previous_beat_context = ""
                        if b_idx > 1 and chapter_content:
                            last_beat_text = chapter_content[-1].strip()
                            paragraphs = [p.strip() for p in last_beat_text.split('\n\n') if p.strip()]
                            last_paragraphs = paragraphs[-3:] if len(paragraphs) > 3 else paragraphs
                            previous_beat_context = "\n\n".join(last_paragraphs)
                        else:
                            previous_beat_context = prev_tail  # Fim do capítulo anterior para o Beat 1

                        # 2. Roteiro do capítulo (Roadmap)
                        roadmap = []
                        for i, b in enumerate(beats, 1):
                            status = " (Escrevendo agora)" if i == b_idx else (" (Concluído)" if i < b_idx else " (Pendente)")
                            roadmap.append(f"- Beat {i}: {b}{status}")
                        roadmap_text = "\n".join(roadmap)

                        # 3. Drafting Agent
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
                            f"- Escreva APENAS a cena correspondente ao Beat {b_idx}. Não invente novos personagens, novas salas secretas, vozes misteriosas, nem deuses ex machina.\n"
                            f"- O texto deve terminar logo após os eventos do Beat {b_idx}.\n"
                            f"ATENÇÃO: Retorne APENAS o texto da prosa da cena, sem comentários, notas ou outros cabeçalhos adicionais além do '#' se for o Beat 1."
                        )
                        raw_beat = drafting_agent.execute(draft_prompt)
                        
                        # 2. Stylist Agent
                        stylist_prompt = (
                            f"Você é o StylistAgent. Refine o rascunho de cena a seguir injetando suspense, tensão e rigor de thriller especulativo.\n\n"
                            f"RASCUNHO DA CENA:\n{raw_beat}\n\n"
                            f"DEFINIÇÃO DE VOZ / VOICE Profile (siga exatamente):\n{voice_text}\n\n"
                            f"REGRAS DE ESTILO:\n{genre_rules}\n\n"
                            f"ATENÇÃO: Retorne APENAS o texto refinado da prosa da cena. Preserve a formatação de título '#' do primeiro beat se estiver presente. Não inclua notas, preâmbulos, resumos ou explicações."
                        )
                        stylized_beat = stylist_agent.execute(stylist_prompt)
                        
                        # 3. Technical Editor Agent
                        editor_prompt = (
                            f"Você é o TechnicalEditorAgent. Revise a cena estilizada para remover qualquer vício de IA, slop, ou termos de PT-PT (conversão rigorosa para PT-BR) e alinhar com o lore.\n\n"
                            f"CENA:\n{stylized_beat}\n\n"
                            f"REGRAS LORE & SLOP:\n{tech_editor_agent.system_prompt}\n\n"
                            f"ATENÇÃO CRÍTICA: Retorne APENAS o texto final da prosa revisada da cena. Preserve o título '#' no início se estiver presente. "
                            f"Não inclua NENHUM tipo de relatório de revisão, resumos de alterações, comentários ou explicações antes ou depois do texto."
                        )
                        refined_beat = tech_editor_agent.execute(editor_prompt)
                        
                        # 4. Pós-processamento e Sanitização em Python (Garantia de Prosa Limpa)
                        lines = refined_beat.split("\n")
                        clean_lines = []
                        title_kept = False
                        for line in lines:
                            stripped = line.strip()
                            if stripped.startswith("#"):
                                # Apenas permite o H1 (iniciado com '# ') no primeiro beat
                                if b_idx == 1 and stripped.startswith("# ") and not title_kept:
                                    clean_lines.append(line)
                                    title_kept = True
                            else:
                                clean_lines.append(line)
                        refined_beat = "\n".join(clean_lines).strip()
                        
                        chapter_content.append(refined_beat)
                else:
                    print("[DraftChaptersStep] No beats found. Writing the entire chapter in one go.")
                    draft_prompt = (
                        f"Escreva o Capítulo {ch} completo.\n\n"
                        f"ESBOÇO DO CAPÍTULO:\n{ch_outline}\n\n"
                        f"CONTEXTO ANTERIOR:\n{prev_tail}\n\n"
                        f"PERSONAGENS:\n{characters_text}\n\n"
                        f"Escreva o texto completo do capítulo (~3000 palavras)."
                    )
                    raw_ch = drafting_agent.execute(draft_prompt)
                    
                    stylist_prompt = (
                        f"Refine o rascunho do capítulo a seguir com suspense e ritmo.\n\n"
                        f"TEXTO:\n{raw_ch}\n\n"
                        f"REGRAS DE ESTILO:\n{genre_rules}"
                    )
                    stylized_ch = stylist_agent.execute(stylist_prompt)
                    
                    editor_prompt = (
                        f"Revise o capítulo para remover slop, PT-PT e verificar o lore.\n\n"
                        f"TEXTO:\n{stylized_ch}"
                    )
                    refined_ch = tech_editor_agent.execute(editor_prompt)
                    chapter_content.append(refined_ch)
                    
                full_chapter_text = "\n\n".join(chapter_content)
                
                # Save draft temporarily
                ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
                ch_file.parent.mkdir(exist_ok=True)
                ch_file.write_text(full_chapter_text, encoding="utf-8")
                
                # Evaluate
                print(f"[DraftChaptersStep] Evaluating Chapter {ch}...")
                eval_res = evaluate_chapter(ch)
                score = eval_res.get("overall_score", 0.0)
                print(f"[DraftChaptersStep] Chapter {ch} Evaluation Score: {score}")
                
                if score > best_draft_score:
                    best_draft_score = score
                    best_draft_text = full_chapter_text
                    
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
