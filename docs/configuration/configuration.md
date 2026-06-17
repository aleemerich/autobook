# Configuração do Autobook

## Visão Geral

A configuração do Sistema Autobook é gerenciada principalmente através de variáveis de ambiente armazenadas em um arquivo `.env` na raiz do projeto. Este arquivo permite customizar o comportamento do sistema sem modificar o código-fonte, incluindo seleção de provedores de LLM, configuração de modelos, ajuste de parâmetros de qualidade e controle de fluxos de trabalho.

O sistema segue a filosofia de "configuração sobre codificação" - tornando o maior número possível de aspectos configuráveis através de variáveis de ambiente, enquanto mantém padrões razoáveis para uso imediato.

> **Status v0:** esta pagina mistura configuracao pretendida e configuracao
> efetivamente usada pelo codigo. Onde houver diferenca, o comportamento real
> do codigo prevalece. Consulte tambem `../SNAPSHOT_V0.md`.

## Arquivo de Configuração Principal: .env

O arquivo `.env` contém pares `CHAVE=VALOR` que são carregados pelo módulo `llm.py` (através da biblioteca `python-dotenv`) e por outros módulos conforme necessário.

### Exemplo de Arquivo .env
```env
# Seleção de Provedor de LLM
AUTOBOOK_PROVIDER=openrouter

# Chaves de API (apenas uma necessária dependendo do provedor)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...
OPENROUTER_API_KEY=sk-or-v1-...

# URLs Base Customizadas (opcional - sobrescreve padrões do provedor)
# AUTOBOOK_API_BASE_URL=https://api.custom-provider.com

# Seleção de Modelos (opcionais - usa padrões do provedor se não definidos)
AUTOBOOK_WRITER_MODEL=openrouter/owl-alpha
AUTOBOOK_JUDGE_MODEL=nvidia/nemotron-3-super-120b-a12b:free,openrouter/owl-alpha,openrouter/free
AUTOBOOK_REVIEW_MODEL=nvidia/nemotron-3-super-120b-a12b:free

# Configurações de Qualidade e Thresholds
MAX_CHAPTER_ATTEMPTS=3
CHAPTER_THRESHOLD=6.0
NUM_EDITORIAL_RETRIES=5

# Configuração de Críticos
AUTOBOOK_CRITICS=canon_critic,style_critic,flow_critic

# Idioma
AUTOBOOK_LANGUAGE=PT-BR

# Timeouts (em segundos)
AUTOBOOK_PIPELINE_TIMEOUT=3600
AUTOBOOK_LLM_TIMEOUT=3600

# Chaves opcionais de midia
FAL_KEY=your-fal-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
```

## Carregamento de Configuração

### Módulo llm.py (Configuração Primária)
O módulo `llm.py` é responsável pelo carregamento inicial das variáveis de ambiente através de:
```python
from dotenv import load_dotenv
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
```

Isso ocorre na importação do módulo, tornando as variáveis de ambiente disponíveis para todo o sistema.

### Acesso às Configurações
Diferentes módulos acessam as configurações diretamente através de `os.environ.get()`:
- `llm.py`: Para configuração de provedor, chaves de API, modelos e timeouts
- `pipelines/book_generation.py`: Para `MAX_CHAPTER_ATTEMPTS` e `CHAPTER_THRESHOLD`
- `pipelines/editorial_revision.py`: Para `NUM_EDITORIAL_RETRIES` e mapa de temperaturas por tentativa
- `prompt_loader.py`: Para `AUTOBOOK_LANGUAGE`
- Outros módulos conforme necessário

## Categorias de Configuração

### 1. Seleção de Provedor de LLM
Determina qual serviço de Modelo de Linguagem de Grande Escala o sistema usará.

#### AUTOBOOK_PROVIDER
- Valores válidos: `anthropic`, `openai`, `gemini`, `openrouter`
- Padrão: `anthropic` (se não definido ou inválido, o sistema sairá com erro)
- Determina qual perfil em `PROVIDER_PROFILES` (llm.py) será usado

### 2. Chaves de API
Credenciais necessárias para autenticação com o provedor de LLM escolhido.

#### Variáveis Específicas por Provedor
- `ANTHROPIC_API_KEY`: Necessário quando `AUTOBOOK_PROVIDER=anthropic`
- `OPENAI_API_KEY`: Necessário quando `AUTOBOOK_PROVIDER=openai`
- `GEMINI_API_KEY`: Necessário quando `AUTOBOOK_PROVIDER=gemini`
- `OPENROUTER_API_KEY`: Necessário quando `AUTOBOOK_PROVIDER=openrouter`

