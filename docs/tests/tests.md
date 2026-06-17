# Sistema de Testes do Autobook

## Visão Geral

O sistema de testes do Autobook implementa uma suíte abrangente de testes unitários e de integração para garantir a confiabilidade e correto funcionamento do sistema de geração de livros. Os testes ativos estão localizados no diretório `/tests`.

> **Status:** o baseline moderno verificado e `uv run --with pytest pytest tests`, com 301 testes passando. A pasta `/legacy/tests` existe, mas foi desativada e excluída da suíte de testes moderna. Caso seja executada diretamente, a pasta é configurada para ser ignorada via `conftest.py`.

Este sistema verifica:
- Funcionalidade básica de módulos individuais (testes unitários)
- Integração entre componentes (testes de integração)
- Fluxos completos de pipeline
- Funcionalidade de avaliação e métricas
- Suporte a múltiplos idiomas
- Conectividade com provedores de LLM
- Funcionalidade de tiposetagem e geração de saída

## Estrutura de Testes

### Testes Principais (`/tests`)
- `test_continuity.py`: Testes de verificação de continuidade entre capítulos
- `test_evaluate_unit.py`: Testes unitários do módulo de avaliação
- `test_typeset.py`: Testes de funcionalidade de tiposetagem (LaTeX, EPUB)
- `test_logging.py`: Testes do sistema de logging
- `test_foundation_pipeline.py`: Testes do pipeline de fundação
- `test_llm_connectivity.py`: Testes de conectividade com provedores de LLM
- `test_language_support.py`: Testes de suporte a múltiplos idiomas
- `test_integration.py`: Testes de integração entre componentes principais
- `test_llm_unit.py`: Testes unitários do módulo LLM
- `test_ideation_pipeline.py`: Testes do pipeline de ideação
- `test_generation_flow.py`: Testes do fluxo completo de geração de capítulos

### Testes Legados (`/legacy/tests`)
- Status: desativados e explicitamente ignorados na suite de testes moderna.
- Motivo principal: referências a módulos históricos removidos ou renomeados.
- Estão configurados no pytest de forma a serem ignorados por padrão e a retornarem uma saída limpa (sem testes executados) quando invocados diretamente.
- `test_batch_generators_unit.py`: Testes de geradores em lote
- `test_ideation_unit.py`: Testes unitários de ideação
- `test_pipeline_control.py`: Testes de controle de pipeline
- `test_draft_chapter_unit.py`: Testes unitários de geração de capítulos
- `test_foundation_generators_unit.py`: Testes de geradores de fundação
- `test_seed_unit.py`: Testes de funcionalidade de semente
- `test_editorial.py`: Testes de funcionalidade editorial

## Filosofia de Testes

### Pirâmide de Testes
O sistema segue aproximadamente a pirâmide de testes:
- **Testes Unitários** (base): Maior número, testam funções e classes individuais
- **Testes de Integração** (meio): Testam interação entre múltiplos componentes
- **Testes de Fluxo Completo** (topo): Menor número, testam fluxos completos de uso

### Princípios Orientadores
1. **Isolamento**: Testes unitários devem isolar a unidade sob teste usando mocks quando necessário
2. **Determinismo**: Testes devem produzir resultados consistentes dadas as mesmas entradas
3. **Velocidade**: Testes devem ser rápidos o suficiente para execução frequente durante desenvolvimento
4. **Clareza**: Testes devem ser fáceis de entender e modificar
5. **Cobertura**: Testes devem cobrir funcionalidades críticas e caminhos de código frequentemente usados

## Configuração e Execução

### Dependências de Teste
Os testes dependem de:
- `pytest`: Framework de teste principal
- `pytest-mock`: Para criação de mocks
- `responses`: Para mocking de chamadas HTTP (especialmente para testes de LLM)
- `pytest-cop`: Para verificação de estilos de código (opcional)

### Como Executar Testes
```bash
# Executar baseline moderno
uv run --with pytest pytest tests

# Executar teste específico
uv run --with pytest pytest tests/test_llm_unit.py

# Executar teste com marcador específico
uv run --with pytest pytest -m "slow" tests

# Executar testes em modo verbose
uv run --with pytest pytest -v tests

# Executar testes com cobertura
uv run --with pytest pytest --cov=autobook tests/
```

### Marcadores de Teste
- `slow`: Testes que levam mais tempo para executar (ex: testes que fazem chamadas reais a APIs externas quando não mockados)
- `integration`: Testes de integração entre componentes
- `unit`: Testes unitários de funções/classes individuais

