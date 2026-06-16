# Agentes do Autobook

## Visão Geral do Sistema de Agentes

O sistema Autobook implementa uma arquitetura multi-agente onde cada agente especializado tem um papel específico no processo de criação literária. A infraestrutura moderna do sistema de agentes está localizada no pacote `agent_system/` (com suporte a registro dinâmico e lazy instantiation), definindo as especificações de papéis e encapsulando a criação de agentes que são implementados em `agents.py`.

Todos os agentes herdam da classe base `Agent` que encapsula a chamada ao modelo de linguagem (LLM) através do módulo `llm.py`. Os prompts de sistema de cada agente são carregados dinamicamente a partir de arquivos externos localizados em `prompts/{LANG}/agents/` (como `prompts/EN/agents/`).

## Classe Base: Agent

### Responsabilidade
Fornece uma interface comum para todos os agentes literários, encapsulando a interação com o LLM.

### Atributos
- `name`: Identificador do agente (ex: "DraftingAgent")
- `system_prompt`: Instruções de sistema que definem o papel e comportamento do agente
- `temperature`: Parâmetro de criatividade (0.0 a 1.0) passado ao LLM

### Métodos
- `execute(prompt: str) -> str`: Envia o prompt junto com o system_prompt e temperature ao LLM e retorna a resposta

### Tratamento de Erros
- Captura exceções durante a chamada ao LLM
- Logga erros no stderr antes de re lançá-los
- Garante que falhas na chamada ao LLM sejam visíveis para o pipeline

## Agentes Especializados

### 1. DraftingAgent
#### Papel
Responsável por escrever o rascunho inicial, estrutural de uma cena ou capítulo.

#### Características
- **Temperature**: 0.8 (mais criativo para geração inicial)
- **Foco**: Construção de narrativa estrutural, hitting beats específicos, setup da história raw
- **Restrição de Output**: RETORNAR APENAS o texto puro da cena - nenhum comentário, nota ou metadata
- **System Prompt Enfatiza**: 
  - Construir estrutura narrativa sólida
  - Escrever o texto completo da cena sem atalhos ou resumos
  - Formato crítico de saída: apenas prose da cena

#### Uso
Usado na primeira fase da geração de capítulo (modular beat generation ou escrita completa do capítulo)

### 2. StylistAgent
#### Papel
Responsável por refinar o rascunho, injetando ação específica do gênero, tone e cliffhangers.

#### Características
- **Temperature**: 0.7 (equilibrado entre criatividade e coerência)
- **Entrada Requerida**: `genre_rules` (regras específicas do gênero)
- **Foco**: Aplicar regras de gênero, pace, tensão e estilo; injetar ação física, diálogos dinâmicos, ganchos fortes
- **Restriction de Output**: APENAS o texto refinado da cena - nenhuma explicação, nota ou comentário
- **System Prompt Inclui**: 
  - Instruções de estilista de alta tensão especulativa
  - Regras específicas do gênero fornecidas dinamicamente
  - Restrição crítica de formato de saída

#### Uso
Usado após o rascunho inicial para aplicar estilo e aprimorar de acordo com o gênero especificado

### 3. TechnicalEditorAgent
#### Papel
Responsável por calibrar dados científicos, verificar lore e enforcar localização PT-BR.

#### Características
- **Temperature**: 0.3 (mais conservador para precisão técnica)
- **Entradas Requeridas**: 
  - `lore_data`: Referência completa de lore (mundo, cânone, personagens)
  - `slop_rules`: Regras anti-slop e restrições de estilo
- **Foco**: 
  1. **Consistência de Lore**: Verificar nomes, objetos, datas, locais contra dados de referência
  2. **Anti-Slop Guardrails**: Remover estruturas clichês de escrita AI e palavras proibidas
  3. **Localização de Dialeto**: Converter termos PT-PT para PT-BR formal
  4. **Integridade Tonal**: Manter POV, nível de tensão e convenções de gênero
