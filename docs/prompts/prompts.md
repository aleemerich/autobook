# Sistema de Prompts do Autobook

## Visão Geral

O sistema de prompts do Autobook gerencia todos os templates de instruções, diretrizes e configurações usados pelos agentes literários ao interagir com os Modelos de Linguagem de Grande Escala (LLMs). Ele está localizado no diretório `/prompts` com subpastas para cada idioma suportado (atualmente PT-BR e EN).

Este sistema permite:
- Separação clara de instruções de lógica de código
- Suporte a múltiplos idiomas com fallback
- Configuração dinâmica de comportamento dos agentes
- Manutenção fácil de prompts através de arquivos de texto simples

## Estrutura de Diretórios

```
/prompts
├── PT-BR/
│   ├── draft_chapter_system.txt
│   ├── gen_revision_system.txt
│   ├── draft_chapter_user.txt
│   ├── continuity.json
│   ├── directives.txt
│   ├── editorial.json
│   ├── gen_revision_user.txt
│   └── slop.json
├── EN/
│   ├── draft_chapter_system.txt
│   ├── gen_revision_system.txt
│   ├── draft_chapter_user.txt
│   ├── continuity.json
│   ├── directives.txt
│   ├── editorial.json
│   ├── gen_revision_user.txt
│   └── slop.json
└── prompt_loader.py
```

## Tipos de Arquivos de Prompt

### 1. Arquivos de Template de Texto (.txt)
Contêm templates de prompt usados diretamente nas chamadas ao LLM.

#### `*_system.txt`
Definem o papel, comportamento e restrições dos agentes (system prompt).

Exemplos:
- `draft_chapter_system.txt`: Instruções para o DraftingAgent
- `gen_revision_system.txt`: Instruções para revisão de capítulo
- `continuity.json`: Embora seja JSON, contém instruções de sistema para verificação de continuidade

#### `*_user.txt`
Contêm templates de prompt do usuário que são combinados com contexto específico.

Exemplos:
- `draft_chapter_user.txt`: Template para solicitação de rascunho de capítulo
- `gen_revision_user.txt`: Template para solicitação de revisão de capítulo

### 2. Arquivos de Configuração JSON (.json)
Contêm dados estruturados usados para configurar comportamento ou fornecer referência.

#### `continuity.json`
Definições e regras para verificação de continuidade entre capítulos.

#### `editorial.json`
Configuração para o sistema de revisão editorial, incluindo:
- Mapeamento de temperaturas por tentativa de retry
- Rótulos para diferentes tipos de feedback
- Template de diretivas corretivas

#### `slop.json`
Regras e definições para detecção e prevenção de "slop" (texto genérico, clichês de AI, etc.).

## Mecanismo de Carregamento: prompt_loader.py

O módulo `prompt_loader.py` é responsável por:
- Detectar o idioma ativo
- Carregar arquivos de prompt com fallback para inglês
- Fornecer uma interface unificada para o resto do sistema

### Funções Principais

#### `get_active_language() -> str`
Retorna o código do idioma ativo baseado na variável de ambiente `AUTOBOOK_LANGUAGE`.
- Retorna "PT-BR" se definido e não vazio
- Retorna "EN" como padrão caso contrário

#### `load_prompt(filename: str, fallback_to_en: bool = True) -> str`
Carrega um arquivo de prompt pelo nome.

**Parâmetros**:
- `filename`: Nome do arquivo para carregar (ex: "directives.txt")
- `fallback_to_en`: Se True, tenta carregar a versão em inglês se o arquivo não for encontrado no idioma ativo

**Processo**:
1. Determina o diretório de prompts baseado no idioma ativo
2. Tenta carregar o arquivo do idioma ativo
3. Se não encontrado e `fallback_to_en` é True, tenta carregar do diretório EN
4. Levanta `FileNotFoundError` se não encontrado em nenhum local

#### Exemplo de Uso
```python
from prompt_loader import load_prompt, get_active_language

# Carrega prompt com fallback para inglês
system_prompt = load_prompt("draft_chapter_system.txt")

# Carrega prompt sem fallback (levanta exceção se não encontrado)
try:
    directive = load_prompt("directives.txt", fallback_to_en=False)
except FileNotFoundError:
    # Tratar caso onde diretivas não são obrigatórias
    directive = ""
```

## Idiomas Suportados

### Português do Brasil (PT-BR)
- Idioma primário do sistema
- Todos os prompts têm versões em PT-BR
- Usado quando `AUTOBOOK_LANGUAGE` é definido como "PT-BR" ou similar

