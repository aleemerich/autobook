# Caso De Uso E2E: Livro Do Zero Com Autobook

Este documento registra uma execucao real end-to-end do Autobook, assumindo o
papel de um usuario que deseja criar uma obra curta do zero. Ele sera mantido
atualizado durante o processo para permitir retomada caso a sessao seja
interrompida.

## Estado Da Execucao

| Campo | Valor |
| --- | --- |
| Data de inicio | 2026-06-18 |
| Branch inicial | `main` |
| Branch da obra | `autobook/a-cidade-que-esquecia-nomes` |
| Titulo da obra | `A Cidade que Esquecia Nomes` |
| Idioma configurado | `PT-BR` |
| Genero configurado | `high_tension_speculative_thriller` |
| Provider configurado | `openrouter` |
| Modelo writer configurado | `openrouter/owl-alpha` |
| Estado atual | Capitulos 1, 2 e 3 gerados; capitulos 2 e 3 revisados pela pipeline editorial; continuidade final aprovada com score `9.2/10`. |

## Premissa Criativa Usada

- Genero/estilo: suspense especulativo literario em cidade pequena brasileira.
- Centelha: uma cidade onde as pessoas perdem o proprio nome quando mentem sobre o passado.
- Custo especulativo: cada mentira apagada remove uma memoria afetiva ligada ao nome perdido.
- Protagonista: uma escriva do cartorio local que falsificou o registro do irmao desaparecido.

## Passo 1 - Abrir O Wizard

Comando:

```bash
uv run python run.py
```

Resultado observado:

- O wizard abriu corretamente.
- Detectou `main`.
- Informou ausencia de workspace registrado.
- Recomendou criar branch de obra.

## Passo 2 - Criar Branch De Obra Pelo Wizard

Entradas usadas:

```text
Deseja preparar uma branch de obra agora? [s/N]: s
Titulo ou slug da obra: A Cidade que Esquecia Nomes
Criar esta branch agora? [s/N]: s
```

Resultado observado:

- Branch criada: `autobook/a-cidade-que-esquecia-nomes`.
- Workspace registrado em `book_data/workspace.json`.
- Template `voice.md` inicializado em `book_data/`.
- Estado do projeto exibiu semente ausente, fundacao incompleta e nenhum capitulo gerado.

## Passo 3 - Iniciar Ideation Pelo Wizard

Entradas usadas:

```text
Escolha uma opcao: 1
Executar do zero? [s/N]: s
Executar agora? [s/N]: s
```

O wizard chamou o comando equivalente:

```bash
python run.py --pipeline ideation --from-scratch
```

## Passo 4 - Responder O Questionario De Ideacao

Entradas usadas:

```text
Genero/Estilo: Suspense especulativo literario em cidade pequena brasileira
Centelha criativa: Uma cidade onde as pessoas perdem o proprio nome quando mentem sobre o passado
Custo especulativo: Cada mentira apagada remove uma memoria afetiva ligada ao nome perdido
Protagonista: Uma escriva do cartorio local que falsificou o registro do irmao desaparecido
```

## Passo 5 - Gerar Conceitos Com LLM

Resultado observado:

- A primeira tentativa sem timeout curto ficou presa por latencia excessiva e
  foi interrompida.
- A execucao foi retomada com `AUTOBOOK_LLM_TIMEOUT=180`.
- O LLM retornou tres conceitos.
- Foi escolhido o conceito `1`: `O LIVRO DOS SEM NOME`.

## Passo 6 - Gerar Misterio Central

Entrada usada:

```text
Deseja gerar a Bíblia de Mistérios (MYSTERY.md)? [S/N] (default: N): S
```

Resultado observado:

- `book_data/MYSTERY.md` foi criado.
- `book_data/state.json` foi inicializado com:

```json
{
  "chapters_drafted": 0,
  "phase": "foundation",
  "current_focus": "planning"
}
```

## Ponto De Retomada

