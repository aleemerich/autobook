# E2E - Problemas Encontrados E Resolvidos

Este documento registra problemas reais observados durante a execucao
end-to-end do Autobook e como cada um foi analisado/resolvido.

## Problema 1 - Chamada LLM Da Ideation Ficou Presa Por Tempo Excessivo

### Onde Ocorreu

- Branch: `autobook/a-cidade-que-esquecia-nomes`
- Comando iniciado pelo wizard: `python run.py --pipeline ideation --from-scratch`
- Step: `GenerateConceptsStep`
- Modelo: `openrouter/owl-alpha`
- Provider: `openrouter`

### Sintoma

A chamada exibiu:

```text
[LLM] Requesting model 'openrouter/owl-alpha' from provider 'openrouter' (Attempt 1/3)...
[LLM] Waiting for API response (timeout: 3600s)...
```

Depois disso, a execucao ficou aguardando por mais de 90 segundos sem novo
output. A sessao foi interrompida manualmente com `Ctrl+C`.

### Analise

O stack trace indicou que a conexao HTTP tinha sido aberta e o processo estava
aguardando leitura do corpo da resposta (`ssl.py` / `httpcore`). Isso sugere
latencia alta, resposta lenta do provider/modelo ou bloqueio no caminho de rede,
nao uma falha imediata de configuracao.

O timeout efetivo veio de `AUTOBOOK_PIPELINE_TIMEOUT=3600`, porque
`AUTOBOOK_LLM_TIMEOUT` nao estava definido. Para uso interativo, uma espera de
ate 1 hora por chamada e ruim: o usuario nao recebe feedback acionavel e o
processo fica dificil de supervisionar.

### Decisao

Continuar usando os modelos configurados no `.env`, conforme autorizado, mas
definir `AUTOBOOK_LLM_TIMEOUT` apenas na execucao E2E para limitar chamadas
individuais e permitir retry/falha controlada.

### Resolucao Planejada

Retomar a ideation com:

```bash
AUTOBOOK_LLM_TIMEOUT=180 uv run python run.py
```

Se o provider retornar dentro desse limite, o fluxo continua normalmente. Se
falhar, o problema sera reavaliado com base no erro concreto retornado.

### Resultado

Resolvido para a execucao E2E. A chamada de geracao de conceitos retornou
dentro do timeout de 180s. A geracao de `MYSTERY.md` tambem concluiu dentro do
mesmo limite.

## Problema 2 - `uv run` Com Variavel De Ambiente Falhou No Sandbox

### Onde Ocorreu

Ao tentar relancar o wizard com:

```bash
AUTOBOOK_LLM_TIMEOUT=180 uv run python run.py
```

### Sintoma

O comando falhou com:

```text
error: Could not acquire lock
  Caused by: Could not create temporary file
  Caused by: Read-only file system (os error 30)
```

### Analise

O `uv` tentou criar arquivo temporario no cache global fora das raizes gravaveis
do sandbox. O problema nao era do Autobook nem do fluxo de usuario; era uma
restricao do ambiente de execucao do agente.

### Resolucao

O mesmo comando foi relancado com permissao elevada para permitir o uso normal
do cache do `uv`. O wizard abriu corretamente na branch de obra e retomou o
fluxo com o workspace registrado.

## Problema 3 - Selecao De Conceito Salvou Todos Os Conceitos Em `seed.txt`

### Onde Ocorreu

- Pipeline: `ideation`
- Step: `SelectConceptStep`
- Entrada do usuario: escolha `1`

### Sintoma

Mesmo escolhendo o conceito 1, `seed.txt` ficou com a introducao e os tres
conceitos retornados pelo LLM. O arquivo ficou com 2.562 palavras.

### Analise

O LLM retornou conceitos com headings Markdown:

```text
## 1. O LIVRO DOS SEM NOME
## 2. ARQUIVO MORTO
## 3. A CIDADE QUE NAO LEMBRA
```

O parser `parse_numbered_concepts()` aceitava apenas linhas iniciadas por
`1.`, `2.`, `3.`. Como nao reconheceu `## 1.`, caiu no fallback de salvar o
texto completo.

Esse bug teve efeito operacional importante: a foundation passou a receber uma
semente muito maior e semanticamente ambigua, aumentando custo, latencia e risco
de gerar biblias inconsistentes.

### Resolucao

Foi corrigido `pipelines/ideation_steps/selection.py` para aceitar headings
Markdown opcionais e marcadores `1.` ou `1)`.

Tambem foi adicionado teste de regressao em `tests/test_ideation_steps.py`.

Validacao executada:

```bash
uv run --with pytest pytest tests/test_ideation_steps.py -q
```

