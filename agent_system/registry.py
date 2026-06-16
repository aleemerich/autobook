from typing import Dict, List
from agent_system.base import AgentSpec

_REGISTRY: Dict[str, AgentSpec] = {
    "drafting": AgentSpec(
        role="drafting",
        description="Agente responsável por escrever o rascunho narrativo bruto de um capítulo.",
        class_name="DraftingAgent"
    ),
    "stylist": AgentSpec(
        role="stylist",
        description="Agente responsável por refinar o rascunho com gênero, ritmo e estilo.",
        class_name="StylistAgent"
    ),
    "technical_editor": AgentSpec(
        role="technical_editor",
        description="Agente responsável por calibrar consistência técnica, lore e localização para PT-BR.",
        class_name="TechnicalEditorAgent"
    ),
    "canon_critic": AgentSpec(
        role="canon_critic",
        description="Agente crítico responsável por auditar o rascunho em relação ao cânone e lore.",
        class_name="CanonCriticAgent"
    ),
    "style_critic": AgentSpec(
        role="style_critic",
        description="Agente crítico responsável por auditar voz, estilo e clichês de IA (slop).",
        class_name="StyleCriticAgent"
    ),
    "flow_critic": AgentSpec(
        role="flow_critic",
        description="Agente crítico responsável por auditar ritmo, fluxo e transições de cenas.",
        class_name="FlowCriticAgent"
    ),
    "synthesis": AgentSpec(
        role="synthesis",
        description="Agente responsável por aplicar correções direcionadas a partir de relatórios de críticas.",
        class_name="SynthesisAgent"
    ),
}

def list_roles() -> List[str]:
    """Retorna a lista de papéis cadastrados no registry."""
    return list(_REGISTRY.keys())

def get_role_spec(role: str) -> AgentSpec:
    """Retorna a especificação de um papel. Levanta ValueError se o papel não existir."""
    if not role:
        raise ValueError("O nome do papel de agente não pode ser vazio.")
    role_key = role.lower().strip()
    if role_key not in _REGISTRY:
        raise ValueError(f"Papel de agente desconhecido: '{role}'")
    return _REGISTRY[role_key]