- **Restriction de Output**: APENAS o texto final polido e localizado - nenhum relatório técnico, resumo ou explicação

#### System Prompt Enfatiza
- Precisão técnica e expertise em localização
- Aplicação rigorosa de quatro regras específicas
- Formato de saída crítica: apenas prose da história

#### Uso
Usado após o estilista para garantir consistência de lore, qualidade técnica e localização adequada

### 4. CanonCriticAgent
#### Papel
Responsável por auditar cenas de rascunho para conformidade com cânone, personagens e lore.

#### Características
- **Temperature**: 0.3 (focado em detecção precisa, não criatividade)
- **Entrada Requerida**: `lore_data` (dados de referência de lore)
- **Foco**: Auditar rascunho contra estabelecido lore, personagens e fatos do timeline
- **Output Format**: Lista markdown de violações específicas com texto citado e instruções de correção, ou "No canon violations found."
- **System Prompt Enfatiza**:
  - Verificar descrições de personagens, relacionamentos e fatos de backstory estabelecidos
  - Verificar detalhes de localização, timelines e descrições físicas
  - Não introduzir diagnóstico, evento ou detalhe que contradiga o cânone estabelecido
  - Flaggar qualquer contradição factual entre rascunho e dados de referência de lore

#### Uso
Usado como um dos agentes críticos na fase de crítica paralela da geração de capítulo

### 5. StyleCriticAgent
#### Papel
Responsável por auditar cenas de rascunho para conformidade de estilo, voz e compliance com slop.

#### Características
- **Temperature**: 0.3 (focado em detecção precisa)
- **Entrada Requerida**: `slop_rules` (regras de estilo e restrições anti-slop)
- **Foco**: Identificar clichês de AI, tics estilísticos, repetições de palavras, uso excessivo de em-dashes, violações show-vs-tell
- **Output Format**: Lista markdown de falhas estilísticas específicas com texto citado e sugestões de reescrita, ou "No style issues found."
- **System Prompt Inclui**:
  - Instruções de editor estilístico aguçado e crítico de voz
  - Regras específicas de estilo e slop fornecidas dinamicamente
  - Formato de saída crítica detalhada

#### Uso
Usado como um dos agentes críticos na fase de crítica paralela da geração de capítulo

### 6. FlowCriticAgent
#### Papel
Responsável por auditar fluxo de cena a cena, transições e pacing.

#### Características
- **Temperature**: 0.3 (focado em análise estrutural)
- **Entrada Requerida**: Nenhuma além da configuração padrão
- **Foco**: Analisar rascunho de capítulo para identificar problemas de pacing, estruturas de parágrafo monótonas e transições descontínuas entre beats
- **Output Format**: Lista markdown de problemas específicos de pacing/flow/transição com citações e propostas de melhoria, ou "No flow issues found."
- **System Prompt Enfatiza**:
  - Análise de estrutura de história e fluxo
  - Identificação de problemas de pacing
  - Detecção de estruturas de parágrafo monótonas
  - Análise de transições entre beats
  - Sugestões para tornar o fluxo narrativo mais orgânico

#### Uso
Usado como um dos agentes críticos na fase de crítica paralela da geração de capítulo

### 7. SynthesisAgent
#### Papel
Responsável por realizar correções alvo em um rascunho usando um arquivo de crítica específico.

#### Características
- **Temperature**: 0.3 (mais conservador para correções precisas)
- **Entrada Requerida**: Nenhuma além da configuração padrão
- **Foco**: Reescrever/reescrever o rascunho de capítulo focando exclusivamente na resolução dos problemas destacados em um Relato de Crítica específico
- **Restriction de Output**: APENAS o texto final corrigido do capítulo - nenhum preâmbulo, observação, lista de mudanças ou resposta conversacional
- **System Prompt Enfatiza**:
  - Reescrita de manuscrito de elite e mestre editor
  - Foco exclusivo na resolução dos problemas destacados no Relato de Crítica
  - Aplicação meticulosa de ajustes tecidos naturalmente na prosa
  - Manutenção de POV, tom e estilo definidos nos dados de referência
  - Restrição crítica de formato de saída: apenas prose corrigida

