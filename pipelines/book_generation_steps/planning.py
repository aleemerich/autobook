from typing import List

def build_roadmap_text(beats: List[str], current_beat_idx: int) -> str:
    """Gera o design/roadmap do capítulo a partir do beat corrente (1-indexed)."""
    roadmap = []
    for i, b in enumerate(beats, 1):
        if i < current_beat_idx:
            roadmap.append(f"- Beat {i} (CONCLUÍDO): {b}")
        elif i == current_beat_idx:
            roadmap.append(f"- Beat {i} (ESCREVA AGORA): {b}")
        elif i == current_beat_idx + 1:
            roadmap.append(f"- Beat {i} (PRÓXIMO - transicione em direção a este ponto no final): {b}")
        else:
            roadmap.append(f"- Beat {i} (FUTURO): [Não escreva ou mencione este evento ainda]")
    return "\n".join(roadmap)

def build_title_instruction(ch_title: str, current_beat_idx: int) -> str:
    """Retorna a instrução do título caso seja o primeiro beat (1-indexed)."""
    if current_beat_idx == 1:
        return (
            f"IMPORTANTE: Como este é o primeiro Beat do capítulo, inicie a sua resposta com o título formatado exatamente assim (incluindo o caractere '#'):\n"
            f"# {ch_title}\n\n"
        )
    return ""

def build_beat_draft_prompt(
    b_idx: int,
    ch: int,
    title_instruction: str,
    voice_text: str,
    world_text: str,
    canon_text: str,
    roadmap_text: str,
    beat_text: str,
    previous_beat_context: str,
    characters_text: str
) -> str:
    """Monta o prompt para rascunhar o beat."""
    return (
        f"Você é o DraftingAgent. Escreva a cena correspondente ao Beat {b_idx} do Capítulo {ch}.\n\n"
        f"{title_instruction}"
        f"DEFINIÇÃO DE VOZ / VOICE Profile (siga exatamente):\n{voice_text}\n\n"
        f"WORLD BIBLE / DICIONÁRIO DO MUNDO:\n{world_text}\n\n"
        f"ESTABELECIDO CANON / ESTABLISHED CANON (não cometa violações):\n{canon_text}\n\n"
        f"ESTE CAPÍTULO TEM O SEGUINTE DESIGN:\n{roadmap_text}\n\n"
        f"ESTA É A SUA TAREFA ATUAL:\n"
        f"Escreva a cena correspondente ao Beat {b_idx}: {beat_text}\n\n"
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

def build_chapter_draft_prompt(
    ch: int,
    ch_outline: str,
    prev_tail: str,
    characters_text: str
) -> str:
    """Monta o prompt para rascunhar o capítulo completo."""
    return (
        f"Escreva o Capítulo {ch} completo.\n\n"
        f"ESBOÇO DO CAPÍTULO:\n{ch_outline}\n\n"
        f"CONTEXTO ANTERIOR:\n{prev_tail}\n\n"
        f"PERSONAGENS:\n{characters_text}\n\n"
        f"Escreva o texto completo do capítulo (~3000 palavras)."
    )
