# Arquitetura do Projeto Autobook

## Visão Geral

O Autobook é um sistema multi-agente projetado para auxiliar na criação de livros usando Inteligência Artificial. Ele implementa uma arquitetura modular baseada no padrão **Command/Composite** para orquestrar pipelines de geração de conteúdo, com agentes especializados que colaboram para produzir, revisar e aprimorar texto literário.

> **Status v0:** a arquitetura modular descrita aqui esta correta em linhas
> gerais. Os prompts operacionais principais foram neutralizados para nao ficarem
> presos a uma obra especifica, mas ainda ha caminhos historicos, scripts legacy
> e automacoes parciais; veja `../SNAPSHOT_V0.md` para o inventario atualizado.

## Padrões Arquiteturais

### 1. Padrão Command/Composite
O sistema utiliza o padrão **Composite** para tratar pipelines individuais e sequências de steps de forma uniforme. Cada pipeline é composto por steps que implementam uma interface comum.

- **Component**: Classe abstrata `Step` que define a interface para executar uma etapa.
- **Composite**: Classe `Pipeline` que contém uma lista de steps e implementa a mesma interface, permitindo que pipelines sejam tratados como steps individuais.
- **Leaf**: Classes concretas de steps que implementam operações específicas.

### 2. Factory Pattern
A classe `AgentFactory` implementa o padrão **Factory Method** para criar instâncias de agentes dinamicamente com base em seu papel (role).

### 3. Strategy Pattern
Os agentes utilizam diferentes estratégias de chamada para LLMs baseado no provedor configurado (Anthropic, OpenAI, Gemini, OpenRouter), encapsulado no módulo `llm.py`.

### 4. Dependency Injection
Dependências são injetadas através de construtores, principalmente nos agentes que recebem dados de lore, regras de estilo e outros parâmetros de configuração.

## Componentes Principais

### 1. Módulo `run.py`
Orquestrador principal que:
- Configura logging e captura de saída
- Processa argumentos de linha de comando
- Instancia e executa o pipeline selecionado
- Gerencia o contexto de execução

### 2. Pacote `agent_system` e Módulo `agents.py`
Contém:
- A infraestrutura moderna do sistema de agentes sob o pacote `agent_system/`, incluindo a especificação contratual (`BaseAgent`), especificação de papéis (`AgentSpec`), o registro central de papéis e a classe factory wrapper (`AgentFactory`) com lazy instantiation.
- As implementações concretas das classes de agentes especializados localizadas em `agents.py`:
  - `DraftingAgent`: Escreve o rascunho inicial
  - `StylistAgent`: Aplica regras de gênero e estilo
  - `TechnicalEditorAgent`: Verifica consistência, lore e localização
  - `CanonCriticAgent`: Audita compliance com cânone
  - `StyleCriticAgent`: Identifica problemas de estilo e slop
  - `FlowCriticAgent`: Analisa fluxo e transições
  - `SynthesisAgent`: Aplica correções baseado em críticas

### 3. Módulo `llm.py`
Cliente unificado para LLMs que:
- Suporta múltiplos provedores (Anthropic, OpenAI, Gemini, OpenRouter)
- Gerencia chaves de API, URLs e modelos
- Implementa retry com backoff exponencial
- Seleciona modelos baseado no tipo de operação (writing, judge, review)
- Levanta exceções tipadas para erros de configuração antes de chamar provedores externos

### 4. Módulo `workspace/git.py`
Adaptador central para operações Git que:
- Encapsula `git add`, `git commit`, `git push`, leitura de branch e status do worktree
- Usa erro tipado (`GitCommandError`) para falhas de comandos Git
- Mantém os testes desacoplados de chamadas diretas a `subprocess.run`

### 5. Módulo `pipelines/base.py`
Define as classes base:
- `Step`: Interface para etapas atômicas
- `Pipeline`: Implementação composite para sequências de steps

### 6. Pipelines Específicos
Localizados em `/pipelines/`:
- `registry.py`: Centraliza as especificações e o registro das pipelines.
- `ideation.py`: Geração de ideias e conceitos.
- `foundation.py`: Criação de fundação (personagens, mundo, outline).
- `book_generation.py`: Geração completa do livro.
- `editorial_revision.py`: Processo de revisão editorial.
- **Subpacotes de Steps** (`*_steps/`): Funções auxiliares puras e montagem de contexto específicas de cada pipeline separadas em subpacotes dedicados sob `pipelines/` (ex: `book_generation_steps/`, `foundation_steps/`, `ideation_steps/`, `editorial_revision_steps/`).