## Detalhes dos Arquivos de Teste

### test_llm_unit.py
Testa o módulo `llm.py` isoladamente usando mocks para evitar chamadas reais a APIs externas.

#### Áreas de Cobertura
- Seleção de provedor baseado em variáveis de ambiente
- Validação de chaves de API ausentes
- Construção de cabeçalhos e payloads específicos para cada provedor
- Lógica de seleção de modelo (sobrescrita, específicos do provedor, genéricos, padrões)
- Mecanismo de retry com backoff exponencial
- Tratamento de erros de rede e respostas de API
- Extração de respostas para diferentes formatos de provedor
- Tratamento especial do OpenRouter (cabeçalhos de descoberta, detecção de erros em payload 200 OK)
- Integração com prompt loader para diretivas de idioma
- Funções auxiliares como `get_retry_temperature` e `load_editorial_markdown_fallback`

#### Técnicas de Mock
- `responses` library para mocking de chamadas HTTP
- `unittest.mock` para patching de variáveis de ambiente e outras dependências
- Simulação de diferentes códigos de status HTTP e respostas de JSON

### test_llm_connectivity.py
Testa conectividade real com provedores de LLM (quando credenciais estão disponíveis).

#### Áreas de Cobertura
- Verificação de que as chaves de API necessárias estão configuradas
- Teste de chamada básica a cada provedor configurado
- Verificação de que respostas são recebidas e têm formato esperado
- Teste de diferentes modelos configurados
- Verificação de que timeouts funcionam corretamente

#### Observação
Este teste é marcado como `slow` e pode ser pulado em ambientes de desenvolvimento onde não se deseja fazer chamadas reais a APIs externas ou quando credenciais não estão disponíveis.

### test_evaluate_unit.py
Testa o módulo `evaluate.py` e funções relacionadas de avaliação.

#### Áreas de Cobertura
- Extração de texto de capítulo de arquivos
- Verificação de conformidade com cânone
- Detecção de slop (palavras proibidas, tiques estruturais, tells de ficção)
- Avaliação das dimensões narrativas (voice adherence, beat coverage, etc.)
- Identificação das três frases mais fracas
- Cálculo da pontuação geral
- Integração com funções de formatação de feedback
- Testes de borda (capítulos vazios, texto muito curto, etc.)

#### Técnicas de Teste
- Criação de arquivos de capítulo temporários em diretórios de teste
- Mocking de arquivos de referência (canon.md, world.md, etc.)
- Uso de textos de exemplo com características conhecidas para testar detecção específica
- Verificação de que funções retornam estruturas esperadas com tipos corretos

### test_continuity.py
Testa o sistema de verificação de continuidade entre capítulos.

#### Áreas de Cobertura
- Carregamento e parsing de `editorial.md`
- Identificação de mudanças que afetam capítulos futuros
- Verificação de consistência entre elementos declarados como afetando capítulos posteriores
- Testes de diferentes tipos de mudanças (punctual vs continuity_breaking)
- Integração com o script `verify_continuity.py`
- Testes de borda (arquivo editorial.md ausente, formato inválido, etc.)

#### Técnicas de Teste
- Criação de arquivos de `editorial.md` temporários com diferentes estruturas
- Mocking de funções de carregamento de dados de referência
- Verificação de que o script de continuidade retorna códigos de saída esperados
- Testes de diferentes combinações de mudanças que afetam ou não capítulos futuros

### test_foundation_pipeline.py
Testa o pipeline de fundação (`pipelines/foundation.py`).

#### Áreas de Cobertura
- Verificação de pré-requisitos (existência de `seed.txt`)
- Geração de `world.md` (World Bible)
- Geração de `characters.md` (Character Registry)
- Geração de `outline.md` (Chapter Outline & Beats)
- Geração de `canon.md` (Canon Fact Database)
- Commit e push no Git
- Atualização de `state.json`
- Tratamento de erros (arquivo seed.txt ausente, etc.)

#### Técnicas de Teste
- Criação de arquivos de entrada temporários (`seed.txt`, `voice.md`, `CRAFT.md`)
- Mocking de chamadas ao LLM para retornar respostas previsíveis
- Verificação de que arquivos de saída são criados com conteúdo esperado
- Testes de que funções lançam exceções apropriadas quando pré-requisitos faltam
- Verificação de que operações de Git são chamadas corretamente (usando mocking)

