# Comandos Operacionais

Este documento lista os comandos que correspondem ao estado atual do codigo.

## Setup

```bash
cp .env.example .env
uv sync
```

Edite `.env` com o provedor e as chaves necessarias. O provedor ativo e
controlado por `AUTOBOOK_PROVIDER`.

## Orquestrador Principal

A entrada principal consolidada é o script `run.py`.

* **Autobook Wizard (Interativo)**:
  Chamar o script sem argumentos inicia o Wizard do console, que analisa o estado atual do projeto, sugere e cria a branch de obra correta, e registra `book_data/workspace.json`.
  ```bash
  uv run python run.py
  ```

* **Modo CLI Clássico (Direto)**:
  Para rodar um pipeline específico diretamente:
  ```bash
  uv run python run.py --pipeline <pipeline>
  ```

Pipelines aceitos (registrados em `pipelines/registry.py`):
```bash
uv run python run.py --pipeline ideation
uv run python run.py --pipeline foundation
uv run python run.py --pipeline book_generation
uv run python run.py --pipeline editorial_revision
```

### Regra de Branches de Obra
Para manter as branches principais `main`/`master` limpas, as pipelines protegidas (`ideation`, `foundation`, `book_generation`, `editorial_revision`) exigem que o código seja executado em uma branch dedicada no formato `autobook/<slug>`.

Opcoes comuns:

```bash
uv run python run.py --pipeline book_generation --from-scratch --yes
uv run python run.py --pipeline book_generation --chapter 1
uv run python run.py --pipeline book_generation --chapter 1-3,5
uv run python run.py --pipeline editorial_revision --chapter 4
```

Observacoes:

- `--from-scratch` remove capitulos existentes e reinicia o estado quando usado no pipeline de geracao.
- `--chapter` aceita numeros e intervalos separados por virgula.
- A execucao grava logs em `logs/pipeline.log`.
- Alguns pipelines executam `git add`, `git commit` e `git push` diretamente.

## Avaliacao

```bash
uv run python evaluate.py --phase=foundation
uv run python evaluate.py --chapter=5
uv run python evaluate.py --full
```

Os logs de avaliacao sao gravados em `logs/eval_logs/`.

## Continuidade

```bash
uv run python verify_continuity.py
uv run python verify_continuity.py --strict --threshold 7.0
```

`resolve_continuity.py` existe, mas nao deve ser tratado como fluxo fechado
confiavel neste v0: ele chama `run_editorial.py`, que nao existe mais.

## Revisao e Edicao Avancada

```bash
uv run python gen_revision.py <chapter_num> <brief_path>
uv run python adversarial_edit.py <chapter_num>
uv run python adversarial_edit.py all
uv run python apply_cuts.py <chapter_num>
uv run python apply_cuts.py all --dry-run
uv run python compare_chapters.py <chapter_a> <chapter_b>
uv run python compare_chapters.py
uv run python gen_brief.py --auto
uv run python gen_brief.py --eval <chapter_num>
uv run python gen_brief.py --cuts <chapter_num>
uv run python gen_brief.py --panel <chapter_num>
uv run python voice_fingerprint.py
```

Esses scripts existem, mas ainda precisam de documentacao especifica sobre
entradas, saidas e riscos de sobrescrita.

## Typesetting

```bash
uv run python typeset/build_tex.py
```

Esse comando gera `typeset/chapters_content.tex` a partir de
`chapters/ch_*.md`. A compilacao final de PDF depende de uma ferramenta LaTeX
externa instalada no sistema. EPUB ainda e fluxo manual via ferramentas como
Pandoc ou Calibre.

## Testes

Baseline moderno:

```bash
uv run --with pytest pytest tests
```

Estado verificado: 274 testes passando.

Suite legada:

```bash
uv run --with pytest pytest legacy/tests
```

Status v0: nao e baseline confiavel; ha erros de coleta por imports de modulos
historicos removidos.
