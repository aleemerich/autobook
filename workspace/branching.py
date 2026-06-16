import re
import subprocess
import unicodedata

def slugify_work_title(title: str) -> str:
    """Converte o título da obra em um slug ASCII seguro para Git branch."""
    # Normalize unicode to decompose accents (e.g. 'ã' -> 'a' + '~')
    nfkd_form = unicodedata.normalize('NFKD', title)
    # Filter out non-ASCII combining characters
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')
    # Lowercase
    lowered = only_ascii.lower()
    # Replace non-alphanumeric characters with hyphens
    sanitized = re.sub(r'[^a-z0-9]+', '-', lowered)
    # Strip leading/trailing hyphens
    return sanitized.strip('-')

def book_branch_name(title_or_slug: str) -> str:
    """Gera o nome de branch padrão no formato autobook/<slug>."""
    slug_candidate = title_or_slug
    if slug_candidate.startswith("autobook/"):
        slug_candidate = slug_candidate[len("autobook/"):]
    slug = slugify_work_title(slug_candidate)
    return f"autobook/{slug}"

def is_main_branch(branch: str) -> bool:
    """Verifica se a branch informada corresponde a uma branch principal (main ou master)."""
    return branch.strip() in ("main", "master")

def current_branch() -> str:
    """Retorna o nome da branch Git ativa de forma puramente de leitura."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        raise RuntimeError(f"Erro ao ler a branch Git ativa: {e}")

def ensure_not_main_for_generation(branch: str | None = None) -> None:
    """Garante que a branch (informada ou atual) não seja principal, levantando exceção caso contrário."""
    target_branch = branch if branch is not None else current_branch()
    if is_main_branch(target_branch):
        raise ValueError(
            f"Erro: A branch ativa '{target_branch}' é a branch principal do projeto. "
            "A geração de livros deve ocorrer estritamente em uma branch dedicada (ex: autobook/<slug>) "
            "para manter a branch principal limpa de artefatos."
        )
