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
| Cliente LLM | Boa | `llm.py` cobre provedores, modelos, retry, timeout e erros de configuracao tipados. |
| Prompts e idioma | Boa | `prompt_loader.py` e `prompts/{EN,PT-BR}` estao documentados. |
| Pipelines | Parcial | Fluxos principais existem, mas alguns detalhes estao desatualizados. |
| Avaliacao | Boa | `evaluate.py` permanece como fachada/CLI; o pacote `evaluation/` separa slop mecanico, juiz LLM, prompts, JSON e reports. |
| Typeset | Parcial | `typeset/build_tex.py` gera LaTeX; PDF/EPUB final dependem de ferramentas externas. |
| Testes | Boa | Baseline moderno confirmado: 309 testes em `tests/`. |
| Legacy | Parcial | Scripts existem; testes legados foram desativados e ignorados na suíte moderna. |

## Correcoes Importantes Para v0

- O indice antigo apontava para dezenas de arquivos granulares que nao existem. O novo indice aponta para a estrutura real.
- O baseline correto de testes modernos e `309 passed` em `tests/`, nao a suite completa incluindo `legacy/tests`.
- `legacy/tests` foi desativado e excluído da suíte moderna. Seus arquivos são ignorados pelo pytest via conftest.py na pasta.
- `GIT_AUTO_COMMIT` e `GIT_AUTO_PUSH` nao sao flags efetivas no codigo atual. Operacoes Git usadas por pipelines passam pelo adaptador `workspace/git.py`.
- `book_generation` agora falha explicitamente quando `outline.md` nao contem headings reconheciveis de capitulo ou quando arquivos obrigatorios de lore estao ausentes.
- `workspace.json` continua opcional, mas quando presente precisa validar branch `autobook/<slug>` e `created_at` em ISO 8601.
- `book_data/`, `seed.txt` e `chapters/*.md` sao workspace local ignorado na branch principal. Templates versionados ficam em `templates/book_data/`, e pipelines usam add forcado controlado nas branches de obra.
- O fluxo modular de `book_generation` usa `DraftingAgent`, criticos e `SynthesisAgent`. `StylistAgent` e `TechnicalEditorAgent` existem, mas nao sao etapas ativas centrais nesse fluxo.
- `resolve_continuity.py` foi corrigido como loop fechado: a duplicidade de `main()` foi removida, o relatório é lido de `logs/eval_logs/continuity_report.json` e a chamada final é enviada via `run.py`.
- `foundation.py` carrega `CRAFT.md` no caminho correto `docs/others/CRAFT.md` com validação explícita de erro.
- Os prompts operacionais de `foundation.py`, `evaluate.py`, `gen_revision.py`, `gen_audiobook_script.py` e `book_generation_steps/planning.py` nao carregam mais nomes ou regras de uma obra especifica.

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
309 passed
```

Comando tambem testado:

```bash
uv run --with pytest pytest legacy/tests
```

Resultado: `no tests ran` com exit code 0 (excluído e ignorado por configuração).

## Proximas Atualizacoes Recomendadas

1. Monitorar o comportamento de `resolve_continuity.py` sob casos reais de divergência narrativa.
2. Atualizar `legacy/legacy.md` com caminhos reais e status por script.
3. Transformar `docs/others/` em uma area explicitamente historica/criativa.
4. Criar uma pagina dedicada para ferramentas editoriais avancadas.
5. Decidir se `docs/analises/` entra no versionamento como registro oficial da auditoria.
