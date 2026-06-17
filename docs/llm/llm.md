# Cliente LLM do Autobook

## Visão Geral

O módulo `llm.py` implementa um cliente unificado para Modelos de Linguagem de Grande Escala (LLMs) que suporta múltiplos provedores através de uma interface comum. Ele é responsável por todas as chamadas aos modelos de linguagem usadas pelos agentes no sistema Autobook.

## Provedores Suportados

O cliente atualmente suporta quatro provedores principais:

1. **Anthropic** (Claude)
2. **OpenAI** (GPT)
3. **Gemini** (Google)
4. **OpenRouter** (interface unificada para vários modelos)

## Arquitetura e Design

### Padrão de Projeto: Strategy
O módulo implementa o padrão **Strategy** onde cada provedor tem um perfil de configuração que define:
- Variável de ambiente para a chave de API
- URL base padrão
- Sufixo do endpoint
- Modelo padrão
- Variáveis de ambiente para modelos específicos de escritor, juiz e revisor

### Fluxo de Processamento
1. **Resolução do Provedor**: Determinado pela variável de ambiente `AUTOBOOK_PROVIDER` (padrão: "anthropic")
2. **Validação da Chave de API**: Verifica se a chave de API necessária está definida no .env
3. **Resolução da URL**: Usa URL base customizada ou padrão do provedor
4. **Seleção do Modelo**: Hierarquia de sobrescrita:
   - `override_model` (se fornecido)
   - Modelo específico para revisão/juiz (se aplicável)
   - Modelo específico de escritor (se aplicável)
   - Variável de ambiente genérica (AUTOBOOK_WRITER_MODEL, etc.)
   - Modelo padrão do perfil do provedor
5. **Construção da Requisição**: Cria cabeçalhos e payload específicos para o provedor
6. **Execução com Retry**: Faz a chamada HTTP com tentativas múltiplas e backoff exponencial
7. **Extração da Resposta**: Analisa a resposta JSON e extrai o texto conforme o formato do provedor

## Configuração

### Variáveis de Ambiente
O módulo lê várias variáveis de ambiente do arquivo `.env`:

#### Seleção do Provedor
- `AUTOBOOK_PROVIDER`: Provedor a ser usado (anthropic, openai, gemini, openrouter)

#### Chaves de API (uma necessária dependendo do provedor)
- `ANTHROPIC_API_KEY`: Para Anthropic
- `OPENAI_API_KEY`: Para OpenAI
- `GEMINI_API_KEY`: Para Gemini
- `OPENROUTER_API_KEY`: Para OpenRouter

#### URLs Base Customizadas (opcionais)
- `AUTOBOOK_API_BASE_URL`: URL base customizada (sobrescreve o padrão do provedor)

#### Seleção de Modelo (opcionais)
- `AUTOBOOK_WRITER_MODEL`: Modelo para operações de escrita
- `AUTOBOOK_JUDGE_MODEL`: Modelo para operações de julgamento/avaliação
- `AUTOBOOK_REVIEW_MODEL`: Modelo para operações de revisão
- Modelos específicos do provedor (ex: `ANTHROPIC_WRITER_MODEL`, `OPENAI_JUDGE_MODEL`, etc.)

#### Timeouts
- `AUTOBOOK_PIPELINE_TIMEOUT`: Timeout geral para operações de pipeline (padrão: 3600s)
- `AUTOBOOK_LLM_TIMEOUT`: Timeout específico para chamadas LLM (padrão: usa o timeout de pipeline)

#### Outros Configurações
- `MAX_CHAPTER_ATTEMPTS`: Número máximo de tentativas por capítulo (padrão: 3)
- `CHAPTER_THRESHOLD`: Limite de qualidade para aceitação de capítulo (padrão: 6.0)
- `NUM_EDITORIAL_RETRIES`: Número de tentativas para revisão editorial (padrão: 5)
- `AUTOBOOK_CRITICS`: Lista de críticos a usar (padrão: "canon_critic,style_critic,flow_critic")

## Detalhes de Implementação por Provedor

### Anthropic (Claude)
- **Endpoint**: `/v1/messages`
- **Cabeçalhos**: 
  - `x-api-key`: Chave de API
  - `anthropic-version`: "2023-06-01"
  - `anthropic-beta`: "context-1m-2025-08-07" (para contexto maior)
  - `content-type`: "application/json"