#### Uso
Usado na fase de síntese sequencial onde críticas são aplicadas uma após outra para refinar o rascunho

## AgentFactory

### Papel
Implementa o padrão **Singleton Factory** para registrar, criar e carregar agentes literários dinamicamente.

### Características
- **Singleton**: Garante apenas uma instância ao longo da aplicação
- **Registro Dinâmico**: Permite registro de novas classes de agente em tempo de execução
- **Carregamento de Habilidade**: Pode carregar agentes especializados definidos via configuração de habilidade (scripts em `skills/`)
- **Fallbacks Padrão**: Fornece classes padrão para todos os tipos de agente se não registrado dinamicamente

### Métodos Principais
- `register_agent(role: str, agent_class)`: Registra uma nova classe de agente para um papel específico
- `get_agent(role: str, **kwargs) -> Agent`: Cria e retorna uma instância de agente baseada no papel e argumentos
- `load_skill_agent(skill_name: str, **kwargs) -> Agent`: Carrega dinamicamente um agente definido por um script de habilidade

### Lógica de Criação
Para um dado papel, o factory:
1. Verifica se o papel está registrado dinamicamente (de habilidades)
2. Se não, usa classes padrão hardcoded para papéis conhecidos:
   - drafting → DraftingAgent
   - stylist → StylistAgent
   - technical_editor → TechnicalEditorAgent
   - canon_critic → CanonCriticAgent
   - style_critic → StyleCriticAgent
   - flow_critic → FlowCriticAgent
   - synthesis → SynthesisAgent
3. Lança ValueError se o papel não estiver registrado e não tiver classe padrão

### Carregamento de Habilidade
- Procura por `{skill_name}.py` no diretório `skills/`
- Importa dinamicamente o módulo
- Espera que o módulo tenha uma função `register(factory)` para registrar agentes
- Usa `ROLE_NAME` do módulo ou nome da habilidade como papel
- Retorna instância do agente registrado

## Integração com o Pipeline

### Como os Agentes são Usados
1. **Pipelines** criam uma instância de `AgentFactory`
2. Para cada tipo de agente necessário, chamam `factory.get_agent(role, **specific_args)`
3. O agente retornado é então usado para executar prompts específicos via `agent.execute(prompt)`

### Exemplos de Uso nos Pipelines

#### No book_generation.py
```python
factory = AgentFactory()
drafting_agent = factory.get_agent("drafting")
```

#### Na fase de crítica
```python
for role in self.critics_roles:
    context_args = {"lore_data": lore_data, "slop_rules": slop_rules}
    critic_agent = factory.get_agent(role, **context_args)
    critique = critic_agent.execute(critic_prompt)
```

#### Na fase de síntese
```python
synthesis_agent = factory.get_agent("synthesis")
current_text = synthesis_agent.execute(synth_prompt)
```

## Pontos de Melhoria e Antipadrões

### Antipadrões Atuais
1. **Fallbacks Hardcoded na Factory**: A classe AgentFactory contém fallbacks hardcoded para tipos de agente, o que dificulta a extensão pura através de registro
2. **Estado Global de Registro**: Embora use singleton, o registro de agentes ainda é estado mutável global
3. **Duplicação de Lógica de Instanciação**: Similaridade entre o método `get_agent` e o registro dinâmico de habilidades