A execucao esta na branch `autobook/a-cidade-que-esquecia-nomes`, com ideation
concluida. Durante a primeira tentativa de `foundation`, foi identificado que
`seed.txt` continha todos os tres conceitos retornados pelo LLM, apesar da
selecao do conceito 1. O parser de conceitos foi corrigido para aceitar
headings Markdown como `## 1. ...`, e `seed.txt` foi reprocessado com o helper
corrigido.

Proximo passo planejado:

## Passo 7 - Executar Foundation

Comando efetivamente usado apos resolver latencia do writer:

```bash
AUTOBOOK_LLM_TIMEOUT=300 AUTOBOOK_WRITER_MODEL='nvidia/nemotron-3-super-120b-a12b:free' uv run python run.py --pipeline foundation --from-scratch
```

Resultado observado:

- `book_data/world.md` gerado.
- `book_data/characters.md` gerado.
- `book_data/outline.md` gerado.
- `book_data/canon.md` gerado.
- Commit automatico da foundation criado.
- Commit corretivo criado para registrar `state.json` no estado `writing`.

## Passo 8 - Ajustar Escopo Para Novela Curta

O outline gerado tinha 14 capitulos visiveis e recomendacao textual ainda maior.
Para concluir o E2E com custo controlado, o usuario revisou a fundacao e
constrangeu `book_data/outline.md` para uma novela completa em 3 capitulos:

1. A Primeira Letra.
2. O Livro Vivo.
3. O Nome Que Sobra.

Esse ajuste foi commitado na branch da obra com:

```bash
git add --force book_data/outline.md
git commit -m "planning: constrain e2e outline to short novella"
```

## Ponto De Retomada Atual

Proximo passo planejado:

## Passo 9 - Gerar Capitulo 1

Comando usado:

```bash
AUTOBOOK_LLM_TIMEOUT=300 \
AUTOBOOK_WRITER_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_JUDGE_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_REVIEW_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_CRITICS='canon_critic' \
uv run python run.py --pipeline book_generation --from-scratch --chapter 1-3
```

Resultado observado para o capitulo 1:

- Dois beats gerados.
- `canon_critic` executado.
- Sintese sequencial executada.
- Avaliacao precisou de dois ciclos porque a primeira resposta nao veio como JSON puro.
- Score final: `7.0`.
- Continuidade aprovada apos correcao do parser PT-BR.
- Commit criado: `ch01: score 7.0 (attempt 1)`.
- O push remoto falhou por ausencia de upstream e foi corrigido no adaptador Git.

## Ponto De Retomada Atual

Proximo passo planejado:

1. Executar `book_generation --chapter 2-3` sem `--from-scratch`.
2. Preservar `chapters/ch_01.md` e `book_data/state.json` com `chapters_drafted: 1`.
3. Verificar criacao de `chapters/ch_02.md` e `chapters/ch_03.md`.
4. Criar `book_data/editorial.md` com uma revisao curta.
5. Executar `editorial_revision`.
6. Rodar checks finais e completar a documentacao do caso de uso.

## Passo 10 - Retomar Capitulo 2 Apos Interrupcao Parcial

Uma primeira tentativa de gerar os capitulos 2 e 3 materializou
`chapters/ch_02.md` e arquivos em `logs/generation_attempts/ch02_attempt01/`,
mas a sessao foi encerrada durante a avaliacao. Como `book_data/state.json`
permaneceu com `chapters_drafted: 1`, o estado oficial ainda aponta que o
proximo capitulo valido a gerar e o 2.

Comando de retomada:

```bash
AUTOBOOK_LLM_TIMEOUT=300 \
AUTOBOOK_WRITER_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_JUDGE_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_REVIEW_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_CRITICS='canon_critic' \
uv run python run.py --pipeline book_generation --chapter 2-3
```

Resultado observado:

- Capitulo 2 foi reprocessado.
- Tentativa 1 recebeu `raw_judge_score: 8.0`, mas caiu para `overall_score: 4.4`
  por penalidade mecanica de slop e foi descartada.
