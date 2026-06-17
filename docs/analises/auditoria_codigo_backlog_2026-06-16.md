# Backlog da Auditoria Senior de Codigo

Data: 2026-06-16

Este backlog deriva de `auditoria_codigo_2026-06-16.md`. Ele serve como base
para montar as proximas specs de implementacao. Os itens nao devem ser
executados todos de uma vez; a prioridade sugerida e remover riscos funcionais
primeiro e so depois atacar organizacao ampla.

> Atualizacao pos-auditoria: os Pacotes 1 e 2 ja trataram C01, C02, A01, A02
> e a parte operacional de C03. Ainda restam decisoes de produto sobre exemplos,
> docs historicas e futuras refatoracoes maiores, mas os prompts/codigo
> operacional principal nao estao mais presos a uma obra especifica.

## Legenda

- Critica: quebra fluxo, induz resultado incorreto ou contradiz premissa
  central do projeto.
- Alta: risco relevante de manutencao, qualidade ou operacao.
- Media: melhoria importante, mas nao bloqueia uso controlado.
- Baixa: higiene, consistencia ou reducao de ruido.

## Itens Acionaveis

| ID | Severidade | Area | Arquivos principais | Acao recomendada | Criterio de aceite |
| --- | --- | --- | --- | --- | --- |
| C01 | Critica | Continuidade | `resolve_continuity.py`, `verify_continuity.py` | Reescrever ou aposentar `resolve_continuity.py`; remover `main()` duplicado; corrigir caminho do relatorio; trocar chamada inexistente a `run_editorial.py` por fluxo suportado. | Teste unitario/integracao cobrindo leitura de `logs/eval_logs/continuity_report.json` e chamada correta da revisao editorial, ou documento marcando script como legado fora de uso. |
| C02 | Critica | Foundation | `pipelines/foundation.py`, `docs/others/CRAFT.md` | Corrigir caminho de `CRAFT.md` ou mover o craft para prompt/config oficial. | Teste falha se craft obrigatorio nao for encontrado; pipeline usa conteudo real do arquivo. |
| C03 | Critica | Genericidade | `foundation.py`, `evaluate.py`, `gen_audiobook_script.py`, `book_data/` | Separar referencias de obra especifica do framework. | Nenhum prompt/rubrica operacional generico contem nomes, tecnologias ou regras de mundo de uma obra concreta, salvo em fixtures ou exemplos explicitamente marcados. |
| C04 | Critica | Workspace | `book_data/`, `workspace/*`, docs | Decidir se `book_data/` e fixture versionada ou workspace de obra. | Politica documentada e aplicada por `.gitignore`, exemplo separado ou fixtures de teste. |
| A01 | Alta | Entrypoint | `main.py`, `run.py` | Remover ou transformar `main.py` em delegador para `run.main()`. | Executar `uv run python main.py` nao imprime mensagem falsa; ou arquivo nao existe mais. |
| A02 | Alta | Testes legados | `legacy/tests/*`, `legacy/*` | Corrigir imports ou excluir formalmente a coleta legacy. | `pytest` nao falha se alguem roda suite completa esperada; docs dizem como executar legado, se suportado. |
| A03 | Alta | Avaliacao | `evaluate.py` | Dividir god module em pacote de avaliacao. | Modulos menores com responsabilidades separadas; suite cobre avaliacao mecanica, judge e reports. |
| A04 | Alta | Foundation | `pipelines/foundation.py`, `prompts/` | Externalizar prompts longos de foundation. | Prompts de foundation vivem em `prompts/{LANG}/foundation/` com teste de placeholders. |
| A05 | Alta | Git | `pipeline*_steps/*`, `workspace/branching.py` | Criar adaptador Git unico e substituir chamadas diretas dispersas. | Todas as chamadas Git passam por uma camada testada; politicas de erro sao consistentes. |
| A06 | Alta | Ideation | `pipelines/ideation.py`, `cli/wizard.py` | Remover `input()` direto da pipeline; receber respostas por contexto/config. | Pipeline pode rodar em modo nao interativo em teste; wizard segue sendo a camada interativa. |
| A07 | Alta | LLM | `llm.py`, callers | Trocar `sys.exit` por excecoes tipadas. | Pipelines conseguem capturar falha LLM; CLI ainda retorna codigo 1 com mensagem amigavel. |
| A08 | Alta | Agentes | `agent_system/*`, `agents.py` | Definir estrategia de migracao do legado: adapter permanente ou migracao completa. | Documento/contrato claro; nenhum acesso direto novo a `_agents_registry`. |
| A09 | Alta | Fallbacks | `context.py`, `prompt_loader.py`, `foundation_steps/context.py` | Classificar inputs como obrigatorios ou opcionais e remover fallbacks silenciosos perigosos. | Outline/foundation essenciais ausentes geram erro claro ou exigem flag explicita de degradacao. |
| M01 | Media | Wizard | `cli/wizard.py` | Extrair apresentacao, selecao, branch/workspace e execucao para helpers. | `wizard.py` fica majoritariamente orquestrador; testes continuam cobrindo fluxos. |
| M02 | Media | Logging | `run.py` | Substituir `Tee` global por logging/contexto controlado. | Streams globais nao ficam reembrulhados; logs seguem em `logs/pipeline.log`. |
| M03 | Media | Prompts | `evaluate.py`, `verify_continuity.py`, `gen_brief.py`, `gen_revision.py` | Mover prompts operacionais restantes para `prompts/`. | Testes validam carregamento e placeholders dos novos prompts. |
| M04 | Media | Structured output | `evaluate.py`, `verify_continuity.py`, parsing | Criar utilitario comum de JSON/reparo de saida LLM. | Duplicacao removida e comportamento padronizado. |
| M05 | Media | Revisao | `book_generation_steps/revision.py` | Ordenar criticas pela ordem declarada de `critics_roles`. | Teste prova que sintese usa ordem configurada, nao ordem alfabetica acidental. |
| M06 | Media | Feedback | `writing/feedback.py`, `critique.py` | Evoluir criticas para saida estruturada real. | Cada critico gera lista de achados com severidade, quote e instrucao validaveis. |
| M07 | Media | Workspace | `workspace/project.py` | Validar `branch` com `is_book_branch` e `created_at` como ISO. | `load_workspace_metadata` rejeita branch invalida e data invalida. |
| M08 | Media | Tooling | `pyproject.toml` | Adicionar dependencias dev e ferramentas de qualidade em modo gradual. | `uv run pytest` ou grupo dev documentado; ruff/mypy opcionais configurados sem bloquear tudo inicialmente. |
| M09 | Media | Docs | `README.md`, `docs/*` | Marcar docs historicos e alinhar README a comandos suportados. | README nao contem caminhos `doc/` antigos nem fluxo "do zero" incompleto. |
| B01 | Baixa | Higiene | varios scripts | Remover imports mortos confirmados. | Suite moderna verde e `git diff --check` limpo. |
| B02 | Baixa | Encoding | scripts raiz, `typeset/` | Padronizar `encoding="utf-8"`. | Leituras/escritas textuais usam encoding explicito. |
| B03 | Baixa | UX | mensagens CLI | Padronizar idioma/acentuacao das mensagens. | Wizard e erros principais usam estilo consistente. |
| B04 | Baixa | Organizacao | scripts raiz | Classificar scripts como suportados, experimentais ou legacy. | Docs e estrutura deixam claro o status de cada script. |

