#!/usr/bin/env python3
"""
tests/test_integration.py — Integration and flow tests for the new multi-agent pipeline.
Verifies AgentFactory, GenreStrategy, and mock runs of workflows using unittest.
"""

import os
import sys
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from agents import AgentFactory, DraftingAgent, StylistAgent, TechnicalEditorAgent
from genre_strategy import GenreStrategy
from pipelines.base import Step, Pipeline
from pipelines.book_generation import BookGenerationPipeline
from pipelines.editorial_revision import EditorialRevisionPipeline

class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary workspace directory structure
        self.test_dir = Path(__file__).parent / "tmp_workspace"
        self.test_dir.mkdir(exist_ok=True)
        
        self.book_data = self.test_dir / "book_data"
        self.book_data.mkdir(exist_ok=True)
        
        self.chapters = self.test_dir / "chapters"
        self.chapters.mkdir(exist_ok=True)
        
        self.genres = self.test_dir / "genres"
        self.genres.mkdir(exist_ok=True)
        
        # Write default reference files
        (self.book_data / "voice.md").write_text("Voice definition", encoding="utf-8")
        (self.book_data / "world.md").write_text("World definition", encoding="utf-8")
        (self.book_data / "characters.md").write_text("Characters definition", encoding="utf-8")
        (self.book_data / "canon.md").write_text("Canon definition", encoding="utf-8")
        (self.book_data / "outline.md").write_text("### Ch 1: Chapter One\n**Beats:**\n1. Beat number one\n", encoding="utf-8")
        
        # Write a default genre
        en_genres = self.genres / "EN"
        en_genres.mkdir(exist_ok=True)
        (en_genres / "drama.txt").write_text("PADRÕES A EVITAR\n1. AI tells\n", encoding="utf-8")
        
        pt_genres = self.genres / "PT-BR"
        pt_genres.mkdir(exist_ok=True)
        (pt_genres / "drama.txt").write_text("PADRÕES A EVITAR\n1. AI tells\n", encoding="utf-8")

    def tearDown(self):
        # Clean up temporary workspace
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_agent_factory_instantiation(self):
        """Verifies default agents can be registered and fetched from factory."""
        factory = AgentFactory()
        
        # 1. Fetch Drafting Agent
        drafting = factory.get_agent("drafting")
        self.assertTrue(isinstance(drafting, DraftingAgent))
        
        # 2. Fetch Stylist Agent
        stylist = factory.get_agent("stylist", genre_rules="Suspense anime rules")
        self.assertTrue(isinstance(stylist, StylistAgent))
        self.assertIn("Suspense anime rules", stylist.system_prompt)
        
        # 3. Fetch Technical Editor Agent
        tech = factory.get_agent("technical_editor", lore_data="Some lore data", slop_rules="No slop")
        self.assertTrue(isinstance(tech, TechnicalEditorAgent))
        self.assertIn("Some lore data", tech.system_prompt)
        self.assertIn("No slop", tech.system_prompt)

    @patch("genre_strategy.BASE_DIR")
    def test_genre_strategy_resolution(self, mock_base_dir):
        """Verifies GenreStrategy correctly falls back to EN/drama when files are missing."""
        mock_base_dir.return_value = self.test_dir
        
        strategy = GenreStrategy(genre="drama", language="EN")
        strategy.genres_dir = self.test_dir / "genres"
        strategy._load_strategy()
        
        self.assertIn("AI tells", strategy.get_style_guidelines())
        self.assertEqual(len(strategy.get_anti_patterns()), 1)
        self.assertEqual(strategy.get_anti_patterns()[0], "AI tells")

    @patch("pipelines.book_generation.evaluate_chapter")
    @patch("pipelines.book_generation_steps.persistence.git_push")
    @patch("pipelines.book_generation_steps.persistence.git_commit")
    @patch("pipelines.book_generation_steps.persistence.git_add")
    @patch("pipelines.book_generation_steps.persistence.subprocess.run")
    @patch("agents.call_llm")
    def test_book_generation_pipeline_mock_run(
        self,
        mock_call_llm,
        mock_subprocess,
        mock_git_add,
        mock_git_commit,
        mock_git_push,
        mock_eval_chapter
    ):
        """Performs a sandboxed, mock-based run of BookGenerationPipeline."""
        mock_call_llm.return_value = "Mocked chapter/scene output content."
        
        # Mock evaluate_chapter to return score >= threshold (e.g. 7.5)
        mock_eval_chapter.return_value = {
            "overall_score": 8.0,
            "slop": {
                "slop_penalty": 0.0,
                "tier1_hits": [],
                "tier2_hits": []
            }
        }
        
        # Mock subprocess run to simulate successful verify_continuity.py (exit code 0)
        mock_sub_run = MagicMock()
        mock_sub_run.returncode = 0
        mock_subprocess.return_value = mock_sub_run

        # Patch base directories in pipeline
        with patch("pipelines.book_generation.BOOK_DATA_DIR", self.book_data), \
             patch("pipelines.book_generation.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.BASE_DIR", self.test_dir):
             
            pipeline = BookGenerationPipeline()
            
            # Context setup
            context = {
                "from_scratch": True,
                "yes": True
            }
            
            pipeline.run(context)
            
            # Check that chapter draft was generated and written
            ch_file = self.chapters / "ch_01.md"
            self.assertTrue(ch_file.exists())
            self.assertIn("Mocked chapter/scene output content.", ch_file.read_text(encoding="utf-8"))
            
            # Verify state was saved
            state_file = self.book_data / "state.json"
            self.assertTrue(state_file.exists())
            state = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(state["chapters_drafted"], 1)

    @patch("pipelines.book_generation.evaluate_chapter")
    @patch("pipelines.book_generation_steps.persistence.git_push")
    @patch("pipelines.book_generation_steps.persistence.git_commit")
    @patch("pipelines.book_generation_steps.persistence.git_add")
    @patch("pipelines.book_generation_steps.persistence.subprocess.run")
    @patch("agents.call_llm")
    def test_book_generation_pipeline_prompts_contain_voice_world_canon(
        self,
        mock_call_llm,
        mock_subprocess,
        mock_git_add,
        mock_git_commit,
        mock_git_push,
        mock_eval_chapter
    ):
        """Verifies that the generated prompts for DraftingAgent and StylistAgent contain the voice, world, and canon references."""
        mock_call_llm.return_value = "Mocked chapter/scene output content."
        mock_eval_chapter.return_value = {
            "overall_score": 8.0,
            "slop": {
                "slop_penalty": 0.0,
                "tier1_hits": [],
                "tier2_hits": []
            }
        }
        mock_sub_run = MagicMock()
        mock_sub_run.returncode = 0
        mock_subprocess.return_value = mock_sub_run

        with patch("pipelines.book_generation.BOOK_DATA_DIR", self.book_data), \
             patch("pipelines.book_generation.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.BASE_DIR", self.test_dir):
             
            pipeline = BookGenerationPipeline()
            pipeline.run({"from_scratch": True, "yes": True})
            
            # Check all call arguments to call_llm
            called_prompts = [call.kwargs.get("prompt", "") for call in mock_call_llm.call_args_list]
            
            # The drafting prompt should contain voice, world, and canon
            drafting_prompt_calls = [p for p in called_prompts if "DraftingAgent" in p]
            self.assertTrue(len(drafting_prompt_calls) > 0)
            for dp in drafting_prompt_calls:
                self.assertIn("DEFINIÇÃO DE VOZ / VOICE Profile", dp)
                self.assertIn("WORLD BIBLE / DICIONÁRIO DO MUNDO", dp)
                self.assertIn("ESTABELECIDO CANON / ESTABLISHED CANON", dp)
                
            # Check critic calls
            canon_critic_calls = [p for p in called_prompts if "CanonCriticAgent" in p]
            self.assertTrue(len(canon_critic_calls) > 0)
            
            style_critic_calls = [p for p in called_prompts if "StyleCriticAgent" in p]
            self.assertTrue(len(style_critic_calls) > 0)
            
            flow_critic_calls = [p for p in called_prompts if "FlowCriticAgent" in p]
            self.assertTrue(len(flow_critic_calls) > 0)
            
            # Check synthesis calls
            synthesis_calls = [p for p in called_prompts if "SynthesisAgent" in p]
            self.assertTrue(len(synthesis_calls) > 0)

    @patch("pipelines.book_generation.evaluate_chapter")
    @patch("pipelines.book_generation_steps.persistence.git_push")
    @patch("pipelines.book_generation_steps.persistence.git_commit")
    @patch("pipelines.book_generation_steps.persistence.git_add")
    @patch("pipelines.book_generation_steps.persistence.subprocess.run")
    @patch("agents.call_llm")
    def test_book_generation_pipeline_skips_chapters(
        self,
        mock_call_llm,
        mock_subprocess,
        mock_git_add,
        mock_git_commit,
        mock_git_push,
        mock_eval_chapter
    ):
        """Verifies that the generation pipeline skips chapters not present in context['chapters']."""
        mock_call_llm.return_value = "Mocked chapter/scene output content."
        mock_eval_chapter.return_value = {
            "overall_score": 8.0,
            "slop": {
                "slop_penalty": 0.0,
                "tier1_hits": [],
                "tier2_hits": []
            }
        }
        mock_sub_run = MagicMock()
        mock_sub_run.returncode = 0
        mock_subprocess.return_value = mock_sub_run

        with patch("pipelines.book_generation.BOOK_DATA_DIR", self.book_data), \
             patch("pipelines.book_generation.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.BASE_DIR", self.test_dir):
             
            pipeline = BookGenerationPipeline()
            # Request only chapter 2, but outline only has chapter 1
            pipeline.run({"from_scratch": True, "yes": True, "chapters": [2]})
            
            # Since outline has Ch 1, and we skipped it, no draft should be written for ch_01
            ch_file = self.chapters / "ch_01.md"
            self.assertFalse(ch_file.exists())

    @patch("pipelines.book_generation.evaluate_chapter")
    @patch("pipelines.book_generation_steps.persistence.git_push")
    @patch("pipelines.book_generation_steps.persistence.git_commit")
    @patch("pipelines.book_generation_steps.persistence.git_add")
    @patch("pipelines.book_generation_steps.persistence.subprocess.run")
    @patch("agents.call_llm")
    def test_book_generation_pipeline_masks_future_beats(
        self,
        mock_call_llm,
        mock_subprocess,
        mock_git_add,
        mock_git_commit,
        mock_git_push,
        mock_eval_chapter
    ):
        """Verifies that future beats are masked in the roadmap passed to the DraftingAgent."""
        mock_call_llm.return_value = "Mocked chapter/scene output content."
        mock_eval_chapter.return_value = {
            "overall_score": 8.0,
            "slop": {
                "slop_penalty": 0.0,
                "tier1_hits": [],
                "tier2_hits": []
            }
        }
        mock_sub_run = MagicMock()
        mock_sub_run.returncode = 0
        mock_subprocess.return_value = mock_sub_run

        # Outline with 3 beats
        (self.book_data / "outline.md").write_text(
            "### Ch 1: Chapter One\n**Beats:**\n1. Beat number one\n2. Beat number two\n3. Beat number three\n", 
            encoding="utf-8"
        )

        with patch("pipelines.book_generation.BOOK_DATA_DIR", self.book_data), \
             patch("pipelines.book_generation.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.CHAPTERS_DIR", self.chapters), \
             patch("evaluate.BASE_DIR", self.test_dir):
             
            pipeline = BookGenerationPipeline()
            pipeline.run({"from_scratch": True, "yes": True})
            
            called_prompts = [call.kwargs.get("prompt", "") for call in mock_call_llm.call_args_list]
            drafting_prompts = [p for p in called_prompts if "DraftingAgent" in p]
            
            # We expect 3 beats to call the drafting agent
            self.assertEqual(len(drafting_prompts), 3)
            
            # Beat 1 call: Beat 2 is PRÓXIMO, Beat 3 is FUTURO (masked)
            beat_1_prompt = drafting_prompts[0]
            self.assertTrue(any(line in beat_1_prompt for line in [
                "- Beat 1 (ESCREVA AGORA): Beat number one",
                "- Beat 2 (PRÓXIMO - transicione em direção a este ponto no final): Beat number two",
                "- Beat 3 (FUTURO): [Não escreva ou mencione este evento ainda]"
            ]))
            self.assertNotIn("Beat number three", beat_1_prompt)
            
            # Beat 2 call: Beat 1 is CONCLUÍDO, Beat 2 is ESCREVA AGORA, Beat 3 is PRÓXIMO
            beat_2_prompt = drafting_prompts[1]
            self.assertTrue(any(line in beat_2_prompt for line in [
                "- Beat 1 (CONCLUÍDO): Beat number one",
                "- Beat 2 (ESCREVA AGORA): Beat number two",
                "- Beat 3 (PRÓXIMO - transicione em direção a este ponto no final): Beat number three"
            ]))

if __name__ == "__main__":
    unittest.main()