#### Comportamento quando ausente
Se a chave de API necessária não estiver definida, o sistema:
1. Levanta `LLMConfigurationError` com mensagem clara indicando qual variável está faltando
2. Deixa o orquestrador (`run.py`) converter a exceção em mensagem amigável e código de erro de CLI

### 3. URLs Base Customizadas
Permite sobrescrever a URL base padrão do provedor (útil para proxies, ambientes de teste ou provedores personalizados).

#### AUTOBOOK_API_BASE_URL
- Se definido, sobrescreve o `default_url` do perfil do provedor
- Se vazio ou não definido, usa o `default_url` do perfil do provedor
- Exemplo: Para usar um proxy local: `AUTOBOOK_API_BASE_URL=http://localhost:8000`

### 4. Seleção de Modelos
Controla quais modelos específicos são usados para diferentes tipos de operações.

#### Hierarquia de Seleção de Modelo (em llm.py)
1. `override_model` (passado diretamente para a função `call_llm`)
2. Se `is_review`: `AUTOBOOK_REVIEW_MODEL` → `REVIEW_MODEL` específico do provedor → `AUTOBOOK_REVIEW_MODEL` genérico
3. Se `is_judge`: `AUTOBOOK_JUDGE_MODEL` → `JUDGE_MODEL` específico do provedor → `AUTOBOOK_JUDGE_MODEL` genérico
4. Caso contrário (escrita): `AUTOBOOK_WRITER_MODEL` → `WRITER_MODEL` específico do provedor → `AUTOBOOK_WRITER_MODEL` genérico
5. Por fim: `default_model` do perfil do provedor

#### Variáveis de Modelo
- **Genéricos** (funcionam com qualquer provedor):
  - `AUTOBOOK_WRITER_MODEL`: Modelo para operações de escrita padrão
  - `AUTOBOOK_JUDGE_MODEL`: Modelo para operações de julgamento/avaliação
  - `AUTOBOOK_REVIEW_MODEL`: Modelo para operações de revisão editorial
- **Específicos do Provedor** (sobrescrevem genéricos para um provedor específico):
  - `ANTHROPIC_WRITER_MODEL`, `ANTHROPIC_JUDGE_MODEL`, `ANTHROPIC_REVIEW_MODEL`
  - `OPENAI_WRITER_MODEL`, `OPENAI_JUDGE_MODEL`, `OPENAI_REVIEW_MODEL`
  - `GEMINI_WRITER_MODEL`, `GEMINI_JUDGE_MODEL`, `GEMINI_REVIEW_MODEL`
  - `OPENROUTER_WRITER_MODEL`, `OPENROUTER_JUDGE_MODEL`, `OPENROUTER_REVIEW_MODEL`

### 5. Configurações de Qualidade e Thresholds
Controla os padrões de qualidade que determinam quando o trabalho é considerado aceitável.

#### MAX_CHAPTER_ATTEMPTS
- Número máximo de tentativas para gerar um capítulo antes de aceitar a melhor tentativa
- Padrão: 3
- Tipo: Inteiro positivo
- Valores típicos: 2-5

#### CHAPTER_THRESHOLD
- Pontuação mínima de qualidade (0-10) que um capítulo deve atingir para ser considerado aceito
- Padrão: 6.0
- Tipo: Número de ponto flutuante
- Valores típicos: 5.0-8.0
- Valores abaixo de 5.0 geralmente resultam em qualidade muito baixa
- Valores acima de 8.0 podem ser dificilmente atingíveis levando a muitas tentativas

#### NUM_EDITORIAL_RETRIES
- Número máximo de tentativas de revisão editorial para melhorar um capítulo
- Padrão: 5
- Tipo: Inteiro positivo
- Valores típicos: 3-7

#### AUTOBOOK_CRITICS
- Lista de agentes críticos a usar durante a geração de capítulo
- Formato: string separada por vírgulas (ex: "canon_critic,style_critic,flow_critic")
- Valores válidos: qualquer combinação de "canon_critic", "style_critic", "flow_critic"
- Padrão: "canon_critic,style_critic,flow_critic" (todos os três críticos)

### 6. Idioma
Controla o idioma usado para prompts, diretivas e outras saídas do sistema.

#### AUTOBOOK_LANGUAGE
- Valores válidos: "PT-BR", "EN" (atualmente suportados)
- Padrão: "EN" se não definido ou vazio
- Quando definido como "PT-BR": tenta carregar prompts de `/prompts/PT-BR/` com fallback para `/prompts/EN/`
- Quando definido como "EN": carrega prompts diretamente de `/prompts/EN/`
- Afeta: carregamento de `directives.txt`, outros arquivos de prompt específicos de idioma