## Pacotes Sugeridos para Execucao

### Pacote 1 - Quebras e ruido operacional

Escopo:

- C01 `resolve_continuity.py`;
- C02 `CRAFT.md`;
- A01 `main.py`;
- A02 `legacy/tests`;
- B01 imports mortos obvios.

Por que primeiro: reduz risco de comandos quebrados e confusao para humanos e
modelos automatizados.

### Pacote 2 - Genericidade e estado de obra

Escopo:

- C03 hardcodes de obra;
- C04 politica de `book_data/`;
- M09 ajustes de README/docs relacionados.

Por que depois: exige decisao de produto sobre exemplo versionado versus
workspace real.

### Pacote 3 - Contratos de infraestrutura

Escopo:

- A05 Git adapter;
- A07 excecoes em `llm.py`;
- A09 fallbacks obrigatorios/opcionais;
- M07 workspace metadata.

Por que depois: cria base para evoluir pipelines sem comportamento silencioso.

### Pacote 4 - Refatoracao de qualidade

Escopo:

- A03 `evaluate.py`;
- A04 prompts de foundation;
- M03 prompts restantes;
- M04 JSON estruturado.

Por que depois: e o pacote maior e deve ser feito com specs menores.

### Pacote 5 - UX e operacao

Escopo:

- A06 ideation nao interativa;
- M01 wizard;
- M02 logging;
- B03 mensagens.

Por que depois: melhora ergonomia sem bloquear a correcao de riscos centrais.

### Pacote 6 - Feedback editorial avancado

Escopo:

- A08 agent system;
- M05 ordem dos criticos;
- M06 feedback estruturado.

Por que depois: depende de decisoes sobre arquitetura de agentes e pipeline de
planejamento de producao.

## Observacoes para Delegacao a Modelos Menores

Para modelos medios, prefira prompts por pacote pequeno, com:

- lista fechada de arquivos que podem ser alterados;
- proibicao explicita de refatorar fora do escopo;
- testes obrigatorios;
- resumo final com arquivos alterados, comandos e riscos.

Evite pedir a um modelo medio para resolver de uma vez os pacotes 3, 4 ou 6.
Eles cruzam muitas fronteiras arquiteturais e devem ser quebrados em specs
menores depois de aprovadas as decisoes de alto nivel.
