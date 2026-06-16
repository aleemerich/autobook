from typing import Any
from agent_system.registry import get_role_spec

def create_agent(role: str, **kwargs) -> Any:
    """
    Cria uma instância de um agente legado a partir de agents.py,
    delegando para a fábrica original.
    """
    # Importa tardiamente para evitar qualquer dependência circular
    import agents
    legacy_factory = agents.AgentFactory()

    # Valida se o papel existe no novo registry ou se foi registrado dinamicamente na factory legada
    role_key = role.lower().strip() if role else ""
    if role_key not in legacy_factory._agents_registry:
        get_role_spec(role)

    return legacy_factory.get_agent(role, **kwargs)

class AgentFactory:
    """Fábrica moderna do sistema de agentes, servindo como wrapper compatível."""

    def get_agent(self, role: str, **kwargs) -> Any:
        return create_agent(role, **kwargs)

    def register_agent(self, role: str, agent_class: Any) -> None:
        """Registra um novo agente dinamicamente delegando para a fábrica legada."""
        import agents
        agents.AgentFactory().register_agent(role, agent_class)

    def load_skill_agent(self, skill_name: str, **kwargs) -> Any:
        """Carrega dinamicamente um agente especialista delegando para a fábrica legada."""
        import agents
        return agents.AgentFactory().load_skill_agent(skill_name, **kwargs)