- **Payload**:
  - `model`: Nome do modelo
  - `max_tokens`: 8000 (escrita) ou 16000 (julgamento/revisão)
  - `temperature`: Valor configurado
  - `system`: Prompt de sistema
  - `messages`: Array com objeto {"role": "user", "content": prompt}
- **Resposta**: Extrai `data[0][0]["text"]` do array de conteúdo

### Provedores Compatíveis com OpenAI (OpenAI, Gemini, OpenRouter)
- **Endpoint**: `/v1/chat/completions` (ou similar)
- **Cabeçalhos**:
  - `Authorization`: "Bearer {api_key}"
  - `Content-Type`: "application/json"
  - Cabeçalhos específicos do OpenRouter (se aplicável):
    - `HTTP-Referer`: "https://github.com/aleemerich/autobook"
    - `X-Title`: "Autobook"
- **Payload**:
  - `model`: Nome do modelo
  - `temperature`: Valor configurado
  - `messages`: Array com:
    - {"role": "system", "content": system_prompt}
    - {"role": "user", "content": prompt}
  - `max_tokens`: 4000 (julgamento/revisão) ou 8000 (escrita)
- **Resposta**: Extrai `data["choices"][0]["message"]["content"]`

### Tratamento Especial do OpenRouter
- Adiciona cabeçalhos de descoberta: `HTTP-Referer` e `X-Title`
- Trata respostas de erro que retornam 200 OK com campo "error" no JSON

## Mecanismo de Retry e Backoff

### Configuração
- `max_retries`: 3 tentativas
- `backoff_factor`: 2 (tempo de espera: 2^attempt segundos)
- **Tentativa 1**: Espera 0s (imediata)
- **Tentativa 2**: Espera 2s
- **Tentativa 3**: Espera 4s
- **Tentativa 4**: Espera 8s (se max_retries fosse 4)

### Tratamento de Erros Específicos
- **429 (Rate Limit)**: Respeita o cabeçalho `Retry-After` se presente
- **Outros 4xx/5xx**: Levanta exceção após todas as tentativas
- **Erros de Payload**: Detecta erros retornados com 200 OK mas com campo "error" no JSON (comum no OpenRouter)

## Integração com Prompt Loader e Diretivas de Idioma

### Fluxo de Integração
1. Antes de fazer a chamada ao LLM, o módulo `call_llm` importa `prompt_loader`
2. Obtém o idioma ativo usando `get_active_language()`
3. Se um idioma estiver ativo, tenta carregar `directives.txt` para esse idioma
4. Se encontrado, anexa a diretiva ao final do `system_prompt`
5. Se não encontrado para o idioma ativo, tenta carregar a versão em inglês como fallback
6. Se nenhum for encontrado, continua sem diretivas adicionais

### Exemplo de Integração
```python
from prompt_loader import load_prompt, get_active_language
lang = get_active_language()
if lang:
    try:
        directive = load_prompt("directives.txt", fallback_to_en=False)
        system_prompt += f"\n\n{directive}"
    except FileNotFoundError:
        pass
```

## Tratamento de Erros e Logging

### Saída no stderr
O módulo fornece logging detalhado no stderr para depuração:
- "[LLM] Requesting model 'X' from provider 'Y' (Attempt Z/N)..."
- "[LLM] Waiting for API response (timeout: Ts)..."
- "[LLM] Response received! Status: XXX. Processing content..."
- Mensagens de erro detalhadas quando as chamadas falham
- "[LLM] Rate limited (429). Respecting Retry-After header: sleeping for Ss..."
- "[WARNING] LLM API call failed on attempt N: [erro]"
- "[FATAL ERROR] Max retries exceeded during LLM API call."

### Tratamento de Erros
- **Chave de API ausente**: Levanta `LLMConfigurationError` antes de chamar o provedor externo
- **Provedor desconhecido**: Levanta `LLMConfigurationError` listando provedores suportados
- **Falha na chamada**: Após todas as tentativas, levanta a exceção original
- **Resposta de erro da API**: Levanta exceção com detalhes da resposta
- **Payload de erro (200 OK com erro)**: Levanta ValueError com mensagem de erro da API

## Pontos de Melhoria e Antipadrões

### Antipadrões Atuais
1. **Acoplamento estreito com dotenv**: Carrega variáveis de ambiente diretamente em tempo de importação
2. **Lógica complexa de seleção de modelo**: Múltiplas condições aninhadas podem ser difíceis de seguir
3. **Duplicação de lógica de cabeçalhos/payload**: Similaridade entre provedores antropico e outros
4. **Tratamento de erro em evolução**: Configuração já usa exceções tipadas; falhas HTTP ainda propagam exceções da camada externa

