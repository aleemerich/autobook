from dataclasses import dataclass

class BaseAgent:
    """Classe base contratual para todos os agentes literários."""

    def __init__(self, name: str, system_prompt: str, temperature: float = 0.7):
        self.name = name
        self.system_prompt = system_prompt
        self.temperature = temperature

    def execute(self, prompt: str) -> str:
        """Executa a chamada ao LLM com a persona/instruções específicas do agente."""
        raise NotImplementedError("Subclasses devem implementar o método execute.")

@dataclass(frozen=True)
class AgentSpec:
    """Especificação de metadados para um papel de agente."""
    role: str
    description: str
    class_name: str
