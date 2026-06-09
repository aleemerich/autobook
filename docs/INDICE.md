# Documentação Completa do Autobook

## Índice Geral

Este conjunto de documentos descreve completamente o sistema **Autobook** — um pipeline multi-agente autônomo para escrita, revisão, diagramação, ilustração e narração de livros completos usando inteligência artificial.

---

### 1. Arquitetura Geral
- [Visão Geral da Arquitetura](architecture/visao-geral.md)
- [Padrão Command/Composite](architecture/command-composite.md)
- [Fluxo de Dados Principal](architecture/fluxo-dados.md)
- [Injeção de Dependências e Configuração](architecture/dependencias-config.md)

### 2. Pipelines (Orquestração)
- [Pipeline de Ideação](pipelines/ideation.md)
- [Pipeline de Fundação](pipelines/foundation.md)
- [Pipeline de Geração do Livro](pipelines/book-generation.md)
- [Pipeline de Revisão Editorial](pipelines/editorial-revision.md)
- [Comparação entre Pipelines](pipelines/comparacao.md)

### 3. Sistema de Agentes
- [Visão Geral dos Agentes](agents/visao-geral.md)
- [AgentFactory — Fábrica de Agentes](agents/factory.md)
- [DraftingAgent — Agente de Rascunho](agents/drafting.md)
- [StylistAgent — Agente de Estilo](agents/stylist.md)
- [TechnicalEditorAgent — Editor Técnico](agents/technical-editor.md)
- [CanonCriticAgent — Crítico de Canon](agents/canon-critic.md)
- [StyleCriticAgent — Crítico de Estilo](agents/style-critic.md)
- [FlowCriticAgent — Crítico de Fluxo](agents/flow-critic.md)
- [SynthesisAgent — Agente de Síntese](agents/synthesis.md)
- [CustomLocalizerAgent — Localizador Customizado](agents/custom-localizer.md)

### 4. Cliente LLM Unificado
- [Visão Geral do llm.py](llm/visao-geral.md)
- [Provedores Suportados](llm/provedores.md)
- [Resolução de Modelos](llm/resolucao-modelos.md)
- [Retry, Backoff e Failover](llm/retry-failover.md)
- [Timeouts e Configurações](llm/timeouts.md)

### 5. Sistema de Prompts e Localização
- [Prompt Loader](prompts/prompt-loader.md)
- [Estrutura de Diretórios de Prompts](prompts/estrutura-diretorios.md)
- [Prompts por Idioma (PT-BR/EN)](prompts/idiomas.md)
- [Configuração Anti-Slop](prompts/anti-slop.md)
- [Diretivas de Linguagem](prompts/diretivas-linguagem.md)
- [Continuidade e Regras de Divergência](prompts/continuidade.md)
- [Templates de Revisão](prompts/templates-revisao.md)

### 6. Estratégia de Gênero
- [GenreStrategy — Padrão Strategy](genre-strategy/estrategia.md)
- [Gêneros Disponíveis](genre-strategy/generos.md)
- [Carregamento com Fallback](genre-strategy/fallback.md)
- [Extração de Padrões Anti-Slop](genre-strategy/anti-patterns.md)

### 7. Avaliação e Qualidade
- [Evaluate.py — Harness de Avaliação](evaluation/evaluate.md)
- [Detecção Mecânica de Slop](evaluation/slop-mecanico.md)
- [Juiz LLM (LLM Judge)](evaluation/llm-juiz.md)
- [Métricas e Scores](evaluation/metricas.md)
- [Logs de Avaliação](evaluation/logs.md)

### 8. Verificação de Continuidade
- [Verify Continuity](continuity/verify-continuity.md)
- [Resolve Continuity](continuity/resolve-continuity.md)
- [Parse de Outline](continuity/parse-outline.md)
- [Relatórios de Continuidade](continuity/relatorios.md)

### 9. Testes
- [Visão Geral dos Testes](tests/visao-geral.md)
- [Testes de Continuidade](tests/test-continuity.md)
- [Testes de Avaliação](tests/test-evaluate.md)
- [Testes de Pipeline de Fundação](tests/test-foundation.md)
- [Testes de Fluxo de Geração](tests/test-generation-flow.md)
- [Testes de Ideação](tests/test-ideation.md)
- [Testes de Integração](tests/test-integration.md)
- [Testes de Linguagem](tests/test-language.md)
- [Testes de LLM](tests/test-llm.md)
- [Testes de Logging](tests/test-logging.md)
- [Testes de Typesetting](tests/test-typeset.md)
- [Como Executar os Testes](tests/como-executar.md)