### Inglês (EN)
- Idioma de fallback
- Garante que o sistema funcione mesmo que prompts específicos de idioma estejam faltando
- Usado como padrão quando nenhum idioma é especificado

## Detalhes dos Arquivos de Prompt

### Arquivos de Template de Sistema

#### draft_chapter_system.txt
Define o comportamento do **DraftingAgent**:
- Papel: romancista de elite escrevendo cenas estruturais brutas
- Foco: construção de narrativa sólida, hitting beats específicos, setup da história raw
- Restrição crítica de saída: APENAS o prose bruto da cena - nenhum comentário, nota ou metadata
- Enfatiza escrever o texto completo da cena sem atalhos ou resumos

#### gen_revision_system.txt
Define o comportamento para revisão de capítulo:
- Papel: assistente especializado em revisão literária
- Foco: aplicar diretrizes editoriais específicas e gerais
- Usado pelo script `gen_revision.py` durante o pipeline de revisão editorial

#### continuity.json
Embora seja formato JSON, contém instruções de sistema para verificação de continuidade:
- Estrutura de dados para rastreamento de elementos que afetam capítulos futuros
- Definições de tipos de mudanças (punctual vs continuity_breaking)
- Formato para consulta de continuidade entre capítulos

### Arquivos de Template de Usuário

#### draft_chapter_user.txt
Template usado para solicitar rascunhos de capítulo:
- Combina contexto específico (beat, roadmap, texto anterior, etc.)
- Instrui o agente a escrever apenas a cena solicitada
- Fornece estrutura para geração modular por beats ou escrita completa do capítulo

#### gen_revision_user.txt
Template usado para solicitação de revisão de capítulo:
- Combina texto do capítulo com diretrizes editoriais
- Instrui o agente a revisar o capítulo baseado nas diretrizes fornecidas

### Arquivos de Configuração JSON

#### continuity.json
Estrutura exemplo:
```json
{
  "continuity_rules": {
    "affects_chapters": [3, 4, 5],
    "type": "continuity_breaking",
    "description": "Introdução de novo objeto mágico que afeta capítulos futuros"
  }
}
```

#### editorial.json
Configuração para sistema de revisão editorial:
```json
{
  "retry_temp_map": {
    "1": 0.6,
    "2": 0.6,
    "3": 0.7,
    "4": 0.9,
    "5": 0.5
  },
  "feedback_labels": {
    "slop_critical_header": "### PROBLEMAS DE SLOP CRÍTICO:",
    "canon_violations_header": "### VIOLAÇÕES DE CANON/LORE:",
    // ... outros rótulos
  },
  "corrective_brief": {
    "header": "# DIRETIVAS DE RECORREÇÃO PARA RETENTATIVA",
    // ... template de brief corretivo
  }
}
```

#### slop.json
Definições para detecção de slop:
```json
{
  "tier1_words": ["delve", "tapestry", "myriad", "leveraged", "navigate"],
  "tier2_words": ["utilize", "facilitate", "parameter", "interface"],
  "structural_ai_tics": ["em dash overuse", "excessive semicolons"],
  "fiction_ai_tells": ["suddenly", "inexplicably", "as if by magic"]
}
```

## Fluxo de Trabalho do Sistema de Prompts

### Durante Inicialização do Agente
1. Agente é criado com `system_prompt` específico (de arquivos `_system.txt` ou construído dinamicamente)
2. Quando `agent.execute(prompt)` é chamado:
   - O prompt do usuário pode ser um template que precisa de carregamento
   - O system_prompt pode precisar de diretivas de idioma adicionadas

### Durante Chamada ao LLM (em llm.py)
1. Antes de fazer a chamada HTTP, `llm.call_llm` importa `prompt_loader`
2. Obtém o idioma ativo usando `get_active_language()`
3. Se um idioma estiver ativo:
   - Tenta carregar `prompts/{lang}/directives.txt`
   - Se não encontrado e fallback habilitado, tenta `prompts/EN/directives.txt`
   - Se encontrado, anexa ao `system_prompt`: `system_prompt += f"\n\n{directive}"`
4. Prossegue com a chamada ao LLM usando o (possivelmente modificado) system_prompt

## Integração com Agentes Literários

### Como os Agentes Usam Prompts
Cada agente em `agents.py` tem um `system_prompt` definido em sua classe que é passado diretamente para `llm.call_llm`. Este system_prompt frequentemente contém:

