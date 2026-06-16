# 04 - Agent Registry and Factory Spec

## Objetivo
Especificar a organização do sistema de agentes do Autobook, estruturando a criação de um novo pacote `agent_system/` contendo uma classe base estável, um registro dinâmico de papéis e uma fábrica de agentes, mantendo a plena retrocompatibilidade com o módulo original `agents.py`.

## Fora De Escopo
- Mover todos os prompts ou agentes para o novo pacote em uma única etapa rápida.
- Excluir ou remover o arquivo `agents.py` existente na raiz do projeto.
- Alterar a lógica narrativa ou de escrita dos agentes reais no fluxo do livro.

## Estado Atual
Atualmente, o arquivo `agents.py` localizado na raiz do projeto concentra tanto a definição das classes de agentes (ex: `DraftingAgent`, `StylistAgent`, `SynthesisAgent`, etc.) quanto o método de fábrica `AgentFactory`. Essa mistura dificulta a extensibilidade do sistema, o roteamento dinâmico e o desacoplamento de prompts.

## Decisão de Nomenclatura e Imports (Evitando Conflitos)
Devido às particularidades de resolução de imports do Python, a criação de uma pasta com o nome `agents/` na raiz causaria sérios conflitos e ambiguidades enquanto o arquivo `agents.py` ainda existir. 
- **Decisão Arquitetural:** Fica decido e fechado que a nova estrutura deve ser construída sob o pacote denominado **`agent_system/`** (nunca `agents/`).
- **Preservação de `agents.py`:** O arquivo `agents.py` na raiz **não será removido nem deprecado nesta fase**. Ele continuará ativo, servindo como proxy ou ponto de importação compatível.
- **Plano de Remoção Futura:** A depreciação e eventual remoção de `agents.py` constitui uma preocupação de longo prazo e **deve ser tratada em uma fase dedicada futura** (`fase-06x-deprecate-agents-py.md`), detalhada somente após o Gate A e após o pacote `agent_system/` estar 100% estável, testado e com todos os imports de pipelines e ferramentas migrados de forma limpa.

## Comportamento Desejado
- **Criação do Pacote `agent_system/`:**
  - `agent_system/base.py`: Classe base comum para agentes, definindo assinaturas de métodos de chamada comuns de forma modular.
  - `agent_system/registry.py`: Registro centralizado de papéis (ex: `ScenePlanner`, `DraftWriter`, `StyleKeeper`, `ContinuityArchitect`).
  - `agent_system/factory.py`: Fábrica que instancia os agentes associados a um papel, com formato de entrada/saída estruturado.
- **Manutenção de Retrocompatibilidade:** Garantir que imports de código legados (como `from agents import AgentFactory`) continuem funcionando normalmente sem quebra.

## Arquivos Afetados Futuramente
- `agents.py` (ajuste para redirecionar ou manter compatibilidade)
- [NEW] `agent_system/__init__.py`
- [NEW] `agent_system/base.py`
- [NEW] `agent_system/registry.py`
- [NEW] `agent_system/factory.py`
- [NEW] `tests/test_agents_registry.py`

## Contratos De Entrada
- Solicitação de agente à fábrica por meio de strings de papéis.

## Contratos De Saida
- Instância do agente configurado.

## Testes Necessarios
1. **Registro e Listagem:** Testar que novos papéis de agentes podem ser devidamente registrados e listados dinamicamente via registry.
2. **Instanciação pela Fábrica:** Testar que a fábrica cria corretamente instâncias de agentes baseados em papéis estáveis.
3. **Erros de Papéis Inexistentes:** Validar que requisições de papéis inválidos ou não mapeados disparam exceções claras.
4. **Compatibilidade de Imports:** Validar que os testes antigos de `tests/` que importam de `agents.py` continuam executando com sucesso.

## Criterios De Aceite
- Sem conflitos de imports Python na árvore do projeto.
- Testes antigos passam sem quebras.
- Registro centralizado implementado de forma extensível e limpa.

## Perguntas Abertas
- Como deve ser a assinatura de passagem de contexto do LLM client para os agentes sob `agent_system`?
