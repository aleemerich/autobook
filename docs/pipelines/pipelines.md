# Pipelines do Autobook

## Visão Geral dos Pipelines

O sistema Autobook implementa quatro pipelines principais que cobrem todo o ciclo de vida da criação de um livro:
1. **Ideation** - Geração e seleção de conceitos iniciais
2. **Foundation** - Criação das bibilografias de mundo, personagens, outline e cânone
3. **Book Generation** - Escrita sequencial dos capítulos com revisão em cascata
4. **Editorial Revision** - Revisão baseada em feedback editorial e avaliação automática

Cada pipeline segue o padrão **Command/Composite** onde steps individuais são combinados em pipelines que podem ser tratados como steps em pipelines maiores.

## 1. Pipeline de Ideação (`pipelines/ideation.py`)

### Objetivo
Permite geração interativa de conceitos de romances através de questionário e seleção, produzindo o arquivo `seed.txt` e opcionalmente `MYSTERY.md`.

### Steps
1. **BypassOrRunStep** - Verifica se `seed.txt` já existe e oferece opção de pular a ideação
2. **QuestionnaireStep** - Coleta preferências do usuário (gênero, centelha criativa, custo, protagonista)
3. **GenerateConceptsStep** - Solicita 3 conceitos diversos ao LLM baseado nas respostas do questionário
4. **SelectConceptStep** - Permite seleção de um dos conceitos gerados ou entrada customizada
5. **MysteryGeneratorStep** - Opcionalmente gera `MYSTERY.md` com o mistério central
6. **UpdateStateStep** - Inicializa `state.json` para rastrear o progresso

### Fluxo de Dados
- **Entrada**: Respostas do questionário do usuário
- **Processo**: Geração de conceitos via LLM → Seleção → Geração opcional de mistério
- **Saída**: `seed.txt` (conceito selecionado), `MYSTERY.md` (opcional), `state.json`

### Características Técnicas
- Uso de expressões regulares para parsing de conceitos gerados
- Tratamento de interrupção graceful quando usuário opta por pular
- Separação clara entre geração de ideias e seleção humana

## 2. Pipeline de Fundação (`pipelines/foundation.py`)

### Objetivo
Gera as documentações fundamentais do livro a partir do `seed.txt`: mundo, personagens, outline e cânone.

### Pré-requisitos
- Arquivo `seed.txt` deve existir (produzido pelo pipeline de ideação)

### Steps
1. **VerifySeedStep** - Confirma existência de `seed.txt`
2. **GenerateWorldStep** - Cria `world.md` (World Bible)
3. **GenerateCharactersStep** - Cria `characters.md` (Character Registry)
4. **GenerateOutlineStep** - Cria `outline.md` (Chapter Outline & Beats)
5. **GenerateCanonStep** - Cria `canon.md` (Canon Fact Database)
6. **CommitFoundationStep** - Commit dos arquivos no Git e atualiza estado

### Detalhes de Implementação

#### GenerateWorldStep
- Constrói uma world bible específica usando regras de Sanderson (hard rules com custos)
- Inclui seções de cosmologia, magia, geografia, facções, bestiaria, cultura
- Enfatiza especificidade e interconexão entre elementos

#### GenerateCharactersStep
- Implementa framework de personagem abrangente:
  - Three Sliders (Sanderson): proatividade, likabilidade, competência
  - Wound/Want/Need/Lie framework
  - Dialogue Distinctiveness (8 dimensões)
  - Registro detalhado para personagens principais e secundários

#### GenerateOutlineStep
- Cria outline de 22 capítulos (~70,000 palavras total)
- Usa estrutura de três atos com porcentagens específicas
- Inclui foreshadowing ledger com rastreamento de threads
- Define beats específicos por capítulo (try-fail cycles, emotional arcs)

#### GenerateCanonStep
- Extrai fatos hardcoded das documentações de planejamento
- Formata como banco de dados verificável com fontes atribuídas
- Evita invenção de fatos - apenas registra o que está explicitamente declarado

### Fluxo de Dados
- **Entrada**: `seed.txt`, opcionalmente `MYSTERY.md`, `voice.md`, `CRAFT.md`
- **Processo**: Extração de informações → Geração sequencial de documentações
- **Saída**: `world.md`, `characters.md`, `outline.md`, `canon.md`, commit Git

## 3. Pipeline de Geração do Livro (`pipelines/book_generation.py`)