1. **Instruções de Papel**: Definição clara do que o agente deve fazer
2. **Restrições de Comportamento**: O que o agente deve ou não deve fazer
3. **Restrições de Formato de Saída**: Instruções críticas sobre o formato da resposta
4. **Espaço para Contexto Dinâmico**: Locais onde contexto específico é inserido em tempo de execução

### Exemplos de Integração

#### DraftingAgent
- **System Prompt Base**: Definido na classe (veja `agents.py`)
- **Contexto Dinâmico**: Durante execução, elementos como:
  - `title_instruction` (para primeiro beat)
  - `roadmap_text` (mostrando quais beats são concluídos, atual, futuro)
  - `previous_beat_context` (texto do beat anterior para coerência)
  - `character_text`, `world_text`, `canon_text` (referências de lore)
- **Nenhum carregamento de arquivo de prompt direto**: O system_prompt é hardcoded na classe, mas pode ser sobrescrito através de mecanismos de habilidade

#### StylistAgent
- **System Prompt Base**: Construído dinamicamente no construtor
- **Contexto Dinâmico**:
  - `genre_rules` (regras específicas do gênero fornecidas na criação)
  - Estrutura de prompt fixa com espaço para regras de gênero
- **Integração com prompt_loader**: Indireta - as regras de gênero podem vir de arquivos de prompt, mas atualmente são passadas como parâmetros

#### TechnicalEditorAgent
- **System Prompt Base**: Construído dinamicamente no construtor
- **Contexto Dinâmico**:
  - `lore_data` (referência completa de lore)
  - `slop_rules` (regras anti-slop e estilo)
- **Integração com prompt_loader**: Indireta - os dados de lore e regras vêm de arquivos de book_data/, não diretamente de arquivos de prompt

#### Agentes Críticos (Canon, Style, Flow)
- **System Prompt Base**: Construído dinamicamente no construtor
- **Contexto Dinâmico**:
  - Agentes de crítica recebem dados específicos para avaliar contra (lore_data, slop_rules)
  - Estrutura de prompt fixa com espaço para dados de referência
- **Output Format Específico**: Cada agente tem instruções específicas para formato de retorno (lista markdown de problemas ou mensagem de compliance)

#### SynthesisAgent
- **System Prompt Base**: Definido na classe (veja `agents.py`)
- **Contexto Dinâmico**:
  - `current_text`: Texto do capítulo sendo refinado
  - `critique_content`: Conteúdo específico do arquivo de crítica sendo aplicado
- **Nenhum carregamento de arquivo de prompt direto**: System_prompt é hardcoded, mas contexto é passado dinamicamente

## Uso em Scripts de Pipeline

### Ideation Pipeline (ideation.py)
- Usa `SYSTEM_PROMPT` e `GENERATE_PROMPT` como strings constantes
- Não carrega prompts de arquivos - todo o prompt é hardcoded
- Foca em geração de conceitos iniciais ao invés de escrita literária

### Foundation Pipeline (foundation.py)
- Constrói prompts complexos inline usando dados de várias fontes
- Usa templates de string com placeholders para:
  - `seed`, `world`, `characters`, `voice_p2`, `mystery`, `craft`
- Não usa arquivos de prompt externos para as principais gerações

### Book Generation Pipeline (book_generation.py)
- **Carregamento Direto de Arquivos**:
  - `genre_rules = load_genre_rules()` (de `prompt_loader.py`)
  - `slop_rules = load_slop_rules_instruction()` (de `prompt_loader.py`)
- **Construção Dinâmica de Prompt**:
  - Combina `world_text`, `canon_text`, `characters_text`, `voice_text`
  - Usa esses elementos em prompts complexos para drafting, estilização e edição técnica
- **Indireto**: Usa funções de prompt_loader para carregar regras de gênero e slop

### Editorial Revision Pipeline (editorial_revision.py)
- **Carregamento Semântico Principal**:
  - `load_editorial_markdown()` - Carrega e parseia `editorial.md`
  - Usa LLM para extração semântica com fallback regex
- **Carregamento de Configuração**:
  - `load_editorial_config()` - Carrega `editorial.json` para configuração de retry
- **Geração de Feedback**:
  - `format_eval_feedback()` - Converte dados de avaliação em diretrizes para LLM
  - Combina com briefs específicos do capítulo e notas gerais
- **Uso de Templates**:
  - Cria arquivos temporários de brief para passar para `gen_revision.py`

## Pontos de Melhoria e Antipadrões

