from pathlib import Path
from typing import List, Any, Tuple
from writing.feedback import RevisionPlan
from pipelines.book_generation_steps.critique import (
    build_critic_filename,
    convert_critique_file_to_report,
    resolve_role_from_file,
)

def list_critique_files(tmp_dir: Path, critics_roles: List[str] = None) -> List[Path]:
    """Lista os arquivos critique_*.md na ordem configurada dos criticos, com fallback alfabetico."""
    critique_files = sorted(list(tmp_dir.glob("critique_*.md")))
    if not critics_roles:
        return critique_files

    by_name = {path.name: path for path in critique_files}
    ordered_files = []
    seen_names = set()

    for role in critics_roles:
        filename = build_critic_filename(role)
        if filename in by_name:
            ordered_files.append(by_name[filename])
            seen_names.add(filename)

    ordered_files.extend(path for path in critique_files if path.name not in seen_names)
    return ordered_files

def build_revision_plan(critique_files: List[Path], critics_roles: List[str] = None) -> RevisionPlan:
    """Cria o RevisionPlan consolidado a partir dos arquivos de crítica usando convert_critique_file_to_report."""
    reports = []
    for f in critique_files:
        role = resolve_role_from_file(f.name, critics_roles=critics_roles)
        reports.append(convert_critique_file_to_report(f, role))
    return RevisionPlan.consolidate(reports)

def build_synthesis_prompt(critic_name: str, chapter_text: str, critique_content: str) -> str:
    """Monta o prompt de síntese preservando os blocos atuais."""
    return (
        f"Você é o SynthesisAgent. Seu objetivo é revisar e reescrever o texto do capítulo "
        f"com base estritamente no Relatório de Crítica a seguir.\n\n"
        f"TEXTO DO CAPÍTULO:\n{chapter_text}\n\n"
        f"RELATÓRIO DE CRÍTICA APLICADA ({critic_name}):\n{critique_content}\n\n"
        f"Instruções cruciais:\n"
        f"- Resolva todos os problemas listados no Relatório de Crítica de forma integrada, fluida e sutil.\n"
        f"- Certifique-se de que a resposta final contenha APENAS o texto completo da prosa do capítulo.\n"
        f"- Absolutamente nenhuma análise, nota, cabeçalho explicativo, ou comentário adicional deve estar no resultado."
    )

def run_sequential_synthesis(
    tmp_dir: Path,
    chapter_raw_text: str,
    factory: Any,
    critics_roles: List[str] = None
) -> Tuple[str, RevisionPlan]:
    """Executa a síntese sequencial aplicando as críticas uma a uma ao capítulo bruto."""
    print("[DraftChaptersStep] Starting sequential synthesis...")
    critique_files = list_critique_files(tmp_dir, critics_roles=critics_roles)
    print(f"  Found {len(critique_files)} critique files to apply sequentially: {[f.name for f in critique_files]}")
    
    plan = build_revision_plan(critique_files, critics_roles=critics_roles)
    
    current_text = chapter_raw_text
    if not critique_files:
        return current_text, plan
        
    synthesis_agent = factory.get_agent("synthesis")
    for idx, crit_file in enumerate(critique_files, 1):
        crit_name = crit_file.name
        print(f"  [Synthesis Step {idx}/{len(critique_files)}] Applying critique: {crit_name}...")
        critique_content = crit_file.read_text(encoding="utf-8")
        
        synth_prompt = build_synthesis_prompt(crit_name, current_text, critique_content)
        current_text = synthesis_agent.execute(synth_prompt)
        
        (tmp_dir / f"chapter_step_{idx:02d}_{crit_name}").write_text(current_text, encoding="utf-8")
        
    return current_text, plan
