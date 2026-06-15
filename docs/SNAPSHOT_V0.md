# Snapshot v0 do Autobook

Este documento resume o estado atual do projeto cruzando a pasta `docs/` com
os arquivos reais do repositorio. Ele nao substitui a documentacao detalhada:
serve como ponto de partida confiavel para discutir melhorias.

## Escopo Atual

O Autobook e um orquestrador Python para gerar e revisar livros com LLMs. A
entrada principal e `run.py`, que executa pipelines compostos por `Step`s:

- `ideation`: cria ou preserva `seed.txt`, opcionalmente gera `book_data/MYSTERY.md` e inicializa `book_data/state.json`.
- `foundation`: gera `world.md`, `characters.md`, `outline.md` e `canon.md`.
- `book_generation`: gera capitulos em `chapters/ch_XX.md`, avalia, valida continuidade e atualiza `state.json`.
- `editorial_revision`: interpreta `book_data/editorial.md`, reescreve capitulos e reavalia.

## O Que Esta Coberto

| Assunto | Cobertura | Observacao |
| --- | --- | --- |
| Arquitetura `run.py` + `Step`/`Pipeline` | Boa | O padrao Command/Composite esta correto. |
| Agentes | Boa | `agents.py` define drafting, stylist, technical editor, criticos e synthesis. |
| Cliente LLM | Boa | `llm.py` cobre provedores, modelos, retry e timeout. |
| Prompts e idioma | Boa | `prompt_loader.py` e `prompts/{EN,PT-BR}` estao documentados. |
| Pipelines | Parcial | Fluxos principais existem, mas alguns detalhes estao desatualizados. |
| Avaliacao | Boa | `evaluate.py` combina slop mecanico e juiz LLM. |
| Typeset | Parcial | `typeset/build_tex.py` gera LaTeX; PDF/EPUB final dependem de ferramentas externas. |
| Testes | Boa | Baseline moderno confirmado: 60 testes em `tests/`. |
| Legacy | Parcial | Scripts existem, mas ha caminhos e testes quebrados. |

## Correcoes Importantes Para v0

- O indice antigo apontava para dezenas de arquivos granulares que nao existem. O novo indice aponta para a estrutura real.
- O baseline correto de testes modernos e `60 passed` em `tests/`, nao a suite completa incluindo `legacy/tests`.
- `legacy/tests` falha na coleta por imports de `draft_chapter`, `run_editorial` e `run_pipeline`.
- `GIT_AUTO_COMMIT` e `GIT_AUTO_PUSH` nao sao flags efetivas no codigo atual. `foundation`, `book_generation` e `editorial_revision` executam `git commit` e/ou `git push` diretamente.
- O fluxo modular de `book_generation` usa `DraftingAgent`, criticos e `SynthesisAgent`. `StylistAgent` e `TechnicalEditorAgent` existem, mas nao sao etapas ativas centrais nesse fluxo.
- `resolve_continuity.py` nao esta saudavel como loop fechado: tem `main()` duplicado, caminhos divergentes para o relatorio e chama `run_editorial.py`, arquivo que nao existe.
- `foundation.py` procura `doc/CRAFT.md`, mas a referencia real nesta pasta esta em `docs/others/CRAFT.md`.

## Lacunas Documentais

| Lacuna | Resumo para planejamento |
| --- | --- |
| `book_data/` | Falta contrato formal de cada arquivo de estado e lore. Criado v0 em `book-data/book-data.md`. |
| `genre_strategy.py` e `genres/` | Falta explicar selecao por idioma/genero e fallback. Criado v0 em `genre-strategy/genre-strategy.md`. |
| Continuidade | Faltava pagina dedicada para `verify_continuity.py` e estado real de `resolve_continuity.py`. Criado v0 em `continuity/continuity.md`. |
| Skills | Faltava pagina para `skills/create_agent.py` e `skills/redundancy_detector.py`. Criado v0 em `skills/skills.md`. |
| Comandos | Faltava consolidar CLI principal e scripts auxiliares. Criado v0 em `operacional/comandos.md`. |
| Ferramentas editoriais | `apply_cuts.py`, `adversarial_edit.py`, `compare_chapters.py`, `gen_brief.py` e `voice_fingerprint.py` precisam docs proprios depois do v0. |
| Landing page | `landing/index.html` existe, mas falta documentar como atualizar/publicar. |
| Audiobook/arte | Existem scripts e chaves (`ELEVENLABS_API_KEY`, `FAL_KEY`), mas a automacao e parcial e/ou legacy. |

## Baseline Verificado

Comando executado:

```bash
uv run --with pytest pytest tests
```

Resultado:

```text
60 passed
```

Comando tambem testado:

```bash
uv run --with pytest pytest tests legacy/tests
```

Resultado: falha na coleta de quatro testes legados por modulos ausentes:
`draft_chapter`, `run_editorial` e `run_pipeline`.

## Proximas Atualizacoes Recomendadas

1. Revisar `pipelines/foundation.py` para remover ou documentar hardcodes de historia especifica.
2. Corrigir `resolve_continuity.py` ou marcar oficialmente como ferramenta quebrada.
3. Atualizar `legacy/legacy.md` com caminhos reais e status por script.
4. Transformar `docs/others/` em uma area explicitamente historica/criativa.
5. Criar uma pagina dedicada para ferramentas editoriais avancadas.
6. Decidir se `docs/analises/` entra no versionamento como registro oficial da auditoria.