### Antipadrões Atuais
1. **Mix de Estratégias**: Alguns prompts são hardcoded, outros carregados de arquivos, outros construídos dinamicamente
2. **Duplicação de Lógica de Carregamento**: Similaridade entre `load_genre_rules`, `load_slop_rules_instruction` e funções de prompt_loader
3. **Fallback Inconsistente**: Alguns carregamentos usam fallback para inglês, outros não
4. **Hardcoded Caminhos em Alguns Locais**: Referências diretas a caminhos de arquivo em vez de usar o sistema de carregamento
5. **Templates Complexos Inline**: Alguns prompts são construídos como strings multilinha complexas no código

### Sugestões de Refatoramento
1. **Padronizar Carregamento de Prompt**: Usar `prompt_loader.load_prompt` consistentemente para todos os prompts externos
2. **Separar Templates de Dados**: Mover templates de prompt complexos para arquivos externos
3. **Criar Funções de Ajuda Específicas**: Funções como `load_drafting_prompt(context)` que encapsulam a lógica de construção
4. **Padronizar Fallback Garantir**: Sempre tentar carregar do idioma ativo com fallback para inglês, exceto quando explicitamente não desejado
5. **Separar Prompts de Sistema e Usuário**: Ter pastas ou convenções claras para diferentes tipos de prompt
6. **Usar Variáveis de Ambiente para Caminhos**: Permitir customização do diretório de prompts através de variáveis de ambiente

### Boas Práticas Presentes
1. **Separation of Concerns**: Prompts separados da lógica de código
2. **Suporte a Múltiplos Idiomas**: Infraestrutura para PT-BR e EN com fallback
3. **Carregamento Centralizado**: `prompt_loader.py` fornece interface única para carregamento de prompts
4. **Feedback Semântico em Editorial**: Uso de LLM para entender estrutura complexa de feedback em `editorial.md`
5. **Configuração Estruturada**: Uso de JSON para configuração complexa como `editorial.json` e `slop.json`
6. **Separação Clara de Responsabilidades**:
   - `prompt_loader.py`: Carregamento e fallback de idiomas
   - Arquivos de prompt: Conteúdo específico de instruções
   - Módulos que usam prompts: Lógica de como aplicar e combinar prompts

## Exemplos de Prompts

### draft_chapter_system.txt (PT-BR)
```
Você é um romancista de elite escrevendo as cenas estruturais brutas de um capítulo.
Seu foco é construir uma narrativa estrutural sólida, atingir o batimento planejado específico,
e preparar a história bruta. Escreva o TEXTO COMPLETO da cena sem atalhos ou resumos.

RESTRIÇÃO CRÍTICA DE FORMATO DE SAÍDA:
Retorne APENAS o prose bruto da cena de rascunho. NÃO inclua nenhum comentário de introdução/conclusão,
notas, cabeçalhos ou metadados. Saída o texto da história e nada mais.
```

### gen_revision_system.txt (PT-BR)
```
Você é um assistente especializado em revisão literária com experiência em edição de ficção.
Seu trabalho é aplicar diretrizes editoriais específicas e gerais a um rascunho de capítulo
e produzir uma versão revisada que mantenha a trama correta enquanto incorpora todos os
feedback necessários.

RESTRIÇÃO CRÍTICA DE FORMATO DE SAÍDA:
Retorne APENAS o texto revisado do capítulo. NÃO inclua nenhum preâmbulo, observação,
lista de mudanças feita ou resposta conversacional. Sua resposta deve ser 100% texto da história revisada.
```

### continuity.json (excerpt)
```json
{
  "continuity_definition": "Um elemento que afeta capítulos futuros se sua alteração exigiria mudanças em capítulos posteriores para manter consistência interna.",
  "types": {
    "punctual": "Afeta apenas o capítulo em que ocorre",
    "continuity_breaking": "Afeta o capítulo em que ocorre e um ou mais capítulos futuros"
  }
}
```