Resultado: `7 passed`.

Depois da correcao, `seed.txt` foi reprocessado com o proprio helper corrigido
e passou a conter apenas o conceito 1, com 756 palavras.

## Problema 4 - Foundation Travou Em `characters.md` Apos Semente Ambigua

### Onde Ocorreu

- Pipeline: `foundation`
- Step: `GenerateCharactersStep`
- Modelo: `openrouter/owl-alpha`

### Sintoma

`world.md` foi gerado, mas a chamada de `characters.md` ficou aguardando leitura
do corpo da resposta por varios minutos. A execucao foi interrompida com
`Ctrl+C`.

### Analise

O problema ocorreu depois de `world.md` ter sido gerado a partir da semente
errada, que continha todos os conceitos. A entrada para `characters.md` incluia
seed grande + world grande, o que aumentou o prompt e provavelmente agravou a
latencia.

### Resolucao Planejada

Refazer `foundation --from-scratch` apos a correcao de `seed.txt`. Se o
problema persistir, avaliar troca temporaria para outro modelo ja configurado
no `.env` apenas para a execucao E2E.

### Resultado Parcial

Mesmo com `seed.txt` reduzido para 756 palavras, a chamada de `world.md` voltou
a ficar presa por varios minutos. Isso indica que a latencia principal esta no
modelo writer configurado (`openrouter/owl-alpha`) para prompts longos, nao
apenas na semente ambigua.

### Resolucao Atual

Retomar a foundation usando temporariamente:

```bash
AUTOBOOK_WRITER_MODEL=nvidia/nemotron-3-super-120b-a12b:free
AUTOBOOK_LLM_TIMEOUT=300
```

Esse modelo ja esta presente no `.env` como `AUTOBOOK_REVIEW_MODEL`, portanto a
execucao continua dentro do conjunto de modelos configurados para o projeto,
sem alterar `.env` permanentemente.

### Resultado

Resolvido para o E2E. Com o writer temporario alternativo, `world.md`,
`characters.md`, `outline.md` e `canon.md` foram gerados.

## Problema 5 - Commit Da Foundation Deixou `state.json` Modificado

### Onde Ocorreu

- Pipeline: `foundation`
- Step: `CommitFoundationStep`

### Sintoma

Depois da foundation concluir e criar o commit automatico, `git status` mostrou:

```text
 M book_data/state.json
```

### Analise

O step fazia commit dos artefatos antes de chamar `write_foundation_state()`.
Assim, o commit registrava o estado anterior e o cursor correto de escrita
ficava apenas no working tree.

### Resolucao

`CommitFoundationStep` foi alterado para escrever `state.json` antes de chamar
`commit_foundation_artifacts()`.

Foi adicionado teste que valida que `state.json` ja esta no estado correto no
momento do `git_commit`.

Validacao executada:

```bash
uv run --with pytest pytest tests/test_foundation_pipeline.py tests/test_foundation_steps.py tests/test_ideation_steps.py -q
```

Resultado: `38 passed`.

Para a execucao atual, foi criado um commit corretivo apenas de
`book_data/state.json`.

## Problema 6 - `book_generation` Nao Reconheceria Headings `Capítulo`

### Onde Ocorreu

- Arquivo gerado: `book_data/outline.md`
- Parser: `pipelines/book_generation_steps/context.py`

### Sintoma

A foundation gerou headings em PT-BR no formato:

```text
### Capítulo 1 – ...
```

O parser de `book_generation` reconhecia apenas `### Ch N` e
`### Chapter N`. Isso faria a geracao falhar antes do primeiro capitulo.

### Resolucao

O parser foi ampliado para reconhecer `Capítulo` e `Capitulo`, alem de `Ch` e
`Chapter`. Tambem passou a aceitar `:`, `-` e `–` na extracao de titulo.

Teste adicionado:

```bash
uv run --with pytest pytest tests/test_book_generation_context.py tests/test_foundation_pipeline.py tests/test_ideation_steps.py -q
```

Resultado: `31 passed`.

## Problema 7 - Outline Gerado Era Grande Demais Para O E2E

### Sintoma

O outline gerado indicava escala de romance longo e continha 14 capitulos
visiveis, extrapolando o escopo de teste combinado para uma obra curta.

### Analise

Isso nao e falha tecnica da pipeline, mas e uma decisao de produto importante:
para um E2E de documentacao e custo controlado, o usuario precisa revisar a
fundacao antes de iniciar a escrita e ajustar o escopo da obra quando necessario.

### Resolucao

`book_data/outline.md` foi manualmente reduzido para uma novela completa em 3
capitulos, preservando formato reconhecido pelo parser e secoes `**Beats:**`.

