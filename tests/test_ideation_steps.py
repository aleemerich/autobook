from pipelines.ideation_steps.selection import (
    parse_numbered_concepts,
    select_concept_text,
    default_mystery_template,
    build_initial_ideation_state
)

def test_parse_numbered_concepts_with_three_concepts() -> None:
    """Valida o parsing de 3 conceitos numerados no formato '1. ...'."""
    concepts_text = (
        "1. THE ECHO CHAMBER\n"
        "HOOK: In a city of silence, Cass discovers the noise of forgotten lives.\n"
        "WORLD: Rusted pipes, dripping water, copper towers.\n\n"
        "2. THE WEAVERS OF RUST\n"
        "HOOK: A girl who can sew metal must mend the decaying heart of a sleeping war engine.\n"
        "WORLD: Rusted landscape, constant ash rain.\n\n"
        "3. THE BIOTECH REVELATION\n"
        "HOOK: In an ocular society, a blind detective is given a cybernetic eye.\n"
        "WORLD: Neon lights, towering monoliths.\n"
    )
    concepts = parse_numbered_concepts(concepts_text)
    
    assert len(concepts) == 3
    assert "1" in concepts
    assert "2" in concepts
    assert "3" in concepts
    
    assert concepts["1"].startswith("1. THE ECHO CHAMBER")
    assert "WORLD: Rusted pipes" in concepts["1"]
    assert concepts["2"].startswith("2. THE WEAVERS OF RUST")
    assert "constant ash rain." in concepts["2"]
    assert concepts["3"].startswith("3. THE BIOTECH REVELATION")
    assert "neon lights" in concepts["3"].lower()

def test_select_concept_text_returns_selected() -> None:
    """Valida que select_concept_text retorna o conceito escolhido se presente."""
    concepts_text = (
        "1. THE ECHO CHAMBER\n"
        "HOOK: In a city of silence, Cass discovers the noise of forgotten lives.\n\n"
        "2. THE WEAVERS OF RUST\n"
        "HOOK: A girl who can sew metal must mend the decaying heart of a sleeping war engine.\n"
    )
    selected = select_concept_text(concepts_text, "2")
    assert selected.startswith("2. THE WEAVERS OF RUST")
    assert "THE ECHO CHAMBER" not in selected

def test_select_concept_text_fallback_on_parse_failure() -> None:
    """Valida que select_concept_text retorna o texto original completo se o parsing falhar ou nao achar a escolha."""
    # Caso 1: Texto sem número
    bad_text = "This is a concept with no numbers at all."
    selected = select_concept_text(bad_text, "1")
    assert selected == bad_text

    # Caso 2: Opção válida de escolha que não está no texto
    concepts_text = (
        "1. THE ECHO CHAMBER\n"
        "HOOK: In a city of silence, Cass discovers the noise of forgotten lives.\n"
    )
    selected_missing = select_concept_text(concepts_text, "3")
    assert selected_missing == concepts_text

def test_default_mystery_template() -> None:
    """Valida que o template default de misterio contem a tag e titulo corretos."""
    template = default_mystery_template()
    assert "# THE CENTRAL MYSTERY" in template
    assert "Author's Eyes Only" in template
    assert "Define the central secret" in template

def test_build_initial_ideation_state() -> None:
    """Valida que o estado inicial contem os campos e valores corretos."""
    state = build_initial_ideation_state()
    assert state == {
        "chapters_drafted": 0,
        "phase": "foundation",
        "current_focus": "planning"
    }