### 10. Configuração e Ambiente
- [Arquivo .env](configuration/env.md)
- [pyproject.toml](configuration/pyproject.md)
- [Variáveis de Ambiente](configuration/variaveis-ambiente.md)
- [Estrutura de Diretórios](configuration/estrutura-diretorios.md)

### 11. Dados do Livro (book_data)
- [Visão Geral](book-data/visao-geral.md)
- [world.md — Bíblia do Mundo](book-data/world.md)
- [characters.md — Registro de Personagens](book-data/characters.md)
- [outline.md — Esquema de Capítulos](book-data/outline.md)
- [canon.md — Base de Fatos](book-data/canon.md)
- [MYSTERY.md — Mistério Central](book-data/mystery.md)
- [voice.md — Perfil de Voz](book-data/voice.md)
- [editorial.md — Instruções de Revisão](book-data/editorial.md)
- [state.json — Estado do Pipeline](book-data/state.md)

### 12. Typesetting e Exportação
- [Visão Geral](typesetting/visao-geral.md)
- [LaTeX/PDF](typesetting/latex.md)
- [EPUB](typesetting/epub.md)
- [Metadados](typesetting/metadados.md)
- [Landing Page](typesetting/landing.md)

### 13. Código Legado (legacy/)
- [Visão Geral](legacy/visao-geral.md)
- [Scripts Principais](legacy/scripts.md)
- [Testes Legados](legacy/testes.md)

### 14. Análise de Qualidade de Código
- [Violações SOLID](quality-analysis/solid.md)
- [Hardcoding e Viés](quality-analysis/hardcoding.md)
- [Padrões de Design Utilizados](quality-analysis/padroes-design.md)
- [Injeção de Dependências](quality-analysis/dependencias.md)
- [Pontos de Melhoria](quality-analysis/melhorias.md)
- [Dívida Técnica](quality-analysis/divida-tecnica.md)

### 15. Skills (Habilidades Extensíveis)
- [create_agent.py](skills/create-agent.md)
- [redundancy_detector.py](skills/redundancy-detector.md)

---

## Como Ler Esta Documentação

### Para Iniciantes (sem experiência em Python)
Comece por: **1. Arquitetura Geral → Visão Geral da Arquitetura** — explica o "o quê" e "porquê" do sistema sem código.

### Para Desenvolvedores
Siga a ordem numérica. Cada documento explica conceitos técnicos com exemplos práticos.

### Para Quem Quer Estender o Sistema
Foque em: **Pipelines**, **Sistema de Agentes**, **Prompts**, **Skills** e **Análise de Qualidade**.

---

## Convenções de Nomenclatura

| Termo | Significado |
|-------|-------------|
| **Pipeline** | Sequência de passos (steps) que executam uma tarefa macro |
| **Step** | Passo atômico individual dentro de um pipeline |
| **Agente** | Classe que encapsula uma persona de LLM com prompt de sistema específico |
| **LLM** | Large Language Model — modelo de linguagem grande (GPT, Claude, Gemini, etc.) |
| **Prompt de Sistema** | Instruções fixas que definem o comportamento do agente |
| **Prompt de Usuário** | Entrada dinâmica enviada ao agente para uma tarefa específica |
| **Slop** | Padrões de escrita que denunciam texto gerado por IA (clichês, palavras proibidas, estrutura rígida) |
| **Canon** | Conjunto de fatos estabelecidos que não podem ser contraditos |
| **Beat** | Unidade narrativa mínima — uma cena ou momento específico do capítulo |
| **Try-Fail Cycle** | Padrão narrativo: o personagem tenta algo e falha (ou consegue mas com consequência) |

---

## Estado Atual do Projeto

- **Branch principal**: `main` — framework agnóstico, sem referências a livros específicos
- **Branches de livros**: `autobook/a-prova-final`, `autobook/a-prova-final2`, `autobook/o-bug-em-nos`
- **Testes**: 60 testes passando (baseline)
- **Python**: ≥ 3.12
- **Gerenciador de dependências**: `uv`

---

## Próximos Passos Sugeridos

1. Ler [Visão Geral da Arquitetura](architecture/visao-geral.md)
2. Entender os [Pipelines](pipelines/ideation.md)
3. Estudar o [Sistema de Agentes](agents/visao-geral.md)
4. Revisar [Análise de Qualidade](quality-analysis/solid.md) para contribuir com melhorias

---

*Documentação gerada automaticamente a partir do código-fonte. Última atualização: jul/2026.*