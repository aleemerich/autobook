# Pacotes Residuais Pos-Refactor - 2026-06-17

Este documento compara o estado atual do codigo com a auditoria registrada em
`docs/analises/auditoria_codigo_2026-06-16.md` e com o backlog derivado em
`docs/analises/auditoria_codigo_backlog_2026-06-16.md`.

Validacao de referencia apos executar o pacote restante:

- Suite moderna: `uv run --with pytest pytest tests -q` -> 320 testes passando.
- Suite legada: permanece desativada por contrato operacional.

## Pacote restante executado

### Pacote 6 - Feedback editorial avancado

Status: concluido para o escopo do backlog atual.

Itens tratados:

- `A08`: o wrapper moderno de `agent_system` deixou de depender diretamente do
  atributo privado `_agents_registry` para validar agentes dinamicos. O legado
  agora expoe metodos publicos minimos (`has_registered_agent` e
  `unregister_agent`) para esse contrato.
- `M05`: a sintese sequencial agora ordena arquivos de critica pela ordem
  declarada em `critics_roles`, preservando fallback alfabetico apenas quando
  nenhuma ordem e informada.
- `M06`: criticas passam a ser convertidas em `CriticReport` estruturado de
  forma real quando vierem como JSON ou listas markdown. Mensagens explicitas
  de ausencia de problemas geram relatorio vazio em vez de um achado artificial.

Arquivos principais alterados:

- `agent_system/factory.py`
- `agents.py`
- `pipelines/book_generation_steps/critique.py`
- `pipelines/book_generation_steps/revision.py`
- testes correspondentes em `tests/`

## Comparativo com a auditoria

| ID | Status atual | Observacao |
| --- | --- | --- |
| A01 | Resolvido | `main.py` atua como delegador para `run.main()`. |
| A02 | Resolvido | `legacy/tests` nao quebra a suite moderna nem a execucao explicita. |
| A03 | Resolvido | `evaluate.py` virou fachada sobre o pacote `evaluation/`. |
| A04 | Resolvido | Prompts de foundation vivem em `prompts/{LANG}/foundation/`. |
| A05 | Resolvido | Chamadas Git centrais passam por `workspace/git.py`. |
| A06 | Resolvido no nucleo | `IdeationPipeline` aceita contexto nao interativo. A ergonomia do wizard ainda pode melhorar. |
| A07 | Resolvido | `llm.py` usa excecoes tipadas para configuracao e propaga falhas. |
| A08 | Resolvido como adapter | A estrategia atual e manter adapter moderno sobre legado. Migracao completa segue opcional. |
| A09 | Resolvido no fluxo principal | Inputs essenciais foram endurecidos; scripts utilitarios ainda merecem limpeza. |
| M01 | Resolvido | `cli/wizard.py` foi decomposto em helpers de apresentacao, branch/workspace, selecao e execucao. |
| M02 | Resolvido | `run.py` usa captura de log escopada e restaura streams globais. |
| M03 | Resolvido no escopo atual | Prompts principais e prompts dos scripts experimentais iniciais foram externalizados. |
| M04 | Resolvido no escopo atual | JSON de avaliacao e scripts experimentais iniciais reutilizam utilitario comum quando aplicavel. |
| M05 | Resolvido | Criticas seguem a ordem declarada em `critics_roles`. |
| M06 | Resolvido incremental | Conversao estruturada existe; proxima melhoria e fazer agentes emitirem JSON nativamente. |
| M07 | Resolvido | `workspace.json` valida branch `autobook/<slug>` e `created_at` ISO. |
| M08 | Resolvido | `pyproject.toml` declara grupo `dev` e `ruff` gradual. |
| M09 | Parcial | Docs operacionais principais foram atualizados; docs historicos continuam como registro. |
| B01 | Parcial | Imports mortos obvios foram limpos; faltam checks automatizados. |
| B02 | Resolvido no escopo atual | Scripts raiz classificados e `typeset/` tiveram encoding explicito nos pontos levantados. |
| B03 | Parcial | CLI principal melhorou, mas mensagens ainda misturam idiomas/acentuacao em scripts perifericos. |
| B04 | Resolvido no escopo atual | Scripts raiz classificados em `docs/scripts/scripts.md`. |