O ajuste foi commitado na branch da obra.

## Problema 8 - `verify_continuity.py` Tambem Nao Reconhecia `Capítulo`

### Onde Ocorreu

- Pipeline: `book_generation`
- Apos avaliacao do Capitulo 1
- Script chamado pelo pipeline: `verify_continuity.py`

### Sintoma

O Capitulo 1 recebeu score `8.0`, mas a continuidade falhou com:

```text
[ERROR] Failed to parse any chapters from outline.md.
```

Com isso, o pipeline iniciou uma nova tentativa do capitulo mesmo tendo um
rascunho avaliado positivamente.

### Analise

O parser interno de `book_generation_steps/context.py` ja havia sido corrigido
para aceitar `Capítulo`, mas `verify_continuity.py` tinha um parser proprio que
aceitava apenas `### Ch N:` e `### Chapter N:`.

Tambem faltava suporte a campos em PT-BR como `Resumo`, `Local` e
`Personagens`.

### Resolucao

`verify_continuity.parse_outline()` foi atualizado para aceitar:

- `Ch`
- `Chapter`
- `Capitulo`
- `Capítulo`

Tambem passou a aceitar separadores `:`, `-` e `–`, e campos `Resumo`, `Local`
e `Personagens`.

Teste adicionado em `tests/test_continuity.py`.

Validacao executada:

```bash
uv run --with pytest pytest tests/test_continuity.py tests/test_book_generation_context.py -q
```

Resultado: `22 passed`.

## Problema 9 - `git push` Falhou Em Branch De Obra Sem Upstream

### Onde Ocorreu

- Pipeline: `book_generation`
- Apos Capitulo 1 passar avaliacao e continuidade
- Funcao: `workspace.git.git_push()`

### Sintoma

O capitulo foi commitado, mas o pipeline falhou no push:

```text
fatal: The current branch autobook/a-cidade-que-esquecia-nomes has no upstream branch.
```

### Analise

O wizard cria uma branch local `autobook/<slug>`, mas nao configura upstream
remoto. Em um fluxo de usuario local, isso nao deveria impedir a geracao: o
commit local e suficiente para preservar progresso, e o push pode ser feito
depois com `git push --set-upstream`.

Falhas reais de push, como erro de autenticacao ou remoto indisponivel, ainda
devem continuar visiveis.

### Resolucao

`workspace.git.git_push()` foi ajustado para tratar especificamente mensagens de
branch sem upstream como no-op nao bloqueante. Outros erros continuam levantando
`GitCommandError`.

Teste adicionado em `tests/test_workspace_git.py`.

Validacao executada:

```bash
uv run --with pytest pytest tests/test_workspace_git.py tests/test_book_generation_persistence.py tests/test_continuity.py tests/test_book_generation_context.py -q
```

Resultado: `39 passed`.

## Problema 10 - Interrupcao Durante Avaliacao Deixou Capitulo Parcial No Disco

### Onde Ocorreu

- Pipeline: `book_generation`
- Comando: `run.py --pipeline book_generation --chapter 2-3`
- Capitulo: `2`

### Sintoma

A sessao longa foi encerrada durante a avaliacao do Capitulo 2. Ao retomar a
auditoria do estado, existia `chapters/ch_02.md` e havia arquivos em
`logs/generation_attempts/ch02_attempt01/`, mas `book_data/state.json` ainda
indicava:

```json
{
  "chapters_drafted": 1
}
```

Tambem nao havia `evaluation.json` para o Capitulo 2 nem commit automatico.

### Analise

O pipeline salva o texto final tentativo e arquiva artefatos antes de completar
a avaliacao, atualizar estado e criar commit. Isso e positivo para depuracao,
mas cria um estado intermediario quando a execucao e interrompida no meio do
fluxo.

O estado oficial continua correto: como `chapters_drafted` permaneceu em `1`,
uma retomada com `--chapter 2-3` reprocessa o Capitulo 2. O arquivo parcial
existente sera sobrescrito pelo novo ciclo.

### Resolucao Planejada

Retomar a geracao com o mesmo comando de capitulos 2-3, sem `--from-scratch`,
tratando `state.json` como fonte de verdade:

```bash
AUTOBOOK_LLM_TIMEOUT=300 \
AUTOBOOK_WRITER_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_JUDGE_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_REVIEW_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_CRITICS='canon_critic' \
uv run python run.py --pipeline book_generation --chapter 2-3
```

### Resultado

A retomada funcionou. O Capitulo 2 foi reprocessado, avaliado com score `7.0`,
passou na continuidade global e recebeu commit automatico.