### test_ideation_pipeline.py
Testa o pipeline de ideação (`pipelines/ideation.py`).

#### Áreas de Cobertura
- Verificação de arquivos `seed.txt` existentes (bypass)
- Funcionalidade do questionário interativo
- Geração de conceitos via LLM
- Seleção de conceitos (números 1-3 ou customizado)
- Geração opcional de `MYSTERY.md`
- Inicialização de `state.json`
- Tratamento de diferentes fluxos de entrada do usuário

#### Técnicas de Teste
- Mocking de `input()` para simular respostas do usuário
- Mocking de chamadas ao LLM para retornar conceitos previsíveis
- Criação de arquivos de entrada/saída temporários
- Verificação de que o fluxo segue o caminho correto baseado nas entradas do usuário
- Testes de diferentes combinações de escolhas do usuário (bypass, seleção de número, entrada customizada)
- Verificação de que arquivos de saída são criados corretamente

### test_generation_flow.py
Testa o fluxo completo de geração de capítulos (pipeline de geração do livro).

#### Áreas de Cobertura
- Reset de arquivos de capítulo quando `--from-scratch` é usado
- Geração modular por beats (quando outline tem beats definidos)
- Geração de capítulo completo (quando outline não tem beats definidos)
- Execução de agentes críticos em paralelo (canon, style, flow)
- Síntese sequencial de críticas
- Avaliação do capítulo resultante
- Validação de continuidade global
- Commit, push e atualização de estado no Git
- Tratamento de tentativas múltiplas e fallback para melhor tentativa

#### Técnicas de Teste
- Mocking extensivo de:
  - `AgentFactory` e criação de agentes
  - Chamadas ao LLM para cada fase do processo
  - Funções de avaliação (`evaluate_chapter`)
  - Script de continuidade (`verify_continuity.py`)
  - Operações de sistema de arquivos e Git
- Criação de estruturas de diretório de teste com arquivos de referência necessários
- Verificação de que o fluxo segue a sequência correta de operações
- Testes de diferentes caminhos (modular por beats vs capítulo completo)
- Verificação de que tentativas múltiplas são executadas conforme configurado
- Testes de tratamento de falhas (continuidade falha, score abaixo do threshold, etc.)

### test_typeset.py
Testa a funcionalidade de tiposetagem (diretório `/typeset/`).

#### Áreas de Cobertura
- Geração de arquivos LaTeX a partir de capítulos markdown
- Criação de metadata EPUB
- Geração de arquivos de estilo CSS para EPUB
- Integração com pandoc e outras ferramentas de conversão
- Validação de arquivos de saída gerados
- Tratamento de diferentes estruturas de capítulo

#### Técnicas de Teste
- Criação de arquivos de capítulo markdown temporários
- Mocking de chamadas a ferramentas externas (pandoc, etc.) quando apropriado
- Verificação de que arquivos de saída são criados com estrutura esperada
- Testes de diferentes configurações de tiposetagem
- Verificação de que metadata contém informações corretas

### test_language_support.py
Testa suporte a múltiplos idiomas do sistema.

#### Áreas de Cobertura
- Detecção do idioma ativo baseado em `AUTOBOOK_LANGUAGE`
- Carregamento de prompts do idioma correto com fallback para inglês
- Funcionalidade de `prompt_loader.py`
- Integração com o módulo LLM para aplicação de diretivas de idioma
- Testes de diferentes configurações de idioma
- Verificação de que o sistema funciona corretamente quando arquivos de idioma específico estão ausentes

#### Técnicas de Teste
- Manipulação de variáveis de ambiente (`AUTOBOOK_LANGUAGE`)
- Criação de estruturas de diretório de prompt temporárias com diferentes idiomas
- Verificação de que o carregamento de prompt segue as regras de fallback corretas
- Testes de diferentes combinações de disponibilidade de arquivos de prompt
- Verificação de que diretivas de idioma são aplicadas corretamente às chamadas ao LLM

### test_integration.py
Testa integração entre componentes principais do sistema.

#### Áreas de Cobertura
- Fluxo completo de ideação → fundação → geração → revisão
- Passagem de estado entre pipelines através de `state.json` e `book_data/`
- Integração entre geração de capítulos e avaliação
- Funcionalidade de commit e push no Git em múltiplos pontos
- Tratamento de erros em cascata entre componentes
- Verificação de que o sistema pode recuperar de falhas intermediárias

