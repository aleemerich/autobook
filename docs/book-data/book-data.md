# Dados do Livro (`book_data/`)

`book_data/` guarda os arquivos de estado, planejamento e referencia usados
pelos pipelines. Eles sao dados de runtime do livro em andamento, nao apenas
documentacao estatica.

## Arquivos

| Arquivo | Gerado/Usado Por | Papel |
| --- | --- | --- |
| `state.json` | `ideation`, `foundation`, `book_generation` | Cursor do pipeline, incluindo `chapters_drafted`, `phase` e `current_focus`. |
| `MYSTERY.md` | `ideation`, `foundation` | Misterio central opcional, usado na construcao do outline. |
| `world.md` | `foundation`, `book_generation`, avaliacao | Biblia de mundo e regras de ambiente. |
| `characters.md` | `foundation`, `book_generation`, avaliacao | Registro de personagens, relacoes e padroes de voz. |
| `outline.md` | `foundation`, `book_generation`, continuidade | Estrutura de capitulos e beats. |
| `canon.md` | `foundation`, `book_generation`, avaliacao | Base de fatos que nao devem ser contraditos. |
| `voice.md` | `foundation`, `book_generation`, avaliacao | Perfil de voz e restricoes estilisticas do livro. |
| `editorial.md` | `editorial_revision`, `resolve_continuity.py` | Briefs de revisao geral e por capitulo. |
| `workspace.json` | Wizard, scripts auxiliares | Metadados locais da obra, incluindo titulo e branch `autobook/<slug>`. |
| `audiobook_cast.json` | `gen_audiobook_script.py` | Elenco opcional de vozes/personagens para parsing de roteiro de audiobook. |

## Ciclo De Vida

1. `ideation` cria `seed.txt`, opcionalmente `MYSTERY.md`, e inicializa `state.json`.
2. `foundation` le `seed.txt`, `MYSTERY.md` e `voice.md`; gera `world.md`, `characters.md`, `outline.md` e `canon.md`.
3. `book_generation` le `outline.md`, `world.md`, `characters.md`, `canon.md` e `voice.md`; escreve capitulos e atualiza `state.json`.
4. `editorial_revision` le `editorial.md` e capitulos existentes; reescreve os capitulos indicados.
5. `evaluate.py` e `verify_continuity.py` leem esses dados para gerar scores e diagnosticos.

## Contratos Praticos

- `outline.md` precisa conter headers de capitulo no formato reconhecido pelos parsers, como `### Ch 1: Titulo`, em sequencia continua a partir de 1.
- `book_generation` nao usa mais fallback fixo para quantidade de capitulos; se nenhum header reconhecivel for encontrado, a execucao falha com erro explicito.
- `world.md`, `characters.md`, `canon.md` e `voice.md` sao entradas obrigatorias para `book_generation`; arquivos ausentes interrompem o fluxo em vez de entrar como contexto vazio.
- `book_generation` procura a secao `**Beats:**` para gerar cenas modularmente; sem beats, cai no fallback de capitulo inteiro.
- `state.json` controla de onde a geracao sequencial continua.
- `editorial.md` pode conter diretrizes gerais e secoes por capitulo; o parser semantico tenta converter isso para JSON e tem fallback regex.
- `workspace.json` e opcional, mas quando existe deve seguir o schema validado por `workspace/project.py`: `schema_version` 1, `title`, branch no formato `autobook/<slug>` e `created_at` em ISO 8601.
- `audiobook_cast.json` e opcional. Quando ausente, o roteiro de audiobook usa apenas um narrador generico; quando presente, deve ser um objeto JSON `{ "SPEAKER": "descricao de voz" }`.

## Riscos v0

- `book_data/` e a area de trabalho da obra. Em branches principais deve conter apenas placeholders/contratos genericos; artefatos reais devem ser gerados em branches `autobook/<slug>`.
- Alterar manualmente `state.json` pode fazer o pipeline pular ou sobrescrever capitulos.
- `foundation.py` procura a referência de craft no caminho correto `docs/others/CRAFT.md`.
