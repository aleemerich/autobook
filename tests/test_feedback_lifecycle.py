import pytest
from writing import (
    CriticFinding,
    CriticReport,
    RevisionPlan,
    VerificationReport
)

def test_create_valid_critic_finding() -> None:
    """Valida a criação de um CriticFinding com valores válidos."""
    finding = CriticFinding(
        source="canon_critic",
        instruction="Remover contradição de idade do personagem",
        quote="Helena tinha 45 anos...",
        severity="high"
    )
    assert finding.source == "canon_critic"
    assert finding.instruction == "Remover contradição de idade do personagem"
    assert finding.quote == "Helena tinha 45 anos..."
    assert finding.severity == "high"

def test_critic_report_empty_and_with_findings() -> None:
    """Valida o comportamento de CriticReport vazio e com achados."""
    # Vazio
    report_empty = CriticReport(critic_role="style_critic")
    assert report_empty.critic_role == "style_critic"
    assert report_empty.findings == []
    assert report_empty.is_empty is True

    # Com achados
    finding = CriticFinding(
        source="style_critic",
        instruction="Substituir clichê AI 'farol de esperança'",
        quote="Ele era o farol de esperança...",
        severity="medium"
    )
    report = CriticReport(critic_role="style_critic", findings=[finding])
    assert report.is_empty is False
    assert len(report.findings) == 1
    assert report.findings[0] == finding

def test_consolidate_multiple_reports_to_revision_plan() -> None:
    """Valida a consolidação de relatórios de críticos distintos em um único RevisionPlan."""
    finding_canon = CriticFinding(
        source="canon_critic",
        instruction="Corrigir consistência de data",
        quote="no ano de 2045...",
        severity="high"
    )
    report_canon = CriticReport(critic_role="canon_critic", findings=[finding_canon])

    finding_style = CriticFinding(
        source="style_critic",
        instruction="Substituir palavra repetida",
        quote="sorriso melancólico",
        severity="low"
    )
    report_style = CriticReport(critic_role="style_critic", findings=[finding_style])

    metadata = {"chapter": 3, "attempt": 1}
    plan = RevisionPlan.consolidate([report_canon, report_style], metadata=metadata)

    assert plan.is_empty is False
    assert len(plan.findings) == 2
    assert plan.findings[0] == finding_canon
    assert plan.findings[1] == finding_style
    assert plan.metadata == metadata

def test_revision_plan_empty() -> None:
    """Valida comportamento de RevisionPlan vazio."""
    plan = RevisionPlan()
    assert plan.is_empty is True
    assert plan.findings == []

def test_serialization_and_deserialization() -> None:
    """Valida que todos os contratos podem ser serializados em dict e desserializados perfeitamente."""
    # 1. CriticFinding
    finding = CriticFinding(source="flow_critic", instruction="Melhorar transição", quote="E então...", severity="medium")
    finding_dict = finding.to_dict()
    finding_back = CriticFinding.from_dict(finding_dict)
    assert finding == finding_back

    # 2. CriticReport
    report = CriticReport(critic_role="flow_critic", findings=[finding])
    report_dict = report.to_dict()
    report_back = CriticReport.from_dict(report_dict)
    assert report.critic_role == report_back.critic_role
    assert len(report_back.findings) == 1
    assert report_back.findings[0] == finding

    # 3. RevisionPlan
    plan = RevisionPlan(findings=[finding], metadata={"editor": "AI"})
    plan_dict = plan.to_dict()
    plan_back = RevisionPlan.from_dict(plan_dict)
    assert len(plan_back.findings) == 1
    assert plan_back.findings[0] == finding
    assert plan_back.metadata == {"editor": "AI"}

    # 4. VerificationReport
    ver_report = VerificationReport(approved=True, critic_role="canon_critic", feedback="Cânone validado", metadata={"check": "ok"})
    ver_dict = ver_report.to_dict()
    ver_back = VerificationReport.from_dict(ver_dict)
    assert ver_report.approved == ver_back.approved
    assert ver_report.critic_role == ver_back.critic_role
    assert ver_report.feedback == ver_back.feedback
    assert ver_report.metadata == ver_back.metadata

def test_verification_report_approved_and_rejected() -> None:
    """Valida a instanciação de VerificationReport aprovados e reprovados."""
    approved_rep = VerificationReport(approved=True, critic_role="style_critic", feedback="Texto excelente!")
    assert approved_rep.approved is True
    assert approved_rep.critic_role == "style_critic"

    rejected_rep = VerificationReport(approved=False, critic_role="canon_critic", feedback="Erro de lore grave na linha 45")
    assert rejected_rep.approved is False
    assert rejected_rep.critic_role == "canon_critic"

def test_mutable_defaults_isolation() -> None:
    """Valida que as instâncias dos relatórios e planos possuem listas/dicts isolados de default."""
    r1 = CriticReport(critic_role="canon")
    r2 = CriticReport(critic_role="style")

    r1.findings.append(CriticFinding(source="canon", instruction="fix age"))
    # R2 não deve sofrer alteração
    assert len(r2.findings) == 0

    p1 = RevisionPlan()
    p2 = RevisionPlan()
    p1.findings.append(CriticFinding(source="style", instruction="fix slop"))
    p1.metadata["test"] = 123

    assert len(p2.findings) == 0
    assert p2.metadata == {}