#### Técnicas de Teste
- Mocking seletivo de componentes externos (LLM, Git, etc.) enquanto mantém integração interna
- Criação de cenários de teste que exercem múltiplos componentes em sequência
- Verificação de que estado é passado corretamente entre pipelines
- Testes de diferentes combinações de sucesso/falha em componentes intermediários
- Verificação de que o sistema termina em estado consistente

### Testes Legados (`/legacy/tests`)
Esses testes mantêm compatibilidade com funcionalidade mais antiga e podem ser eventualmente migrados ou substituídos.

#### test_batch_generators_unit.py
Testa geradores em lote para diferentes aspectos do livro.

#### test_ideation_unit.py
Testa funções unitárias relacionadas à ideação.

#### test_pipeline_control.py
Testa mecanismos de controle e orquestração de pipeline.

#### test_draft_chapter_unit.py
Testa geração de capítulos em nível unitário.

#### test_foundation_generators_unit.py
Testa geradores específicos para componentes de fundação.

#### test_seed_unit.py
Testa funcionalidade relacionada ao arquivo `seed.txt`.

#### test_editorial.py
Testa funcionalidade específica do sistema de revisão editorial.

## Estratégias de Mock e Isolamento

### Mocking de Chamadas ao LLM
A maioria dos testes usa mocking extensivo para evitar chamadas reais a APIs externas:

#### Usando `responses` library
```python
@responses.activate
def test_llm_call():
    responses.add(
        responses.POST,
        "https://api.anthropic.com/v1/messages",
        json={"content": [{"text": "Resposta de teste"}]},
        status=200
    )
    # Testa chamada ao LLM
```

#### Usando `unittest.mock.patch`
```python
with patch('llm.os.environ') as mock_env:
    mock_env.get.return_value = "test-api-key"
    # Testa função que depende de variáveis de ambiente
```

#### Mocking de Funções Internas
```python
with patch('module.function_to_mock') as mock_func:
    mock_func.return_value = "valor de teste"
    # Testa código que chama a função mockada
```

### Mocking de Operações de Sistema de Arquivos
```python
# Usando temporary directories e arquivos
with tempfile.TemporaryDirectory() as tmpdir:
    # Cria arquivos de teste no diretório temporário
    test_file = Path(tmpdir) / "test.txt"
    test_file.write_text("conteúdo de teste")
    # Testa funções que usam o arquivo
```

#### Usando `unittest.mock.mock_open`
```python
with patch("builtins.open", mock_open(read_data="conteúdo de teste")) as mock_file:
    # Testa função que lê de arquivo
    result = function_that_reads_file()
    assert result == "conteúdo de teste"
```

### Mocking de Operações de Git
```python
with patch("modulo_em_teste.git_add") as mock_git_add:
    # Testa função que chama git via workspace/git.py
    function_that_uses_git()
    mock_git_add.assert_called_with("arquivo", base_dir=base_dir)
```

Chamadas Git de produção são centralizadas em `workspace/git.py`; testes de
pipelines devem mockar os helpers importados pelo módulo em teste, não
`subprocess.run` global.

## Cobertura de Testes e Melhorias Contínuas

Baseline verificado neste snapshot:

```text
uv run --with pytest pytest tests
301 passed
```

A execução direta de `legacy/tests` é ignorada via `conftest.py`, resultando em "no tests ran".

### Áreas de Alta Cobertura
1. **Módulo LLM**: Boa cobertura de lógica de seleção de provedor, construção de requisição e tratamento de erros
2. **Módulo de Avaliação**: Boa cobertura de funções de verificação de canon, slop e dimensões narrativas
3. **Carregamento de Prompts**: Boa cobertura de `prompt_loader.py` e fallback de idioma
4. **Pipelines de Ideação e Fundação**: Boa cobertura de fluxos de decisão e geração de conteúdo

### Áreas para Melhoria de Cobertura
1. **Testes de Integração Completa**: Poucos testes que exercem todo o fluxo de ideação → fundação → geração → revisão
2. **Testes de Geração de Capítulo Completo**: Testes que verificam um capítulo completo do início ao fim
3. **Testes de Tiposetagem**: Cobertura poderia ser melhorada para diferentes estruturas de capítulo e opções de saída
4. **Testes de Tratamento de Erros**: Mais testes específicos para diferentes cenários de falha
5. **Testes de Performance**: Testes que verificam que o sistema permanece dentro de limites de desempenho aceitáveis