### Sugestões de Refatoramento
1. **Separar Configuração da Lógica**: Carregar variáveis de ambiente em uma função de configuração explícita
2. **Estratégia de Seleção de Modelo**: Extrair a lógica de seleção de modelo para uma função separada
3. **Padronização de Construção de Requisição**: Usar estratégia ou template method para construir requisições
4. **Camada de Abstração de Erros**: Expandir exceções específicas para diferentes tipos de falha externa
5. **Injeção de Dependência de HTTP Client**: Facilitar teste permitindo injeção de cliente HTTP mock

### Boas Práticas Presentes
1. **Separation of Concerns**: Claro separação entre resolução de provedor, construção de requisição, execução e extração de resposta
2. **Tratamento de Error Robusto**: Múltiplas camadas de verificação de erro incluindo respect headers de rate limit
3. **Extensibilidade**: Fácil adicionar novos provedores adicionando ao `PROVIDER_PROFILES`
4. **Configuração Flexível**: Múltiplas formas de especificar modelos (sobrescrita, específicos do provedor, genéricos, padrões)
5. **Logging Detalhado**: Informações abrangentes para depuração e monitoramento
6. **Timeouts Configuráveis**: Timeouts separados para pipeline inteiro e chamadas individuais LLM
7. **Mecanismo de Retry Inteligente**: Backoff exponencial com respeito a headers de rate limit
8. **Suporte a Múltiplos Formatos de Resposta**: Tratamento específico para estrutura de resposta de cada provedor

## Exemplo de Uso

### Chamada Direta
```python
from llm import call_llm

response = call_llm(
    prompt="Escreva um parágrafo sobre inteligência artificial.",
    system_prompt="Você é um assistente útil e conhecedor.",
    temperature=0.7
)
print(response)
```

### Uso com Modelos Específicos
```python
# Usar modelo de juiz para avaliação
evaluation = call_llm(
    prompt="Avalie a qualidade deste texto: [texto]",
    system_prompt="Você é um avaliador crítico de textos literários.",
    temperature=0.2,
    is_judge=True  # Usa AUTOBOOK_JUDGE_MODEL ou equivalente
)

# Usar modelo de revisão para feedback de edição
review = call_llm(
    prompt="Forneça sugestões de melhoria para este capítulo: [texto]",
    system_prompt="Você é um editor experiente de ficção.",
    temperature=0.3,
    is_review=True  # Usa AUTOBOOK_REVIEW_MODEL ou equivalente
)

# Sobrescrever modelo específico
custom_response = call_llm(
    prompt="Explique a teoria da relatividade.",
    system_prompt="Você é um professor de física.",
    temperature=0.5,
    override_model="gpt-4-turbo"  # Usa este modelo independente da configuração
)
```

## Integração com o Sistema de Agentes

Os agentes em `agents.py` usam o módulo LLM através da chamada `call_llm` encapsulada no método `execute`:

```python
def execute(self, prompt: str) -> str:
    """Call the underlying LLM with the agent's specific persona/instructions."""
    try:
        return call_llm(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=self.temperature,
            is_judge=False
        )
    except Exception as e:
        print(f"[{self.name}] Error during execution: {e}", file=sys.stderr)
        raise
```

Isso garante que:
- Cada agente use seu próprio `system_prompt` e `temperature`
- Todas as chamadas ao LLM passem pelo mesmo mecanismo de tratamento de erro e retry
- O provedor e modelo usados sejam consistentes com a configuração global
- As diretivas de idioma sejam aplicadas automaticamente quando apropriado

## Conclusão

O módulo `llm.py` fornece uma base robusta e flexível para interação com Modelos de Linguagem de Grande Escala no sistema Autobook. Sua implementação demonstra:

1. **Boa Aplicação de Padrões de Projeto**: Uso eficaz do padrão Strategy para suporte a múltiplos provedores
2. **Tratamento de Error Robusto**: Mecanismos abrangentes de retry, backoff e respeito a limitações de taxa
3. **Flexibilidade de Configuração**: Múltiplas formas de configurar provedores, modelos e parâmetros
4. **Integração Suave**: Funcionamento transparente com o sistema de agentes e prompt loader
5. **Logging Detalhado**: Informações abrangentes para depuração e monitoramento em produção

O design permite que o sistema facilmente adote novos provedores de LLM ou modelos à medida que ficam disponíveis, mantendo uma interface consistente para todos os agentes literários.
