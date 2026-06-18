from pathlib import Path
from typing import List, Any
from evaluation.json_utils import parse_json_response
from writing.feedback import CriticFinding, CriticReport


NO_FINDINGS_MARKERS = (
    "no canon violations found",
    "no style issues found",
    "no flow issues found",
    "no issues found",
    "no violations found",
)

def build_critic_filename(role: str) -> str:
    """Gera nome do arquivo de crítica com a regra atual."""
    if role.endswith("_critic"):
        clean_name = role[:-7]
    else:
        clean_name = role
    return f"critique_{clean_name}.md"

def resolve_role_from_file(filename: str, critics_roles: List[str] = None) -> str:
    """Resolve o papel de agente correspondente a partir do nome de um arquivo de crítica."""
    if critics_roles is None:
        critics_roles = ["canon_critic", "style_critic", "flow_critic", "technical_editor"]

    for role in critics_roles:
        if filename == build_critic_filename(role):
            return role

    clean_name = filename
    if clean_name.startswith("critique_"):
        clean_name = clean_name[len("critique_"):]
    if clean_name.endswith(".md"):
        clean_name = clean_name[:-3]

    if clean_name in ["canon", "style", "flow"]:
        return f"{clean_name}_critic"
    return clean_name

def build_critic_prompt(critic_name: str, chapter_raw_text: str) -> str:
    """Monta o prompt de crítica preservando exatamente os blocos atuais."""
    return (
        f"Você é o {critic_name}.\n"
        f"Seu objetivo é analisar o seguinte rascunho bruto de capítulo e gerar um relatório de críticas detalhado.\n\n"
        f"RASCUNHO BRUTO DO CAPÍTULO:\n{chapter_raw_text}\n\n"
        f"Siga as suas instruções de persona e as regras do sistema."
    )

def run_critic_agents(
    tmp_dir: Path,
    critics_roles: List[str],
    chapter_raw_text: str,
    lore_data: str,
    slop_rules: str,
    factory: Any
) -> List[Path]:
    """Executa os críticos ativos sequencialmente e salva seus arquivos de relatório."""
    print("[DraftChaptersStep] Running active critic agents...")
    context_args = {
        "lore_data": lore_data,
        "slop_rules": slop_rules
    }
    created_files = []
    for role in critics_roles:
        filename = build_critic_filename(role)
        print(f"  Running {role}...")
        critic_agent = factory.get_agent(role, **context_args)
        critic_prompt = build_critic_prompt(critic_agent.name, chapter_raw_text)
        critique = critic_agent.execute(critic_prompt)
        
        file_path = tmp_dir / filename
        file_path.write_text(critique, encoding="utf-8")
        created_files.append(file_path)
    return created_files

def convert_critique_file_to_report(critique_file: Path, role: str) -> CriticReport:
    """Converte um arquivo de crítica existente em um CriticReport estruturado."""
    content = critique_file.read_text(encoding="utf-8")
    return convert_critique_text_to_report(content, role)


def convert_critique_text_to_report(content: str, role: str) -> CriticReport:
    """Converte texto bruto de crítica em achados estruturados sempre que possível."""
    normalized = content.strip()
    if not normalized:
        return CriticReport(critic_role=role, findings=[])

    if normalized.lower().rstrip(".") in NO_FINDINGS_MARKERS:
        return CriticReport(critic_role=role, findings=[])

    json_report = _convert_json_critique(normalized, role)
    if json_report is not None:
        return json_report

    markdown_findings = _convert_markdown_critique(normalized, role)
    if markdown_findings:
        return CriticReport(critic_role=role, findings=markdown_findings)

    finding = CriticFinding(
        source=role,
        instruction=normalized,
        quote="",
        severity="medium"
    )
    return CriticReport(
        critic_role=role,
        findings=[finding]
    )


def _convert_json_critique(content: str, role: str) -> CriticReport | None:
    if "{" not in content or "}" not in content:
        return None

    try:
        data = parse_json_response(content)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    findings_data = data.get("findings", [])
    if not isinstance(findings_data, list):
        return None

    findings = []
    for item in findings_data:
        if not isinstance(item, dict):
            continue
        instruction = item.get("instruction") or item.get("fix") or item.get("recommendation") or item.get("issue")
        if not instruction:
            continue
        findings.append(CriticFinding(
            source=item.get("source") or data.get("critic_role") or role,
            instruction=str(instruction).strip(),
            quote=str(item.get("quote", "")).strip(),
            severity=_normalize_severity(item.get("severity", "medium"))
        ))

    return CriticReport(
        critic_role=data.get("critic_role") or role,
        findings=findings
    )


def _convert_markdown_critique(content: str, role: str) -> List[CriticFinding]:
    findings = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith(("-", "*")):
            continue

        instruction = stripped.lstrip("-* ").strip()
        if not instruction:
            continue

        findings.append(CriticFinding(
            source=role,
            instruction=instruction,
            quote=_extract_first_quote(instruction),
            severity=_infer_markdown_severity(instruction)
        ))
    return findings


def _extract_first_quote(text: str) -> str:
    for quote_char in ('"', "'"):
        parts = text.split(quote_char)
        if len(parts) >= 3 and parts[1].strip():
            return parts[1].strip()
    return ""


def _infer_markdown_severity(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in ("critical", "grave", "major", "alta")):
        return "high"
    if any(marker in lowered for marker in ("minor", "baixo", "baixa", "low")):
        return "low"
    return "medium"


def _normalize_severity(severity: Any) -> str:
    normalized = str(severity).strip().lower()
    if normalized in {"low", "medium", "high", "critical"}:
        return normalized
    return "medium"