### Estratégias para Melhoria
1. **Adicionar Testes de Fluxo Completo**: Criar testes que exercem todo o pipeline com mocks seletivos
2. **Aprimorar Mocks de LLM**: Criar mocks mais sofisticados que simulem diferentes cenários de resposta
3. **Expandir Testes de Tiposetagem**: Adicionar testes para diferentes estruturas de entrada e opções de saída
4. **Adicionar Testes de Property-Based Testing**: Usar frameworks como `hypothesis` para testar propriedades em vez de exemplos específicos
5. **Implementar Testes de Mutação**: Usar ferramentas como `mutmut` para identificar áreas de código fracamente testadas
6. **Criar Testes de Fuzz**: Testar entradas inesperadas para melhorar robustez

## Integração com Pipeline de Desenvolvimento

### Execução Automática de Testes
Os testes podem ser integrados em pipelines de CI/CD para:
- Verificar que mudanças não quebram funcionalidade existente
- Garantir que novos recursos funcionam conforme esperado
- Detectar regressões precocemente
- Manter qualidade de código ao longo do tempo

### Exemplos de Integração
#### GitHub Actions
```yaml
name: Test Suite

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-mock responses
    - name: Run tests
      run: pytest -v
```

#### GitLab CI
```yaml
test:
  stage: test
  image: python:3.12
  before_script:
    - pip install pytest pytest-mock responses
  script:
    - pytest -v
```

## Boas Práticas de Testes no Autobook

### 1. Nome Claro e Descritivo
Nomes de funções de teste devem ser descritivos o suficiente para entender o que está sendo testado sem ler o código:
- `test_llm_provider_selection_with_valid_env_vars`
- `test_evaluate_chapter_canon_compliance_with_violation`
- `test_ideaion_pipeline_bypass_when_seed_exists`

### 2. Organização Lógica
Testes relacionados devem estar agrupados:
- Todos os testes de seleção de provedor LLM juntos
- Todos os testes de detecção de slop juntos
- Todos os testes de fluxo de pipeline de ideação juntos

### 3. Uso Adequado de Fixtures
Quando apropriado, usar fixtures do pytest para:
- Configuração comum de estado de teste
- Criação de objetos complexos usados em múltiplos testes
- Limpeza automática de recursos

### 4. Isolamento Adequado
- Testes unitários devem mockar dependências externas
- Testes de integração devem testar interações reais entre componentes internos
- Testes de fluxo completo devem mockar apenas componentes externos verdadeiros (LLM, APIs externas, etc.)

### 5. Legibilidade de Asserções
Asserções devem ser claras sobre o que está sendo verificado:
```python
# Bom
assert result["overall_score"] >= 6.0
assert len(result["canon_compliance"]["violations"]) == 0
assert "delve" not in result["slop"]["tier1_hits"]

# Menos bom
assert result  # O que estamos verificando exatamente?
```

### 6. Cobertura de Caminhos de Execução
Testar tanto caminhos de sucesso quanto de falha:
- Caminho feliz (tudo funciona como esperado)
- Caminhos de erro (entradas inválidas, recursos ausentes, falhas externas)
- Caminhos de limite (valores mínimos/máximos, condições de borda)

## Conclusão

O sistema de testes do Autobook fornece uma base sólida para garantir a confiabilidade e correto funcionamento do sistema de geração de livros literários. Sua implementação demonstra:

1. **Cobertura Abrangente**: Testes cobrem módulos críticos, pipelines principais e funcionalidades de apoio
2. **Isolamento Adequado**: Uso apropriado de mocking para testar unidades isoladamente enquanto testa integrações reais quando necessário
3. **Integração com Práticas de Desenvolvimento**: Estrutura que suporta execução frequente durante desenvolvimento e integração em pipelines de CI/CD
4. **Escalabilidade**: Fácil adicionar novos testes para novos recursos ou aprimorar existentes
5. **Foco em Qualidade**: Testes que verificam não apenas se o código funciona, mas se ele produz saída de qualidade aceitável

O design permite que desenvolvedores façam alterações com confiança de que funcionalidades existentes não serão quebradas, enquanto fornece uma estrutura para validar que novos recursos funcionam conforme esperado antes de serem mesclados na branch principal.

Para melhorar ainda mais o sistema de testes, recomenda-se:
1. Aumentar a cobertura de testes de fluxo completo
2. Adicionar mais testes de property-based e fuzz testing
3. Expandir testes de tratamento de erros e condições de borda
4. Considerar a adopção de testes de mutação para identificar fraquezas na cobertura
5. Manter e melhorar continuamente à medida que o sistema evolui
