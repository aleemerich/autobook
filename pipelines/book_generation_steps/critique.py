from pathlib import Path
from typing import List, Any
from writing.feedback import CriticFinding, CriticReport

def build_critic_filename(role: str) -> str:
    """Gera nome do arquivo de crítica com a regra atual."""
    clean_name = role.replace("_critic", "")
    return f"critique_{clean_name}.md"

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
    """Converte um arquivo de crítica existente em um CriticReport simples."""
    content = critique_file.read_text(encoding="utf-8")
    finding = CriticFinding(
        source=role,
        instruction=content,
        quote="",
        severity="medium"
    )
    return CriticReport(
        critic_role=role,
        findings=[finding]
    )