### Sugestões de Refatoramento
1. **Separar Registro e Criação**: Dividir AgentFactory em registro puro (mantém dicionário de mapeamento) e criador (usa o registro para instanciar)
2. **Configuração Explícita de Fallbacks**: Em vez de fallbacks hardcoded, ter um objeto de configuração separado que pode ser injetado
3. **Interface de Agente Mais Rica**: Considerar métodos adicionais na classe base Agent para diferentes tipos de interação com LLM (streaming, batch processing, etc.)
4. **Padronização de Tratamento de Erros**: Criar exceções customizadas para falhas de agente específicas

### Boas Práticas Presentes
1. **Single Responsibility Principle**: Cada agente tem um papel bem definido e focado
2. **Open/Closed Principle**: Fácil estender com novos tipos de agente através de registro ou habilidades
3. **Liskov Substitution Principle**: Todos os agentes podem ser usados intercambiavelmente onde um Agent é esperado
4. **Interface Segregation**: Interface simples e focada na classe base Agent
5. **Dependency Injection**: Dependências (dados de lore, regras, etc.) são injetadas através de construtores ou métodos de factory
6. **Uso de Padrões de Projeto Apropriados**: Factory Method para criação de agentes, Singleton para gerenciamento de fábrica

## Exemplos de Prompts de Sistema

### DraftingAgent System Prompt
```
You are an elite novelist drafting the raw, foundational scenes of a chapter.
Your focus is on building solid narrative structure, hitting the specific planned beat,
and setting up the raw story. Write the FULL text of the scene without shortcuts or summaries.

CRITICAL OUTPUT FORMAT CONSTRAINT:
Return ONLY the raw prose of the draft scene. Do NOT include any intro/outro comments,
notes, headers, or metadata. Output the story text and nothing else.
```

### StylistAgent System Prompt (exemplo)
```
You are a master stylist and editor of high-tension speculative fiction.
Your task is to take a raw chapter draft and rewrite it to apply the specific
genre, pace, tension, and style rules below. Inject physical action, dynamic dialogues,
and strong hooks.

CRITICAL OUTPUT FORMAT CONSTRAINT:
Return ONLY the refined prose of the scene. Do NOT include any explanations, notes,
preambles, or markdown commentary. Your output must consist strictly of the revised story text.

GENRE SPECIFIC RULES:
[regras de gênero específicas vão aqui]
```

### TechnicalEditorAgent System Prompt (exemplo)
```
You are a meticulous technical editor and localization expert.
Your sole focus is to review the chapter text and refine it for absolute consistency
with the world lore, scientific facts, and language guidelines.

Apply the following rules strictly:
1. LORE CONSISTENCY: Ensure all names, objects, dates, and locations match the lore reference data provided below.
2. ANTI-SLOP GUARDRAILS: Strip any clichéd AI writing structures or forbidden words.
3. DIALECT LOCALIZATION: Translate any residual European Portuguese (PT-PT) terms into natural, formal Brazilian Portuguese (PT-BR).
4. TONAL INTEGRITY: Maintain the POV, tension level, and genre conventions defined in the lore reference and voice profile data.

CRITICAL OUTPUT FORMAT CONSTRAINT:
Return ONLY the final, polished, and localized prose of the scene.
Do NOT include any technical review reports, summary of edits, preambles, remarks, or explanations.
Your response must be 100% pure story prose.

LORE REFERENCE DATA:
[dados de lore vão aqui]

ANTI-SLOP & STYLE CONSTRAINTS:
[regras de anti-slop e estilo vão aqui]
```

## Conclusão

O sistema de agentes do Autobook demonstra uma aplicação bem pensada da arquitetura multi-agente para geração de literatura criativa. Cada agente tem um papel especializado e claramente definido, trabalhando em conjunto através de um processo de geração em cascata e crítica iterativa para produzir texto de alta qualidade que aderência tanto aos requisitos criativos quanto técnicos.

O uso do padrão Factory através do AgentFactory proporciona excelente extensibilidade, permitindo que novos tipos de agente sejam adicionados através de registro dinâmico ou carregamento de habilidade sem modificar o código núcleo.