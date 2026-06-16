from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

@dataclass
class CriticFinding:
    """Representa um problema ou achado específico apontado por um crítico."""
    source: str         # papel do crítico (ex: 'canon_critic')
    instruction: str    # instrução de correção/sugestão
    quote: str = ""     # trecho com problema
    severity: str = "medium"  # severidade (ex: 'low', 'medium', 'high')

    def to_dict(self) -> Dict[str, Any]:
        """Converte a instância para um dicionário serializável."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticFinding":
        """Recontrói a instância a partir de um dicionário."""
        return cls(
            source=data["source"],
            instruction=data["instruction"],
            quote=data.get("quote", ""),
            severity=data.get("severity", "medium")
        )

@dataclass
class CriticReport:
    """Representa o relatório consolidado de achados gerado por um único crítico."""
    critic_role: str
    findings: List[CriticFinding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converte a instância para um dicionário serializável."""
        return {
            "critic_role": self.critic_role,
            "findings": [f.to_dict() for f in self.findings]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticReport":
        """Recontrói a instância a partir de um dicionário."""
        findings = [CriticFinding.from_dict(f) for f in data.get("findings", [])]
        return cls(
            critic_role=data["critic_role"],
            findings=findings
        )

    @property
    def is_empty(self) -> bool:
        """Indica se o relatório não contém achados."""
        return len(self.findings) == 0

@dataclass
class RevisionPlan:
    """Representa o plano consolidado de revisões a ser aplicado ao rascunho."""
    findings: List[CriticFinding] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte a instância para um dicionário serializável."""
        return {
            "findings": [f.to_dict() for f in self.findings],
            "metadata": self.metadata.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RevisionPlan":
        """Recontrói a instância a partir de um dicionário."""
        findings = [CriticFinding.from_dict(f) for f in data.get("findings", [])]
        return cls(
            findings=findings,
            metadata=data.get("metadata", {}).copy()
        )

    @property
    def is_empty(self) -> bool:
        """Indica se o plano de revisão está vazio (sem achados)."""
        return len(self.findings) == 0

    @classmethod
    def consolidate(cls, reports: List[CriticReport], metadata: Dict[str, Any] | None = None) -> "RevisionPlan":
        """Consolida múltiplos relatórios de críticos em um único plano de revisão."""
        consolidated_findings = []
        for report in reports:
            consolidated_findings.extend(report.findings)
        return cls(
            findings=consolidated_findings,
            metadata=metadata if metadata is not None else {}
        )

@dataclass
class VerificationReport:
    """Representa o resultado do processo de verificação pós-revisão."""
    approved: bool
    critic_role: str
    feedback: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte a instância para um dicionário serializável."""
        return {
            "approved": self.approved,
            "critic_role": self.critic_role,
            "feedback": self.feedback,
            "metadata": self.metadata.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VerificationReport":
        """Recontrói a instância a partir de um dicionário."""
        return cls(
            approved=data["approved"],
            critic_role=data["critic_role"],
            feedback=data.get("feedback", ""),
            metadata=data.get("metadata", {}).copy()
        )
