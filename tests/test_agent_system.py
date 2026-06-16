import pytest
from agent_system import (
    list_roles,
    get_role_spec,
    create_agent,
    AgentFactory,
    AgentSpec
)

def test_registry_lists_all_roles() -> None:
    """Valida que o registry lista todos os 7 papéis padrão definidos."""
    expected_roles = {
        "drafting",
        "stylist",
        "technical_editor",
        "canon_critic",
        "style_critic",
        "flow_critic",
        "synthesis"
    }
    roles = list_roles()
    assert set(roles) == expected_roles
    assert len(roles) == 7

def test_registry_get_role_spec() -> None:
    """Valida a recuperação de especificações para papéis válidos."""
    spec = get_role_spec("drafting")
    assert isinstance(spec, AgentSpec)
    assert spec.role == "drafting"
    assert spec.class_name == "DraftingAgent"
    assert "rascunho" in spec.description

def test_registry_raises_value_error_for_unknown_role() -> None:
    """Valida que o registry levanta ValueError para papéis desconhecidos."""
    with pytest.raises(ValueError) as excinfo:
        get_role_spec("narrator")
    assert "Papel de agente desconhecido" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        get_role_spec("")
    assert "não pode ser vazio" in str(excinfo.value)

def test_factory_creates_agents_without_executing() -> None:
    """Valida a instanciação de todos os agentes sem realizar chamadas de LLM."""
    for role in list_roles():
        agent = create_agent(role)
        assert agent is not None
        assert agent.name in (
            "DraftingAgent",
            "StylistAgent",
            "TechnicalEditorAgent",
            "CanonCriticAgent",
            "StyleCriticAgent",
            "FlowCriticAgent",
            "SynthesisAgent"
        )

def test_factory_agent_kwargs() -> None:
    """Valida que os kwargs são passados e configurados corretamente."""
    # Test DraftingAgent
    drafting_agent = create_agent("drafting", temperature=0.9)
    assert drafting_agent.temperature == 0.9

    # Test StylistAgent
    stylist_agent = create_agent("stylist", genre_rules="Suspense", temperature=0.6)
    assert stylist_agent.temperature == 0.6
    assert "Suspense" in stylist_agent.system_prompt

    # Test TechnicalEditorAgent
    tech_agent = create_agent("technical_editor", lore_data="Lore XYZ", slop_rules="No slop")
    assert "Lore XYZ" in tech_agent.system_prompt
    assert "No slop" in tech_agent.system_prompt

def test_agent_factory_class_compatibility() -> None:
    """Valida a compatibilidade da nova classe AgentFactory com o padrão get_agent."""
    factory = AgentFactory()
    agent = factory.get_agent("flow_critic", temperature=0.45)
    assert agent is not None
    assert agent.name == "FlowCriticAgent"
    assert agent.temperature == 0.45

def test_legacy_factory_imports_continue_working() -> None:
    """Valida que a importação e instanciamento da fábrica antiga continuam funcionando."""
    from agents import AgentFactory as LegacyFactory
    legacy_factory = LegacyFactory()
    agent = legacy_factory.get_agent("synthesis", temperature=0.25)
    assert agent is not None
    assert agent.name == "SynthesisAgent"
    assert agent.temperature == 0.25

def test_factory_register_custom_agent() -> None:
    """Valida que register_agent e get_agent funcionam com agentes customizados e restaura o estado original."""
    import agents
    factory = AgentFactory()
    legacy_factory = agents.AgentFactory()

    # Salva o estado do registry original
    original_registry = legacy_factory._agents_registry.copy()

    # Cria uma classe fake para teste
    class CustomFakeAgent:
        def __init__(self, name="CustomFake", temperature=0.7, **kwargs):
            self.name = name
            self.temperature = temperature
            self.kwargs = kwargs

    try:
        # Registra o agente customizado
        factory.register_agent("custom_test_role", CustomFakeAgent)

        # Instancia o agente customizado
        agent = factory.get_agent("custom_test_role", temperature=0.85, extra_arg="val")

        assert isinstance(agent, CustomFakeAgent)
        assert agent.name == "CustomFake"
        assert agent.temperature == 0.85
        assert agent.kwargs == {"extra_arg": "val"}
    finally:
        # Restaura o estado original do registry
        legacy_factory._agents_registry = original_registry

    # Assegura que o papel customizado não permaneceu registrado
    assert "custom_test_role" not in legacy_factory._agents_registry

def test_factory_load_skill_agent(monkeypatch) -> None:
    """Valida que load_skill_agent delega corretamente para a fábrica legada."""
    import agents
    factory = AgentFactory()

    called_args = []
    def mock_load_skill_agent(self, skill_name, **kwargs):
        called_args.append((skill_name, kwargs))
        return "mock_agent_instance"

    monkeypatch.setattr(agents.AgentFactory, "load_skill_agent", mock_load_skill_agent)

    agent = factory.load_skill_agent("my_skill", temp=0.5)

    assert agent == "mock_agent_instance"
    assert called_args == [("my_skill", {"temp": 0.5})]

def test_create_agent_validation_and_value_error() -> None:
    """Valida que create_agent e get_agent continuam levantando ValueError para papéis desconhecidos."""
    factory = AgentFactory()

    with pytest.raises(ValueError) as excinfo:
        create_agent("unknown_role_xyz")
    assert "Papel de agente desconhecido" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        factory.get_agent("another_unknown_role")
    assert "Papel de agente desconhecido" in str(excinfo.value)