### Objetivo
Escreve os capítulos do livro sequencialmente usando agentes especializados em cascata: drafting → stylist → technical editor → críticos → síntese.

### Pré-requisitos
- Documentos de fundação devem existir (`world.md`, `characters.md`, `outline.md`, `canon.md`)

### Steps
1. **ResetStep** - Opcionalmente limpa arquivos de capítulo se `--from-scratch` for especificado
2. **DraftChaptersStep** - Executa o processo de escrita em cascata para cada capítulo

### Detalhes da DraftChaptersStep

#### Arquitetura em Cascata
Para cada capítulo, o processo segue estas fases:

1. **Modular Beat Generation (Drafting Only)**
   - Divide o capítulo em beats conforme o outline
   - Gera cada beat separadamente usando apenas o DraftingAgent
   - Mantém contexto deslizante entre beats para coerência

2. **Crítica Independente**
   - Executa agentes críticos em paralelo:
     - `canon_critic`: Verifica consistência com cânone/lore
     - `style_critic`: Identifica problemas de estilo e slop
     - `flow_critic`: Analisa transições e pacing
   - Cada crítico produz um arquivo de crítica separado

3. **Síntese Sequencial**
   - Aplica críticas uma após outra usando o SynthesisAgent
   - Cada iteração refina o texto baseado na crítica específica
   - Preserva o fluxo natural enquanto incorpora correções

4. **Avaliação e Validação**
   - Avalia o capítulo usando o harness de avaliação (`evaluate.py`)
   - Verifica continuidade global com `verify_continuity.py`
   - Só avança se atingir threshold de qualidade (≥6.0) e passar na continuidade
   - Após sucesso, faz commit e push para o Git

### Características Técnicas
- **Tentativas Múltiplas**: Até 3 attempts por capítulo para atingir qualidade
- **Threshold Configurável**: Score mínimo para aceitação (padrão: 6.0)
- **Validação de Continuidade**: Verifica consistência global antes de avançar
- **Logging Detalhado**: Salva todas as tentativas em `logs/generation_attempts/`
- **Rollback Inteligente**: Mantém melhor tentativa se todas falharem
- **Integração Git**: Commits automáticos após cada capítulo aprovado

### Fluxo de Dados
- **Entrada**: Documentos de fundação, state atual, tentativa anterior
- **Processo**: Geração modular → Crítica paralela → Síntese sequencial → Avaliação
- **Saída**: Capítulo escrito em `chapters/ch_XX.md`, state atualizado, commit Git

## 4. Pipeline de Revisão Editorial (`pipelines/editorial_revision.py`)

### Objetivo
Processa feedback editorial centralizado em `editorial.md` e aplica revisões direcionadas aos capítulos, validando melhorias através do harness de avaliação.

### Pré-requisitos
- Arquivo `editorial.md` deve existir com feedback estruturado
- Capítulos devem existir em `chapters/` para revisão

### Steps
1. **LoadEditorialStep** - Carrega e parseia `editorial.md` usando extração semântica LLM com fallback regex
2. **ExecuteEditorialStep** - Aplica revisões aos capítulos especificados com loops de correção

### Detalhes da Execução Editorial

#### Parsing de `editorial.md`
- Usa LLM para extração semântica com temperatura baixa (0.1) para precisão
- Fallback para parser regex em caso de falha da LLM
- Estrutura de saída:
  ```json
  {
    "general_notes": "Diretrizes gerais de estilo",
    "chapters": {
      "1": {
        "brief": "Instruções específicas",
        "type": "punctual|continuity_breaking",
        "affects_downstream": [2, 3, 4]
      }
    }
  }
  ```

#### Processo de Revisão por Capítulo
Para cada capítulo alvo:
1. **Baseline**: Avalia versão atual usando `evaluate_chapter()`
2. **Tentativa Inicial**: Gera revisão usando `gen_revision.py` com temperature 0.8
3. **Loops de Correção** (até 5 tentativas):
   - Formata feedback de avaliação em diretrizes para o LLM
   - Combina feedback com diretrizes originais
   - Gera nova versão com temperature ajustada por tentativa
   - Avalia resultado e compara com melhor versão até então
4. **Commit**: Se melhorar ou mantiver qualidade, faz commit do resultado
5. **Fallback**: Se não melhorar, reverte para versão original

