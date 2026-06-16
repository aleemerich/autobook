from typing import Any
from agent_system.registry import get_role_spec

def create_agent(role: str, **kwargs) -> Any:
    """
    Cria uma instância de um agente legado a partir de agents.py,
    delegando para a fábrica original.
    """
    # Valida se o papel existe no novo registry (levanta ValueError se não existir)
    get_role_spec(role)

    # Importa tardiamente para evitar qualquer dependência circular
    import agents
    legacy_factory = agents.AgentFactory()
    return legacy_factory.get_agent(role, **kwargs)

class AgentFactory:
    """Fábrica moderna do sistema de agentes, servindo como wrapper compatível."""

    def get_agent(self, role: str, **kwargs) -> Any:
        return create_agent(role, **kwargs)