## Novos pacotes recomendados

### Pacote R1 - Tooling e checks graduais

Status: concluido como baseline inicial.

Escopo:

- Adicionar grupo/dev deps ou configuracao minima para `pytest`, `ruff` e, se viavel,
  `mypy` em modo nao bloqueante.
- Configurar regras iniciais de ruff para imports mortos, whitespace e encoding
  sem tentar corrigir todo o projeto de uma vez.
- Documentar comandos de qualidade suportados.

Motivo:

- Fecha `M08`, reduz reincidencia de `B01` e ajuda a controlar `B02`.

### Pacote R2 - Scripts raiz suportados vs experimentais

Status: concluido para o escopo atual. Classificacao inicial criada em
`docs/scripts/scripts.md`; prompts de scripts experimentais movidos para
`prompts/{LANG}/tools/`; parsing JSON comum reutilizado onde aplicavel; encoding
de scripts suportados/experimentais ajustado.

Escopo:

- Classificar scripts raiz em tres grupos: suportado, experimental, legacy.
- Para scripts suportados, padronizar `encoding="utf-8"`, mover prompts restantes
  para `prompts/{LANG}/tools/` e reutilizar utilitarios de JSON quando aplicavel.
- Para scripts experimentais/legacy, documentar status e evitar que entrem em
  expectativas de qualidade da suite principal.

Alvos iniciais:

- `gen_audiobook_script.py`
- `compare_chapters.py`
- `adversarial_edit.py`
- `voice_fingerprint.py`
- `typeset/build_tex.py`

Motivo:

- Fecha o restante de `M03`, `M04`, `B02` e `B04` sem misturar scripts laterais
  com as pipelines principais.

### Pacote R3 - Decomposicao do wizard

Status: concluido.

Escopo:

- Extrair de `cli/wizard.py` helpers de apresentacao, selecao de pipeline,
  preparacao de branch/workspace e execucao.
- Preservar comportamento e testes atuais.
- Opcional: permitir que o wizard monte contexto nao interativo para ideation
  em vez de deixar a pipeline perguntar diretamente.

Motivo:

- Fecha `M01` e melhora a manutencao da principal interface de usuario.

### Pacote R4 - Estrategia final de agentes

Status: concluido como decisao arquitetural atual. O adapter moderno sobre
`agents.py` foi formalizado em `docs/agents/agent-system-strategy.md`.

Escopo:

- Decidir formalmente se `agent_system` sera adapter permanente sobre `agents.py`
  ou se haverá migracao completa das classes legadas.
- Se a escolha for adapter permanente, estabilizar o contrato publico e evitar
  novas dependencias sobre detalhes internos do legado.
- Se a escolha for migracao completa, mover classes para `agent_system/` em fases
  pequenas e manter `agents.py` como compatibilidade.

Motivo:

- `A08` esta operacionalmente resolvido, mas ainda existe decisao arquitetural
  de longo prazo.

### Pacote R5 - Feedback estruturado nativo

Status: concluido incrementalmente. Prompts dos criticos principais agora
preferem JSON no contrato `CriticReport`, enquanto o parser mantem fallback para
markdown e texto livre.

Escopo:

- Atualizar prompts dos criticos para preferirem JSON com schema de `CriticReport`.
- Manter compatibilidade com markdown como fallback.
- Adicionar validacao de severidade, quote e instruction antes de gerar
  `RevisionPlan`.

Motivo:

- O pacote 6 estruturou a ingestao. Este pacote fecha a producao nativa de
  feedback estruturado e reduz ambiguidade dos modelos.

## Estado Final da Rodada

Os pacotes `R1` a `R5` foram executados no escopo definido aqui. O que resta
nao e bloqueio do refactor: sao decisoes futuras sobre promover ou arquivar
scripts experimentais, adicionar testes dedicados para esses scripts caso virem
contrato suportado, e eventualmente expandir o `ruff` para a pasta `tests/` e
para `gen_brief.py`.