### Características Técnicas
- **Extração Semântica**: Usa LLM para entender estrutura de feedback complexo
- **Loops de Correção Iterativos**: Até 5 tentativas com temperaturas variáveis
- **Métricas de Avaliação Abrangentes**:
  - Compliance com cânone
  - Detecção de slop (palavras proibidas, tics estruturais, etc.)
  - Dimensões narrativas (voice adherence, beat coverage, etc.)
  - Frases mais fracas para reescrita
- **Temperatura Adaptativa**: Ajusta criatividade baseado no número da tentativa
- **Integração Git**: Commits após cada capítulo processado com mensagens descritivas

### Fluxo de Dados
- **Entrada**: `editorial.md`, capítulos atuais em `chapters/`
- **Processo**: Parsing feedback → Avaliação baseline → Geração de revisão → Loops de correção → Validação
- **Saída**: Capítulos revisados em `chapters/`, commit Git, state atualizado se necessário

## Integração entre Pipelines

### Fluxo de Trabalho Típico
1. `python run.py --pipeline ideation` → Cria `seed.txt`
2. `python run.py --pipeline foundation` → Gera world, personagens, outline, cânone
3. `python run.py --pipeline book_generation` → Escreve capítulos sequencialmente
4. `python run.py --pipeline editorial_revision` → Aplica feedback editorial

### Pontos de Integração
- **State Compartilhado**: `book_data/state.json` rastreia progresso entre pipelines
- **Documentos de Referência**: Todos os pipelines leem de `book_data/` (world, personagens, etc.)
- **Estado dos Capítulos**: Pipeline de escrita produz arquivos em `chapters/` que são usados pelos pipelines de revisão
- **Git como Banco de Dados**: Todos os pipelines fazem commit e push, criando histórico verificável

## Qualidade e Testabilidade

### Mecanismos de Qualidade Embutidos
1. **Threshold de Aceitação**: Cada capítulo deve atingir score mínimo antes de avançar
2. **Validação de Continuidade**: Verificação global antes de commit
3. **Múltiplas Tentativas**: Até 3 attempts por capítulo para melhorar qualidade
4. **Loops de Correção Editorial**: Até 5 attempts com feedback direcionado
5. **Avaliação Abrangente**: Métricas múltiplas (canon, slop, dimensões narrativas)

### Características que Aumentam Testabilidade
- **Modularidade**: Cada step pode ser testado isoladamente
- **Injeção de Dependência**: Agentes e LLMs podem ser mockados
- **Estado Explícito**: `state.json` torna o progresso visível e testável
- **Separation of Concerns**: Lógica de pipeline separada de implementação de steps
- **Logging Detalhado**: Facilita diagnóstico de falhas

## Pontos de Melhoria e Antipadrões

### Antipadrões Identificados
1. **Hardcoded Caminhos em Vários Locais**: Alguns caminhos são construídos usando caminhos relativos hardcoded
2. **Duplicação de Lógica de Git**: Vários steps fazem chamadas diretas ao Git em vez de abstrair
3. **Estado Global Implícito**: Uso de variáveis de ambiente para configuração pode complicar testes
4. **Parsing Frágil em Alguns Locais**: Dependência de formatos específicos de saída do LLM sem validação robusta

### Sugestões de Refatoramento
1. **Camada de Abstração de Arquivos**: Criar serviço para operações de arquivo com caminhos configuráveis
2. **Serviço de Operações Git**: Encapsular operações Git em uma classe repositório
3. **Objeto de Configuração Explícito**: Passar configuração explícita em vez de ler diretamente de `os.environ`
4. **Validação de Schema**: Validar saídas do LLM contra schemas esperados antes do processamento
5. **Padronização de Tratamento de Erros**: Criar exceções customizadas para diferentes camadas do sistema

### Boas Práticas Presentes
1. **Separation of Responsabilidades Claras**: Cada step tem uma responsabilidade bem definida
2. **Uso Apropriado de Padrões de Projeto**: Composite para pipelines, Factory para agentes
3. **Extensibilidade**: Fácil adicionar novos steps, agentes ou tipos de crítica
4. **Foco na Qualidade**: Múltiplas camadas de validação antes de considerar trabalho completo
5. **Histórico Verificável**: Uso do Git para rastrear todas as mudanças e decisões
6. **Logging Compreensivo**: Facilita auditoria e debug de processos complexos