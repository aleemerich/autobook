# Plano de Implementação: Fase 00 - Criação de Especificações

Este plano detalha a criação das especificações técnicas (specs) para a Fase 00 do refatoramento da plataforma Autobook, sem realizar qualquer alteração em arquivos de código Python.

## Proposta de Ações

Criaremos 8 arquivos de especificações na pasta `docs/planejamento/refactor-plataforma/` e atualizaremos a tabela de arquivos no índice central `docs/INDICE.md`.

Cada arquivo de especificação seguirá estritamente a seguinte estrutura obrigatória:
1. **Objetivo** (Goal/Purpose)
2. **Fora de Escopo** (Out of Scope)
3. **Estado Atual** (Current State)
4. **Comportamento Desejado** (Desired Behavior)
5. **Arquivos Afetados** (Affected Files)
6. **Testes Necessários** (Required Tests)
7. **Critérios de Aceite** (Acceptance Criteria)
8. **Perguntas Abertas** (Open Questions)

---

## Detalhamento dos Arquivos

### 1. `00-decisao.md` (Contexto e Decisão Arquitetural)
- **Objetivo**: Registrar a decisão arquitetural e o contexto para o refatoramento híbrido (agentes estáveis + plano de produção dinâmico).
- **Estado Atual**: Configurações rígidas de outline (ex: 22 capítulos), prompts longos e gerais, e falta de verificação estruturada de continuidade.

### 2. `01-run-entrypoint.md` (Ponto de Entrada `run.py`)
- **Objetivo**: Redirecionar `run.py` sem argumentos para um wizard CLI interativo, preservando o parser atual para quando houver parâmetros.
- **Estado Atual**: `run.py` exige `--pipeline` obrigatoriamente e falha sem argumentos.

### 3. `02-pipeline-contract.md` (Contrato de Pipeline, Registry e Discovery)
- **Objetivo**: Definir o contrato base de metadados de pipelines (`requires`, `produces`), o registro (`registry.py`) e a camada de descoberta de estado do projeto (`discovery.py`).
- **Estado Atual**: Sem metadados estruturados de dependência; imports estáticos de pipelines em `run.py`.

### 4. `03-branch-workflow.md` (Workflow de Git Branch por Obra)
- **Objetivo**: Criar utilitários para isolar a produção de livros em branches `autobook/<slug>`, mantendo `main` limpa.
- **Estado Atual**: Livros gerados na branch ativa sem qualquer verificação estruturada.

### 5. `04-agent-registry.md` (Registro e Fábrica de Agentes)
- **Objetivo**: Centralizar agentes em `agent_system/` com registro dinâmico e fábrica, mantendo retrocompatibilidade com `agents.py`.
- **Estado Atual**: `agents.py` na raiz possui código e instanciamento estático e hardcoded de agentes.

### 6. `05-prompt-layout.md` (Layout e Carregamento de Prompts Externos)
- **Objetivo**: Mover prompts hardcoded de agentes para arquivos `prompts/{LANG}/agents/` com fallback para `EN`.
- **Estado Atual**: Prompts de sistema misturados com lógica Python no arquivo `agents.py`.

### 7. `06-feedback-lifecycle.md` (Ciclo de Vida do Feedback)
- **Objetivo**: Definir contrato estruturado de críticas e revisões (`critic_report -> revision_plan -> revised_text`).
- **Estado Atual**: Críticas geradas em Markdown mas sem consumo estruturado sistemático garantido na etapa seguinte.

### 8. `07-migration-plan.md` (Plano de Migração e Decomposição em Subpipelines)
- **Objetivo**: Estruturar a decomposição da pipeline `book_generation` em subpipelines menores e a migração em fases testáveis.
- **Estado Atual**: `book_generation.py` é um script monolítico complexo.

---

## Verificação e Fechamento

Ao final das escritas, executaremos:
- `git diff --check -- docs` para validar espaços em branco/regras do Git.
- `docs/INDICE.md` será atualizado com os links para os novos documentos criados.

## Perguntas Abertas / Feedback Solicitado

1. Há alguma terminologia específica ou restrição de idioma (PT-BR) que você gostaria de ajustar nas especificações?
2. A estrutura dos links de arquivos em markdown segue o padrão do repositório?