### editorial.json (excerpt)
```json
{
  "retry_temp_map": {
    "1": 0.6,
    "2": 0.6,
    "3": 0.7,
    "4": 0.9,
    "5": 0.5
  },
  "feedback_labels": {
    "slop_critical_header": "### PROBLEMAS DE SLOP CRÍTICO:",
    "canon_violations_header": "### VIOLAÇÕES DE CANON/LORE:",
    "slop_style_header": "### ESTILO & VOCABULÁRIO (SLOP SECUNDÁRIO):",
    "narrative_dimensions_header": "### DEFICIÊNCIAS NAS DIMENSÕES NARRATIVAS:",
    "weakest_sentences_header": "### FRASES MAIS FRACAS (REESCREVER/MELHORAR):",
    "banned_words_msg": "- PALAVRAS PROIBIDAS usadas (MUDAR IMEDIATAMENTE): {words}",
    "suspicious_words_msg": "- Palavras suspeitas usadas (evitar): {words}",
    "structural_tics_msg": "- Tiques estruturais de IA detectados: {words}",
    "cliches_tells_msg": "- Clichês/tells de IA detectados: {words}",
    "em_dash_density_msg": "- Densidade excessiva de travessões: {density} (limite máximo é 15).",
    "dimension_header": "#### Dimensão '{dim}' (Nota {score}):",
    "weakest_moment_prefix": "  * Ponto fraco: \"{moment}\"",
    "suggested_fix_prefix": "  * Correção sugerida: {fix}"
  }
}
```

### slop.json (excerpt)
```json
{
  "tier1_words": [
    "delve",
    "tapestry",
    "myriad",
    "leveraged",
    "navigate",
    "realm",
    "steadfast",
    "undertaken",
    "endeavor"
  ],
  "tier2_words": [
    "utilize",
    "facilitate",
    "parameter",
    "interface",
    "synergy",
    "leverage",
    "robust",
    "comprehensive"
  ],
  "structural_ai_tics": [
    "em dash overuse",
    "excessive semicolons",
    "parenthetical overuse",
    "colon overuse"
  ],
  "fiction_ai_tells": [
    "suddenly",
    "inexplicably",
    "as if by magic",
    "fortunately",
    "unfortunately",
    "it turned out that",
    "little did they know"
  ]
}
```

## Integração com o Fluxo de Trabalho Geral

### Durante Geração de Capítulo (book_generation.py)
1. **Carregamento de Regras**:
   - `genre_rules = load_genre_rules()` → Carrega regras de gênero do prompt apropriado
   - `slop_rules = load_slop_rules_instruction()` → Carrega regras de slop do prompt apropriado
2. **Construção de Contexto**:
   - Coleta `world_text`, `canon_text`, `characters_text`, `voice_text` de `book_data/`
3. **Criação de Agentes**:
   - `stylist_agent = factory.get_agent("stylist", genre_rules=genre_rules)`
   - `tech_editor_agent = factory.get_agent("technical_editor", lore_data=lore_data, slop_rules=slop_rules)`
4. **Execução em Cascata**:
   - Cada agente recebe seu system_prompt (combinado com contexto quando necessário)
   - O system_prompt pode ter diretivas de idioma adicionadas automaticamente via `llm.py`

### Durante Revisão Editorial (editorial_revision.py)
1. **Carregamento de Feedback Centralizado**:
   - `parsed = load_editorial_markdown()` → Extrai estrutura de `editorial.md`
2. **Carregamento de Configuração**:
   - `config = load_editorial_config()` → Obtém parâmetros de retry de `editorial.json`
3. **Geração de Feedback Dinâmico**:
   - `feedback_str = format_eval_feedback(eval_data, retry_idx)` → Converte avaliação em diretrizes
4. **Criação de Brief Temporário**:
   - Combina brief específico do capítulo, feedback de avaliação e notas gerais
   - Salva em arquivo temporário para passar para `gen_revision.py`
5. **Execução de Revisão**:
   - `gen_revision.py` usa os arquivos de prompt de sistema e usuário apropriados
   - Aplica temperatura baseada na tentativa de retry

## Conclusão

O sistema de prompts do Autobook fornece uma base flexível e internacionalizada para gerenciar instruções aos Modelos de Linguagem de Grande Escala. Sua implementação demonstra:

1. **Separação Efetiva de Responsabilidades**: Prompts separados da lógica de código, facilitando manutenção e atualização
2. **Suporte a Múltiplos Idiomas**: Infraestrutura robusta para PT-BR com fallback para EN, permitindo fácil expansão para outros idiomas
3. **Carregamento Centralizado**: `prompt_loader.py` fornece interface única e consistente para acesso a prompts
4. **Feedback Semântico Avançado**: Uso inteligente de LLM para entender e processar estruturas complexas de feedback em `editorial.md`
5. **Configuração Estruturada**: Uso de JSON para configuração complexa que seria difícil de gerenciar em arquivos de texto simples
6. **Extensibilidade**: Fácil adicionar novos tipos de prompt, idiomas ou mecanismos de carregamento

O design permite que escritores e editores ajustem facilmente o comportamento do sistema através de arquivos de texto simples, sem modificar código, enquanto fornece aos desenvolvedores uma interface consistente e confiável para acessar esses recursos.