## Problema 11 - Avaliacao De Capitulos Em PT-BR Perdia Outline E Falhava Com JSON Verboso

### Onde Ocorreu

- Modulo: `evaluate.py`
- Modulo: `evaluation/json_utils.py`
- Durante avaliacao dos capitulos 2 e 3.

### Sintoma

O avaliador frequentemente retornou raciocinio textual antes do JSON final.
Quando isso acontecia, a etapa de reparo podia falhar ou cair em reconstrucao
por regex. Alem disso, `evaluate.py` procurava o outline do capitulo apenas com
headings em ingles (`### Ch N`), entao outlines em PT-BR com
`### Capítulo N` chegavam ao juiz como:

```text
(outline entry not found)
```

### Analise

Isso prejudica duas partes importantes do fluxo:

- O juiz perde o contrato narrativo especifico do capitulo quando o outline
  esta em PT-BR.
- Modelos medios/baratos que explicam antes do JSON causam ciclos extras de
  avaliacao, aumentando custo e tempo.

### Resolucao

`evaluate.py` recebeu `extract_chapter_outline_entry()`, que reconhece:

- `Ch`
- `Chapter`
- `Capitulo`
- `Capítulo`

`evaluation/json_utils.py` passou a varrer todos os objetos JSON balanceados da
resposta e preferir o ultimo objeto valido que contenha a chave obrigatoria
(`overall_score` ou `continuity_score`), antes de cair no fallback por regex.

Testes adicionados em `tests/test_evaluate_unit.py`.

Validacao executada:

```bash
uv run --with pytest pytest tests/test_evaluate_unit.py tests/test_logging.py -q
```

Resultado: `13 passed`.

## Problema 12 - Capitulo 3 Aceito Ainda Continha Palavra Em Ingles

### Onde Ocorreu

- Arquivo: `chapters/ch_03.md`
- Avaliacao final do Capitulo 3.

### Sintoma

O Capitulo 3 foi aceito com score final `6.0`, mas a propria avaliacao apontou
residuo de idioma:

```text
inside da bochecha
```

### Analise

O texto passou no limiar minimo porque a penalidade mecanica reduziu
`raw_judge_score: 7` para `overall_score: 6.0`. Ainda assim, uma palavra em
ingles dentro da prosa PT-BR viola a expectativa de idioma e precisa ser
corrigida por revisao editorial.

### Resolucao Planejada

Criar `book_data/editorial.md` com instrucao especifica para o Capitulo 3 e
executar `editorial_revision --chapter 3`.

### Resultado

A pipeline editorial removeu temporariamente o termo em ingles, mas reverteu o
capitulo porque a avaliacao automatica considerou as tentativas piores que o
baseline.

Durante a execucao, foi feita uma correcao manual indevida nos artefatos da
obra. Essa acao foi revertida com o commit:

```text
Revert "editorial: fix ch03 language and timeline"
```

Estado correto da analise: o problema permanece aberto para o sistema. O usuario
nao deve corrigir `chapters/*.md` diretamente; o ajuste precisa vir de melhoria
em `editorial_revision`, nos prompts/briefs editoriais, ou em uma etapa
automatizada de saneamento textual.

## Problema 13 - Manutencao Final Editorial Chamava Script Legado Incompativel

### Onde Ocorreu

- Pipeline: `editorial_revision`
- Funcao: `run_final_maintenance()`
- Script chamado: `legacy/build_outline.py`

### Sintoma

Ao fim da pipeline editorial, o processo chamou `legacy/build_outline.py`, que
falhou com:

```text
FileNotFoundError: ... /legacy/characters.md
```

### Analise

O script legado calcula sua base como a pasta `legacy/` e espera uma estrutura
antiga (`legacy/characters.md`, `legacy/chapters/`). Essa estrutura nao existe
no fluxo atual, que usa `book_data/characters.md` e `chapters/` na raiz.

Como `subprocess.run()` era chamado sem `check=True`, a falha nao derrubava a
pipeline, mas gerava ruido operacional e podia confundir o usuario.

### Resolucao

`run_final_maintenance()` foi ajustada para chamar `legacy/build_outline.py`
somente quando o conjunto legado minimo existir:

- `legacy/build_outline.py`
- `legacy/characters.md`
- `legacy/chapters/`

No fluxo moderno, a manutencao final segue rodando `verify_continuity.py`.

Testes adicionados/ajustados em `tests/test_editorial_revision_steps.py`.

Validacao executada:

```bash
uv run --with pytest pytest tests/test_editorial_revision_steps.py tests/test_evaluate_unit.py tests/test_logging.py -q
```

