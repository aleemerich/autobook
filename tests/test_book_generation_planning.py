import pytest
from pipelines.book_generation_steps.planning import (
    build_roadmap_text,
    build_title_instruction,
    build_beat_draft_prompt,
    build_chapter_draft_prompt
)

def test_roadmap_first_beat() -> None:
    """Valida que o roadmap do primeiro beat marca o atual, próximo e futuros corretamente."""
    beats = ["Beat One", "Beat Two", "Beat Three"]
    roadmap = build_roadmap_text(beats, 1)
    
    # Primeiro: ESCREVA AGORA
    assert "- Beat 1 (ESCREVA AGORA): Beat One" in roadmap
    # Segundo: PRÓXIMO
    assert "- Beat 2 (PRÓXIMO - transicione em direção a este ponto no final): Beat Two" in roadmap
    # Terceiro: FUTURO
    assert "- Beat 3 (FUTURO): [Não escreva ou mencione este evento ainda]" in roadmap

def test_roadmap_intermediate_beat() -> None:
    """Valida que o roadmap de beat intermediário marca anteriores como concluídos."""
    beats = ["Beat One", "Beat Two", "Beat Three"]
    roadmap = build_roadmap_text(beats, 2)
    
    # Primeiro: CONCLUÍDO
    assert "- Beat 1 (CONCLUÍDO): Beat One" in roadmap
    # Segundo: ESCREVA AGORA
    assert "- Beat 2 (ESCREVA AGORA): Beat Two" in roadmap
    # Terceiro: PRÓXIMO
    assert "- Beat 3 (PRÓXIMO - transicione em direção a este ponto no final): Beat Three" in roadmap

def test_roadmap_last_beat() -> None:
    """Valida que o roadmap do último beat não cria um próximo beat inexistente."""
    beats = ["Beat One", "Beat Two", "Beat Three"]
    roadmap = build_roadmap_text(beats, 3)
    
    # Primeiro e Segundo: CONCLUÍDO
    assert "- Beat 1 (CONCLUÍDO): Beat One" in roadmap
    assert "- Beat 2 (CONCLUÍDO): Beat Two" in roadmap
    # Terceiro: ESCREVA AGORA
    assert "- Beat 3 (ESCREVA AGORA): Beat Three" in roadmap
    # Não deve haver Beat 4 / PRÓXIMO
    assert "Beat 4" not in roadmap
    assert "PRÓXIMO" not in roadmap

def test_title_instruction_only_on_beat_1() -> None:
    """Valida que a instrução do título aparece somente no beat 1."""
    title = "O Mistério da Estrela"
    
    instr1 = build_title_instruction(title, 1)
    assert "IMPORTANTE: Como este é o primeiro Beat do capítulo" in instr1
    assert f"# {title}" in instr1
    
    instr2 = build_title_instruction(title, 2)
    assert instr2 == ""

def test_beat_prompt_structure() -> None:
    """Valida que o prompt de beat preserva voz, world, canon, roadmap, beat atual, contexto anterior e personagens."""
    title_instruction = "TITLE_INSTRUCTION_MOCK"
    voice_text = "VOICE_TEXT_MOCK"
    world_text = "WORLD_TEXT_MOCK"
    canon_text = "CANON_TEXT_MOCK"
    roadmap_text = "ROADMAP_TEXT_MOCK"
    beat_text = "BEAT_TEXT_MOCK"
    previous_beat_context = "PREV_BEAT_CONTEXT_MOCK"
    characters_text = "CHARS_TEXT_MOCK"
    
    prompt = build_beat_draft_prompt(
        b_idx=2,
        ch=3,
        title_instruction=title_instruction,
        voice_text=voice_text,
        world_text=world_text,
        canon_text=canon_text,
        roadmap_text=roadmap_text,
        beat_text=beat_text,
        previous_beat_context=previous_beat_context,
        characters_text=characters_text
    )
    
    assert "Você é o DraftingAgent. Escreva a cena correspondente ao Beat 2 do Capítulo 3." in prompt
    assert title_instruction in prompt
    assert f"DEFINIÇÃO DE VOZ / VOICE Profile (siga exatamente):\n{voice_text}" in prompt
    assert f"WORLD BIBLE / DICIONÁRIO DO MUNDO:\n{world_text}" in prompt
    assert f"ESTABELECIDO CANON / ESTABLISHED CANON (não cometa violações):\n{canon_text}" in prompt
    assert f"ESTE CAPÍTULO TEM O SEGUINTE DESIGN:\n{roadmap_text}" in prompt
    assert f"ESTA É A SUA TAREFA ATUAL:\nEscreva a cena correspondente ao Beat 2: {beat_text}" in prompt
    assert f"GANCHO DE TRANSIÇÃO DO TEXTO ANTERIOR:\n{previous_beat_context}" in prompt
    assert f"REGISTRO DE PERSONAGENS:\n{characters_text}" in prompt
    # Certifica a presença do aviso de saúde mental sobre Helena
    assert "Helena NÃO tem histórico de demência" in prompt

def test_beat_prompt_beat_1_includes_title() -> None:
    """Valida que o prompt do beat 1 inclui a instrução de título e o beat >1 não inclui."""
    title = "Chapter Title"
    title_instruction = build_title_instruction(title, 1)
    
    prompt1 = build_beat_draft_prompt(
        b_idx=1,
        ch=1,
        title_instruction=title_instruction,
        voice_text="",
        world_text="",
        canon_text="",
        roadmap_text="",
        beat_text="start",
        previous_beat_context="",
        characters_text=""
    )
    assert f"# {title}" in prompt1
    
    # Beat 2
    title_instruction_2 = build_title_instruction(title, 2)
    prompt2 = build_beat_draft_prompt(
        b_idx=2,
        ch=1,
        title_instruction=title_instruction_2,
        voice_text="",
        world_text="",
        canon_text="",
        roadmap_text="",
        beat_text="middle",
        previous_beat_context="",
        characters_text=""
    )
    assert "# Chapter Title" not in prompt2

def test_chapter_draft_prompt_structure() -> None:
    """Valida que o prompt do capítulo completo preserva outline, contexto anterior e personagens."""
    ch_outline = "OUTLINE_MOCK"
    prev_tail = "PREV_TAIL_MOCK"
    characters_text = "CHARS_TEXT_MOCK"
    
    prompt = build_chapter_draft_prompt(
        ch=5,
        ch_outline=ch_outline,
        prev_tail=prev_tail,
        characters_text=characters_text
    )
    
    assert "Escreva o Capítulo 5 completo." in prompt
    assert f"ESBOÇO DO CAPÍTULO:\n{ch_outline}" in prompt
    assert f"CONTEXTO ANTERIOR:\n{prev_tail}" in prompt
    assert f"PERSONAGENS:\n{characters_text}" in prompt
    assert "Escreva o texto completo do capítulo (~3000 palavras)." in prompt
