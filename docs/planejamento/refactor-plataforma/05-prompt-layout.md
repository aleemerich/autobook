# 05 - Prompt Layout and Loader Spec

## Objetivo
Especificar a migração e organização de prompts do Autobook, movendo prompts que estão hardcoded nas classes de agentes para arquivos de texto estruturados na pasta `prompts/{LANG}/agents/`, estabelecendo regras de fallback automático de idiomas e migração gradual.

## Fora De Escopo
- Alterar o texto, semântica ou comportamento lógico dos prompts existentes no projeto durante o processo de extração física.
- Migrar todos os agentes do sistema simultaneamente (a migração de prompts deve ocorrer de maneira isolada e controlada por agente/papel).

## Estado Atual
Atualmente, a maioria dos prompts de sistema e templates de instrução utilizados pelos agentes literários e críticos estão declarados diretamente no código-fonte Python do arquivo `agents.py` como strings estáticas. Essa abordagem impede a localização ágil (traduções de idioma) e dificulta a manutenção dos templates de prompts.

## Comportamento Desejado
- **Layout Físico de Arquivos:** Os prompts de sistema de cada agente serão armazenados em:
  - `prompts/EN/agents/<role>.txt` (idioma de fallback base)
  - `prompts/PT-BR/agents/<role>.txt` (idioma principal do projeto local)
- **Fallback Automático de Idiomas:** O carregador de prompts (`prompt_loader.py` ou utilitário equivalente sob `agent_system`) deve buscar o prompt no idioma configurado para o livro (ex: `PT-BR`). Caso o arquivo correspondente não seja encontrado naquele subdiretório, o sistema deve automaticamente buscar e carregar o arquivo correspondente em `EN` como fallback seguro.
- **Fallback Estático Temporário:** Durante a fase de transição de cada agente, se o arquivo não estiver presente em nenhum diretório físico de prompts, o sistema poderá fazer fallback para a string hardcoded existente no código Python para manter a continuidade operacional.
- **Preservação de Semântica:** Durante a migração física das strings de prompt de código para os arquivos `.txt`, os textos devem ser copiados exatamente como são, sem alteração de conteúdo ou comportamento semântico.

## Arquivos Afetados Futuramente
- `prompt_loader.py`
- `agent_system/` (ou utilitário de carregamento integrado)
- [NEW] `prompts/EN/agents/` (e arquivos txt correspondentes)
- [NEW] `prompts/PT-BR/agents/` (e arquivos txt correspondentes)
- [NEW] `tests/test_agent_prompts.py`

## Contratos De Entrada
- Identificador de idioma (ex: `"PT-BR"`, `"EN"`) e identificador do papel do agente (ex: `"drafting"`, `"critic_style"`).

## Contratos De Saida
- String de prompt do sistema carregada e pronta para interpolação pelo LLM client.

## Testes Necessarios
1. **Carregamento Principal:** Validar carregamento do prompt no idioma correto quando o arquivo `.txt` existe na pasta de destino.
2. **Fallback de Idioma:** Apagar ou simular ausência do prompt em `PT-BR` e validar que o loader recupera o prompt de `EN`.
3. **Fallback para Hardcoded:** Validar que, em caso de ausência física total do arquivo (ex: durante a fase de transição gradual), o agente continua operando com o prompt hardcoded default definido em Python.
4. **Erro Controlado:** Retornar erro legível de execução caso um prompt obrigatório não seja encontrado em nenhuma das origens (nem físico nem hardcoded).

## Criterios De Aceite
- Os agentes migrados recuperam seus prompts de forma transparente dos arquivos de texto.
- Sem regressão na qualidade literária dos textos gerados (visto que a semântica do prompt foi integralmente preservada).
- Todos os testes da suite moderna continuam passando.

## Perguntas Abertas
- Como unificar a sintaxe de templates de variáveis dinâmicas (ex: uso de `{world}` ou `{{world}}`) nos arquivos de texto de prompts externos?
