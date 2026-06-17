# Documentacao do Autobook

Este indice reflete a estrutura real da pasta `docs/` e o estado atual do
codigo na branch em uso. O objetivo deste v0 e servir como snapshot tecnico:
o que existe, o que funciona, o que esta parcial e o que precisa ser
atualizado antes de virar documentacao definitiva.

## Leitura Recomendada

1. [Snapshot v0](SNAPSHOT_V0.md)
2. [Arquitetura](architecture/arquitetura.md)
3. [Pipelines](pipelines/pipelines.md)
4. [Comandos operacionais](operacional/comandos.md)
5. [Dados do livro](book-data/book-data.md)
6. [Testes](tests/tests.md)

## Documentos Principais

| Area | Documento | Status v0 |
| --- | --- | --- |
| Snapshot e lacunas | [SNAPSHOT_V0.md](SNAPSHOT_V0.md) | Atual |
| Arquitetura | [architecture/arquitetura.md](architecture/arquitetura.md) | Coberto, precisa revisao fina |
| Pipelines | [pipelines/pipelines.md](pipelines/pipelines.md) | Coberto, parcialmente desatualizado |
| Fluxo detalhado | [fluxo-detalhado/guia-completo-fluxos.md](fluxo-detalhado/guia-completo-fluxos.md) | Rico, precisa checagem contra codigo |
| Agentes | [agents/agentes.md](agents/agentes.md) | Coberto |
| Cliente LLM | [llm/llm.md](llm/llm.md) | Coberto |
| Prompts e localizacao | [prompts/prompts.md](prompts/prompts.md) | Coberto |
| Generos | [genre-strategy/genre-strategy.md](genre-strategy/genre-strategy.md) | Novo v0 |
| Avaliacao | [evaluation/evaluation.md](evaluation/evaluation.md) | Coberto |
| Continuidade | [continuity/continuity.md](continuity/continuity.md) | Novo v0 |
| Configuracao | [configuration/configuration.md](configuration/configuration.md) | Atualizado para v0 |
| Dados do livro | [book-data/book-data.md](book-data/book-data.md) | Novo v0 |
| Typesetting | [typesetting/typesetting.md](typesetting/typesetting.md) | Coberto, com partes manuais |
| Testes | [tests/tests.md](tests/tests.md) | Atualizado para baseline real |
| Legacy | [legacy/legacy.md](legacy/legacy.md) | Precisa limpeza |
| Qualidade | [quality-analysis/quality-analysis.md](quality-analysis/quality-analysis.md) | Coberto |
| Skills | [skills/skills.md](skills/skills.md) | Novo v0 |
| Comandos | [operacional/comandos.md](operacional/comandos.md) | Novo v0 |
| Planejamento futuro | [planejamento/como-transformar-parecer-em-specs.md](planejamento/como-transformar-parecer-em-specs.md) | Novo v0 |


## Referencias Historicas e Criativas

Os arquivos abaixo sao uteis como material de referencia, mas nao devem ser
lidos como documentacao tecnica atual sem validacao contra o codigo:

- [others/PIPELINE.md](others/PIPELINE.md)
- [others/CRAFT.md](others/CRAFT.md)
- [others/ANTI-SLOP.md](others/ANTI-SLOP.md)
- [others/ANTI-PATTERNS.md](others/ANTI-PATTERNS.md)
- [others/WORKFLOW.md](others/WORKFLOW.md)
- [others/PROJECT_STUDY.md](others/PROJECT_STUDY.md)
- [others/program.md](others/program.md)
- [others/cauldron.txt](others/cauldron.txt)
- [others/results.tsv](others/results.tsv)

## Analises

- [analises/docs_analysis.md](analises/docs_analysis.md): auditoria detalhada da documentacao contra o codigo.
- [analises/analise_arquitetura_autobook.md](analises/analise_arquitetura_autobook.md): proposta de arquitetura e evolucao.
- [analises/recomendacao_pipeline_producao.md](analises/recomendacao_pipeline_producao.md): parecer sobre pipeline intermediaria, agentes dinamicos, continuidade, estilo e modelos de menor custo.
- [analises/auditoria_codigo_2026-06-16.md](analises/auditoria_codigo_2026-06-16.md): auditoria senior do codigo atual, com achados de arquitetura, clean code, riscos funcionais e aderencia a documentacao.
- [analises/auditoria_codigo_backlog_2026-06-16.md](analises/auditoria_codigo_backlog_2026-06-16.md): backlog acionavel derivado da auditoria senior para planejamento das correcoes.

## Estado Atual Verificado

- Entrada principal: `run.py`.
- Pipelines suportados pela CLI: `ideation`, `foundation`, `book_generation`, `editorial_revision`.
- Baseline moderno de testes: `uv run --with pytest pytest tests` com 301 testes passando.
- `legacy/tests` nao faz parte do baseline atual; a coleta e ignorada e retorna sem testes por configuracao local.
- Python: `>=3.12`.
- Gerenciador recomendado: `uv`.
- Provedores LLM suportados em `llm.py`: `anthropic`, `openai`, `gemini`, `openrouter`.