### 7. Timeouts
Controla quanto tempo o sistema aguarda antes de considerar operações como falhas.

#### AUTOBOOK_PIPELINE_TIMEOUT
- Timeout geral para operações de pipeline inteiras
- Padrão: 3600 segundos (1 hora)
- Tipo: Inteiro positivo
- Usado como fallback quando `AUTOBOOK_LLM_TIMEOUT` não está definido ou é inválido

#### AUTOBOOK_LLM_TIMEOUT
- Timeout específico para chamadas individuais ao LLM
- Se definido e válido, sobrescreve `AUTOBOOK_PIPELINE_TIMEOUT` para chamadas LLM
- Se vazio, não definido ou inválido, usa `AUTOBOOK_PIPELINE_TIMEOUT`
- Tipo: Inteiro positivo
- Valores típicos: 60-300 segundos (1-5 minutos) para chamadas LLM individuais

### 8. Outras Configurações
Configurações adicionais que controlam comportamentos específicos do sistema.

#### Git automatico
O codigo atual nao implementa flags efetivas `GIT_AUTO_COMMIT` ou
`GIT_AUTO_PUSH`. Os pipelines `foundation`, `book_generation` e
`editorial_revision` chamam `git add`, `git commit` e, em alguns casos,
`git push` por meio do adaptador `workspace/git.py`.

Para transformar isso em configuracao real, sera necessario alterar o codigo
para ler variaveis de ambiente antes dessas chamadas centralizadas.

## Precedência e Herança de Configuração

O sistema segue uma ordem clara de precedência para configuração:

1. **Parâmetros de Função Diretos** (sobrescrita mais alta)
   - Ex: `override_model` passado para `call_llm()`
   - Ex: Parâmetros específicos passados para construtores de agentes

2. **Variáveis de Ambiente Específicas**
   - Ex: `AUTOBOOK_WRITER_MODEL`, `AUTOBOOK_JUDGE_MODEL`, etc.
   - Ex: `MAX_CHAPTER_ATTEMPTS`, `CHAPTER_THRESHOLD`

3. **Variáveis de Ambiente Genéricas**
   - Ex: `AUTOBOOK_PROVIDER`, `AUTOBOOK_LANGUAGE`

4. **Valores Padrão Codificados**
   - Valores hardcoded no código quando nenhuma configuração é encontrada
   - Ex: `default_model` nos `PROVIDER_PROFILES`, `CHAPTER_THRESHOLD = 6.0`

## Exemplos de Configuração para Diferentes Cenários

### Configuração Mínima para Começar
```env
AUTOBOOK_PROVIDER=anthropic
ANTHROPIC_API_KEY=sua-chave-aqui
```

### Configuração para Desenvolvimento Local
```env
AUTOBOOK_PROVIDER=openai
OPENAI_API_KEY=sua-chave-aqui
AUTOBOOK_API_BASE_URL=http://localhost:1234/v1  # Proxy local para teste
MAX_CHAPTER_ATTEMPTS=2
CHAPTER_THRESHOLD=5.0  # Padrão mais baixo para desenvolvimento rápido
AUTOBOOK_LANGUAGE=PT-BR
```

### Configuração para Produção com Alta Qualidade
```env
AUTOBOOK_PROVIDER=anthropic
ANTHROPIC_API_KEY=sua-chave-de-produção-aqui
AUTOBOOK_WRITER_MODEL=claude-sonnet-4-6
AUTOBOOK_JUDGE_MODEL=claude-opus-4-1
AUTOBOOK_REVIEW_MODEL=claude-opus-4-1
MAX_CHAPTER_ATTEMPTS=5
CHAPTER_THRESHOLD=7.5
NUM_EDITORIAL_RETRIES=7
AUTOBOOK_CRITICS=canon_critic,style_critic,flow_critic
AUTOBOOK_LANGUAGE=PT-BR
AUTOBOOK_PIPELINE_TIMEOUT=7200  # 2 horas para pipelines longos
AUTOBOOK_LLM_TIMEOUT=120       # 2 minutos para chamadas LLM
```

### Configuração para Uso com OpenRouter (Acesso a Múltiplos Modelos)
```env
AUTOBOOK_PROVIDER=openrouter
OPENROUTER_API_KEY=sua-chave-openrouter-aqui
# OpenRouter permite acessar muitos modelos através de uma única chave
AUTOBOOK_WRITER_MODEL=anthropic/claude-sonnet-4-6
AUTOBOOK_JUDGE_MODEL=openai/gpt-4o
AUTOBOOK_REVIEW_MODEL=google/gemini-pro-1.5
MAX_CHAPTER_ATTEMPTS=3
CHAPTER_THRESHOLD=6.5
```