Resultado: `35 passed`.

## Problema 14 - Revisao Editorial Podia Deixar Capitulo Parcial Apos Falha

### Onde Ocorreu

- Pipeline: `editorial_revision`
- Capitulo: `2`
- Situacao: avaliacao falhou depois de `gen_revision.py` sobrescrever o arquivo
  do capitulo.

### Sintoma

Uma execucao editorial falhou com erro fatal de avaliacao, mas deixou
`chapters/ch_02.md` modificado no working tree.

### Analise

O step carregava o texto original, executava a reescrita e so depois avaliava.
Se a avaliacao falhasse, o arquivo ja tinha sido sobrescrito. Isso e ruim para
um usuario humano porque o sistema deixa um manuscrito nao validado no disco.

### Resolucao

`pipelines/editorial_revision.py` passou a tratar cada capitulo como uma
transacao:

- carrega `original_text` antes da tentativa;
- restaura o original em qualquer excecao;
- remove arquivos temporarios no `finally`.

Teste adicionado em `tests/test_editorial_revision_steps.py`.

## Problema 15 - Prompts De Revisao Local Expandiam Demais O Capitulo

### Onde Ocorreu

- Script: `gen_revision.py`
- Prompts: `prompts/*/gen_revision_user.txt`
- Capitulo: `3`

### Sintoma

Mesmo com brief pedindo correcao local, uma tentativa de revisao gerou
`5319` palavras para um capitulo originalmente em torno de `1576` palavras.

### Analise

O prompt dizia para devolver o capitulo completo, mas nao fornecia um orçamento
de palavras verificavel. Modelos medios interpretaram "capitulo completo" como
permissao para reescrever e expandir.

### Resolucao

Foram adicionadas duas camadas:

- `gen_revision.py` calcula um orçamento de palavras a partir do rascunho
  existente e injeta isso no prompt.
- `editorial_revision` rejeita mecanicamente tentativas muito menores ou muito
  maiores que o original antes de gastar avaliacao LLM.

Testes adicionados em `tests/test_prompt_genericity.py` e
`tests/test_editorial_revision_steps.py`.

## Problema 16 - Avaliador Continuou Raciocinando Antes Do JSON

### Onde Ocorreu

- Modulo: `evaluation/judge.py`
- Prompts: `prompts/EN/evaluation/chapter*.txt`
- Avaliacoes editoriais dos capitulos 2 e 3.

### Sintoma

Mesmo quando o prompt pedia JSON, o modelo frequentemente retornava analise em
prosa antes do objeto. Isso causou ciclos extras e aumentou bastante o tempo de
execucao.

### Resolucao Parcial

Foram adicionados contratos explicitos:

- o primeiro caractere deve ser `{`;
- o ultimo caractere deve ser `}`;
- qualquer observacao deve estar dentro dos campos do JSON.

`evaluation/json_utils.py` tambem passou a truncar logs de respostas invalidas
para evitar despejos gigantes no terminal.

### Status

Parcialmente resolvido. O ruido de log caiu, mas o modelo ainda pode ignorar o
contrato e exigir ciclos extras. Uma evolucao futura recomendada e criar um
modo de avaliacao ainda mais curto/estruturado para modelos baratos.

## Problema 17 - Penalidade De Idioma Nao Barrava Residuos Em Ingles

### Onde Ocorreu

- Modulo: `evaluation/slop.py`
- Configuracao: `prompts/PT-BR/slop.json`
- Capitulo: `3`

### Sintoma

O texto continha `inside da bochecha`, mas a penalidade mecanica nao tratava
termos residuais de outro idioma como problema critico configuravel.

### Resolucao

`prompts/PT-BR/slop.json` ganhou a lista
`language_hygiene.foreign_language_terms`, e `evaluation/slop.py` passou a
computar `foreign_language_hits` e penalizar esses termos.

`format_eval_feedback()` passou a destacar esses residuos como:

```text
TERMOS DE OUTRO IDIOMA encontrados na prosa
```

Teste adicionado em `tests/test_evaluate_unit.py`.

## Resultado Final Da Rodada E2E

Depois dos ajustes, o fluxo editorial conseguiu revisar os capitulos 2 e 3 por
pipeline, sem edicao manual de `chapters/*.md`:

- Capitulo 2: commit `editorial: revised ch02 (6.0 -> 6.0)`.
- Capitulo 3: commit `editorial: revised ch03 (4.0 -> 7.0)`.
- Continuidade final: `9.2/10.0`.

Pendencia tecnica principal: reduzir custo e instabilidade do juiz quando usado
com modelos medios que tendem a raciocinar antes do JSON.