### 7. Sistema de Prompts
Localizado em `/prompts/` com subpastas para cada idioma (PT-BR, EN):
- Arquivos `.txt` e subpastas de agentes (`prompts/{LANG}/agents/`): Contêm os prompts de sistema de cada agente carregados dinamicamente no construtor.
- Arquivos `.json`: Configurações estruturadas (continuity, editorial, slop).

### 8. Módulo `prompt_loader.py`
Responsável por:
- Carregar prompts baseado no idioma ativo
- Fornecer fallbacks para inglês quando necessário
- Gerenciar diretivas de idioma

### 9. Módulo `book_data/`
Armazena o estado do projeto em execução:
- `state.json`: Estado atual do pipeline
- Arquivos Markdown com informações do livro (personagens, mundo, cânone, etc.)

## Fluxo de Dados

1. **Inicialização**: `run.py` processa argumentos e cria o pipeline apropriado
2. **Execução do Pipeline**: Cada step no pipeline é executado sequencialmente
3. **Interação com Agentes**: Steps que requerem geração de texto utilizam o `AgentFactory` para criar agentes especializados
4. **Chamada ao LLM**: Agentes utilizam `llm.call_llm()` para obter respostas do modelo de linguagem
5. **Atualização de Estado**: Informações são salvas em `book_data/` para uso em steps subsequentes
6. **Ciclo de Revisão**: Para geração de livro, há ciclos de rascunho → crítica → síntese

## Injeção de Dependência

O sistema demonstra injeção de dependência principalmente através:

1. **AgentFactory**: Recebe instâncias registradas dinamicamente
2. **Construtores de Agentes**: Recebem dados de lore, regras de estilo e parâmetros de temperatura
3. **Configuração de Provedor**: O módulo `llm.py` lê variáveis de ambiente para configurar o provedor ativo

## Pontos de Melhoria e Antipadrões Identificados

### Antipadrões Atuais:
1. **Hardcoded Caminhos**: Alguns caminhos são construídos usando caminhos absolutos ou relativos hardcoded
2. **Mistura de Responsabilidades**: A classe `AgentFactory` contém tanto lógica de factory quanto fallback hardcoded para tipos de agentes
3. **Estado Global**: Uso de variáveis de ambiente para configuração pode tornar testes mais difíceis
4. **Duplicação de Lógica**: Similaridade na criação de agentes entre o método `get_agent` e o registro dinâmico

### Sugestões de Refatoramento:
1. **Extrair Interface de Configuração**: Criar um objeto de configuração explícito em vez de depender diretamente de `os.environ`
2. **Separar Responsabilidades da Factory**: Dividir `AgentFactory` em registro puro e criação, movendo fallbacks para um local separado
3. **Utilizar Injeção de Dependência Mais Explícita**: Passar dependências de forma mais explícita através de construtores ou setters
4. **Padronizar Tratamento de Erros**: Criar exceções customizadas para diferentes camadas do sistema

### Boas Práticas Presentes:
1. **Separation of Concerns**: Cada módulo tem uma responsabilidade bem definida
2. **Padrões de Projeto Apropriados**: Uso correto de Composite, Factory e Strategy
3. **Encapsulamento**: Detalhes de implementação são escondidos atrás de interfaces bem definidas
4. **Extensibilidade**: Fácil adicionar novos agentes, pipelines ou provedores de LLM
5. **Testabilidade**: Estrutura modular facilita o teste de unidades individuais

## Diagrama de Componentes (Textual)

```
+----------------+       +------------------+       +---------------------+
|    run.py      | ----> |   Pipeline Base  | ----> |    Step Implement   |
+----------------+       +------------------+       +---------------------+
        |                          |
        V                          V
+------------------+       +---------------------+
|  Agent Factory   |       |      LLM Client     |
+------------------+       +---------------------+
        |                          |
        V                          V
+------------------+       +---------------------+
|   Agentes       | <----> |   Prompt Loader     |
| (Drafting,      |       |   (IDIOMAS,         |
|  Stylist, etc.) |       |   DIRETIVAS)        |
+------------------+       +---------------------+
        |
        V
+------------------+
|   book_data/     |
| (State, Lore,   |
|  Characters, etc)|
+------------------+
```

## Conclusão

A arquitetura do Autobook demonstra uma boa aplicação de princípios de design de software, particularmente:
- Modularidade clara
- Uso apropriado de padrões de projeto
- Separação de responsabilidades
- Extensibilidade para novos recursos e provedores de LLM

O foco em agentes literários especializados cria um sistema poderoso para geração de texto criativo mantendo a qualidade através de ciclos de revisão especializados.