- Tentativa 2 recebeu score `7.0`, passou continuidade e foi commitada:
  `ch02: score 7.0 (attempt 2)`.
- Capitulo 3 precisou de duas tentativas.
- Tentativa 2 recebeu score `6.0`, passou continuidade e foi commitada:
  `ch03: score 6.0 (attempt 2)`.
- `book_data/state.json` terminou com:

```json
{
  "chapters_drafted": 3
}
```

## Passo 11 - Corrigir Problemas Observados No Avaliador

Durante as avaliacoes dos capitulos 2 e 3 foram identificados dois problemas
tecnicos:

1. O avaliador nao encontrava entradas de outline com heading `Capítulo`.
2. Modelos medios frequentemente retornavam raciocinio antes do JSON, causando
   falhas de parse e ciclos extras.

Antes de continuar para a revisao editorial, foram corrigidos:

- `evaluate.py`, para reconhecer headings `Ch`, `Chapter`, `Capitulo` e
  `Capítulo`.
- `evaluation/json_utils.py`, para escolher o ultimo objeto JSON valido com a
  chave obrigatoria quando a resposta contem texto explicativo antes do JSON.

Validacao executada:

```bash
uv run --with pytest pytest tests/test_evaluate_unit.py tests/test_logging.py -q
```

Resultado: `13 passed`.

## Passo 12 - Preparar Revisao Editorial Pontual

O Capitulo 3 foi aceito pelo pipeline, mas a avaliacao detectou a palavra em
ingles `inside` dentro da prosa:

```text
Ele bateu o inside da bochecha...
```

Esse problema sera tratado com `editorial_revision` usando `book_data/editorial.md`
e foco nos capitulos 2 e 3.

## Passo 13 - Executar Primeira Revisao Editorial

Arquivo criado:

```text
book_data/editorial.md
```

Comando usado:

```bash
AUTOBOOK_LLM_TIMEOUT=300 \
AUTOBOOK_WRITER_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_JUDGE_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_REVIEW_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
NUM_EDITORIAL_RETRIES=2 \
uv run python run.py --pipeline editorial_revision --chapter 3
```

Resultado observado:

- O parser semantico de `editorial.md` funcionou e encontrou o brief do
  Capitulo 3.
- A pipeline removeu temporariamente `inside da bochecha`.
- A avaliacao automatica considerou as tentativas piores que o baseline e
  reverteu o capitulo original.
- A manutencao final executou continuidade e obteve score `8.5/10`.
- Foi detectado ruido operacional: chamada a `legacy/build_outline.py`, que
  esta incompativel com a estrutura moderna.

Conclusao operacional:

- O usuario nao deve editar `chapters/*.md` manualmente para corrigir a obra.
- A tentativa de correcao manual feita durante o E2E foi revertida com
  `Revert "editorial: fix ch03 language and timeline"`.
- O residuo `inside da bochecha`, a ambiguidade temporal e qualquer outro erro
  textual devem ser tratados por melhoria de pipeline/script, nao por patch
  direto no manuscrito.
- O E2E demonstrou uma falha real: `editorial_revision` consegue tentar a
  correcao, mas pode reverter a mudanca quando a avaliacao automatica considera
  a tentativa pior que o baseline.

## Passo 14 - Corrigir Manutencao Final Editorial

`run_final_maintenance()` foi ajustada para nao chamar `legacy/build_outline.py`
quando a estrutura legada esperada nao existir. No fluxo moderno, a etapa final
continua executando `verify_continuity.py`.

Validacao especifica:

```bash
uv run --with pytest pytest tests/test_editorial_revision_steps.py tests/test_evaluate_unit.py tests/test_logging.py -q
```

Resultado: `35 passed`.

## Passo 15 - Endurecer Revisao Editorial Para Rodada Real

Antes de nova tentativa, foram corrigidos problemas sistemicos observados:

- `evaluation/slop.py` e `prompts/PT-BR/slop.json` passaram a penalizar termos
  residuais de outro idioma, como `inside`.
- `pipelines/editorial_revision.py` passou a restaurar o texto original caso a
  revisao falhe depois de escrever uma tentativa no disco.
- `prompts/PT-BR/gen_revision_user.txt` e `prompts/EN/gen_revision_user.txt`
  receberam um contrato de escopo para revisoes locais.
- `pipelines/editorial_revision_steps/revision.py` recebeu diretrizes
  corretivas mais conservadoras.
- `evaluation/judge.py` e os prompts de avaliacao receberam contrato explicito
  de saida JSON.
- `evaluation/json_utils.py` passou a truncar logs de respostas invalidas para
  evitar despejos gigantes no terminal.
- `gen_revision.py` passou a calcular um orçamento de palavras baseado no
  rascunho existente, e a pipeline passou a rejeitar tentativas que violem
  muito esse orçamento antes de gastar nova avaliacao LLM.

Validacao focada executada:

```bash
uv run --with pytest pytest tests/test_editorial_revision_steps.py tests/test_prompt_genericity.py tests/test_evaluate_unit.py tests/test_evaluation_judge.py -q
```

Resultado: `54 passed`.

## Passo 16 - Revisar Capitulo 2 Pela Pipeline

Comando usado:

```bash
AUTOBOOK_LLM_TIMEOUT=300 \
AUTOBOOK_WRITER_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_JUDGE_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_REVIEW_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
NUM_EDITORIAL_RETRIES=1 \
uv run python run.py --pipeline editorial_revision --chapter 2
```

Resultado observado:

- Baseline do Capitulo 2: `6.0`, slop `1.0`.
- A primeira reescrita ficou com `1404` palavras, sem expansao exagerada.
- O corretivo ficou com `1192` palavras.
- A pipeline manteve a melhor versao disponivel e criou o commit:
  `editorial: revised ch02 (6.0 -> 6.0)`.
- A continuidade global final da rodada ficou em `9.0/10.0`.

Observacao: mesmo sem ganho numerico, o commit foi produzido pela propria
pipeline. Nao houve edicao manual do capitulo.

## Passo 17 - Revisar Capitulo 3 Pela Pipeline

Comando usado:

```bash
AUTOBOOK_LLM_TIMEOUT=300 \
AUTOBOOK_WRITER_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_JUDGE_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
AUTOBOOK_REVIEW_MODEL='nvidia/nemotron-3-super-120b-a12b:free' \
NUM_EDITORIAL_RETRIES=1 \
uv run python run.py --pipeline editorial_revision --chapter 3
```

Resultado observado:

- Baseline do Capitulo 3: `4.0`, slop `3.0`.
- Uma tentativa inicial expandiu para `5319` palavras e recebeu score `0`.
- O corretivo posterior voltou a tamanho controlado (`1589` palavras) e recebeu
  score `7.0`, slop `1.0`.
- A pipeline criou o commit:
  `editorial: revised ch03 (4.0 -> 7.0)`.
- A continuidade global final ficou em `9.2/10.0`.

## Estado Final Do E2E

O fluxo completo foi executado com sucesso suficiente para documentacao:

1. Wizard criou branch de obra e workspace.
2. Ideation gerou conceitos e misterio.
3. Foundation gerou biblias.
4. Book generation gerou 3 capitulos e commits automaticos.
5. Editorial revision revisou capitulos 2 e 3 por pipeline.
6. Continuidade final aprovou a obra com score `9.2/10.0`.

Pontos tecnicos ainda relevantes para evolucao:

- O avaliador ainda pode raciocinar antes do JSON, exigindo ciclos extras.
- Modelos economicos podem gerar latencia alta.
- Revisoes locais precisam de guardrails mecanicos de tamanho, ja adicionados
  apos o E2E revelar a expansao indevida.