## Validação e Tratamento de Erros

### Validação na Inicialização
Quando o módulo `llm.py` é carregado, ele:
1. Lê o arquivo `.env`
2. Valida que `AUTOBOOK_PROVIDER` é um dos valores suportados
3. Não valida imediatamente as chaves de API (validação ocorre na primeira chamada ao LLM)

### Validação na Primeira Chamada ao LLM
Quando `call_llm()` é invocada pela primeira vez:
1. Verifica que a chave de API necessária para o provedor configurado está definida
2. Se ausente, exibe mensagem de erro e sai com código de erro 1
3. Prossegue com a chamada se a chave estiver presente

### Tratamento de Valores Inválidos
- **AUTOBOOK_PROVIDER inválido**: Sistema exibe mensagem listando provedores válidos e sai com código de erro 1
- **Timeouts inválidos**: Sistema usa valores padrão (3600 segundos) e continua
- **Valores numéricos inválidos**: Sistema usa valores padrão definidos no código
- **Strings vazias**: Geralmente tratadas como "não definidas" e usam padrões ou fallback

## Integração com o Sistema de Prompt Loader

A configuração de idioma (`AUTOBOOK_LANGUAGE`) é usada pelo `prompt_loader.py` para:
1. Determinar qual subdiretório de `/prompts/` usar como primário
2. Tentar carregar arquivos do idioma primário primeiro
3. Fazer fallback para `/prompts/EN/` se o arquivo não for encontrado no idioma primário e fallback estiver habilitado
4. Controlar quais diretivas de idioma são anexadas aos system_prompts nas chamadas ao LLM

## Pontos de Melhoria e Antipadrões

### Antipadrões Atuais
1. **Configuração Dispersa**: Variáveis de ambiente são lidas diretamente em múltiplos módulos sem um objeto de configuração centralizado
2. **Validação Tardia**: Algumas configurações não são validadas até serem usadas, o que pode causar falhas em tempo de execução longe do ponto de configuração
3. **Falta de Documentação Integrada**: O arquivo `.env` não contém documentação inline explicando o propósito de cada variável
4. **Configuração de Modelo Complexa**: A hierarquia de seleção de modelo pode ser confusa para usuários novos
5. **Estado Global de Configuração**: Uso direto de `os.environ` torna o teste mais difícil pois o estado é global

### Sugestões de Refatoramento
1. **Criar Objeto de Configuração Centralizado**: Uma classe que carrega, valida e fornece acesso a todas as configurações
2. **Validar na Inicialização**: Validar todas as configurações críticas assim que possível após o carregamento do `.env`
3. **Adicionar Documentação ao .env.example**: Incluir comentários explicativos no arquivo de exemplo
4. **Simplificar Seleção de Modelo**: Considerar uma interface mais direta para seleção de modelo
5. **Injetar Configuração**: Passar objetos de configuração explícitos para funções e classes em vez de ler diretamente de `os.environ`
6. **Adicionar Suporte a Tipos de Dados**: Converter automaticamente strings para os tipos apropriados (int, float, bool) com validação

### Boas Práticas Presentes
1. **Separation of Concerns**: Configuração separada da lógica de código
2. **Flexibilidade**: Múltiplas maneiras de configurar o mesmo aspecto (genérico vs específico do provedor)
3. **Fallbacks Inteligentes**: Valores razoáveis são usados quando configuração não é fornecida
4. **Mensagens de Error Claras**: Quando configuração obrigatória está ausente, mensagens explicativas são fornecidas
5. **Suporte a Múltiplos Ambientes**: Fácil ter diferentes arquivos `.env` para desenvolvimento, teste e produção
6. **Hierarquia Lógica de Sobrescrita**: Ordem clara de precedência para sobrescrever configurações

## Arquivo de Exemplo: .env.example

O projeto inclui um arquivo `.env.example` que mostra todas as variáveis de ambiente suportadas com comentários explicativos:

```env
# ======================
# SELEÇÃO DE PROVEDOR LLM
# ======================
# Provedor de LLM a ser usado: anthropic, openai, gemini, openrouter
AUTOBOOK_PROVIDER=openrouter

# ======================
# CHAVES DE API
# ======================
# Apenas a chave do provedor selecionado é necessária
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIzaSy...
OPENROUTER_API_KEY=sk-or-v1-...

# ======================
# URL BASE CUSTOMIZADA (OPCIONAL)
# ======================
# Sobrescreve a URL base padrão do provedor (útil para proxies, teste, etc.)
# AUTOBOOK_API_BASE_URL=https://api.custom-provider.com

# ======================
# SELEÇÃO DE MODELOS (OPCIONAL)
# ======================
# Se não definidos, usa os padrões do provedor
# Modelo para operações de escrita padrão
# AUTOBOOK_WRITER_MODEL=openrouter/owl-alpha
# ANTHROPIC_WRITER_MODEL=claude-sonnet-4-6

# Modelo para operações de julgamento/avaliação
# AUTOBOOK_JUDGE_MODEL=nvidia/nemotron-3-super-120b-a12b:free,openrouter/owl-alpha,openrouter/free
# ANTHROPIC_JUDGE_MODEL=claude-opus-4-1

# Modelo para operações de revisão editorial
# AUTOBOOK_REVIEW_MODEL=nvidia/nemotron-3-super-120b-a12b:free
# ANTHROPIC_REVIEW_MODEL=claude-opus-4-1

# ======================
# CONFIGURAÇÕES DE QUALIDADE E THRESHOLDS
# ======================
# Número máximo de tentativas para gerar um capítulo antes de aceitar a melhor tentativa
MAX_CHAPTER_ATTEMPTS=3

# Pontuação mínima de qualidade (0-10) que um capítulo deve atingir para ser considerado aceito
CHAPTER_THRESHOLD=6.0

# Número máximo de tentativas de revisão editorial para melhorar um capítulo
NUM_EDITORIAL_RETRIES=5

# Lista de agentes críticos a usar durante a geração de capítulo
# Formato: "canon_critic,style_critic,flow_critic" (qualquer combinação dos três)
AUTOBOOK_CRITICS=canon_critic,style_critic,flow_critic

# ======================
# IDIOMA
# ======================
# Idioma para prompts, diretivas e outras saídas
# Valores válidos: PT-BR, EN
# Padrão: EN se não definido
AUTOBOOK_LANGUAGE=PT-BR

# ======================
# TIMEOUTS (EM SEGUNDOS)
# ======================
# Timeout geral para operações de pipeline inteiras
# Usado como fallback quando AUTOBOOK_LLM_TIMEOUT não está definido
AUTOBOOK_PIPELINE_TIMEOUT=3600

# Timeout específico para chamadas individuais ao LLM
# Se definido e válido, sobrescreve AUTOBOOK_PIPELINE_TIMEOUT para chamadas LLM
AUTOBOOK_LLM_TIMEOUT=3600

# ======================
# CHAVES OPCIONAIS DE MIDIA
# ======================
FAL_KEY=your-fal-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
```

## Conclusão

O sistema de configuração do Autobook fornece uma base flexível e poderosa para personalizar o comportamento do sistema de geração de livros literários. Sua implementação demonstra:

1. **Separação Efetiva de Configuração e Código**: Permite alterar comportamento sem modificar código-fonte
2. **Suporte a Múltiplos Provedores de LLM**: Fácil trocar entre Anthropic, OpenAI, Gemini e OpenRouter
3. **Configuração Granular de Modelos**: Controle fino sobre quais modelos são usados para diferentes tipos de operações
4. **Controle de Qualidade Ajustável**: Parâmetros configuráveis para equilibrar qualidade, tempo e custo
5. **Suporte a Múltiplos Idiomas**: Infraestrutura para PT-BR com expansão fácil para outros idiomas
6. **Integração com Prompt Loader**: Configuração de idioma funciona perfeitamente com o sistema de carregamento de prompts
7. **Hierarquia Clara de Sobrescrita**: Ordem bem definida de precedência para sobrescrever configurações
8. **Mensagens de Error Claras**: Quando configuração obrigatória está ausente, orientação útil é fornecida

O design permite que usuários adaptem facilmente o sistema ao seu ambiente específico, seja para desenvolvimento local, produção em escala ou experimentação com diferentes provedores e modelos de LLM, mantendo ao mesmo tempo uma interface consistente e previsível para todos os componentes do sistema.

Para melhorar ainda mais o sistema de configuração, recomenda-se:
1. Criar um objeto de configuração centralizado para melhor testabilidade e validação
2. Adicionar validação precoce de configurações críticas
3. Melhorar a documentação inline no arquivo .env.example
4. Simplificar interfaces complexas como seleção de modelo quando apropriado
5. Considerar suporte a múltiplos arquivos de configuração (por exemplo, .env.development, .env.production)
