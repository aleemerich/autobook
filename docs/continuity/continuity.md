# Continuidade

O sistema de continuidade tem duas partes: verificacao global e tentativa de
geracao de correcoes.

## `verify_continuity.py`

Status v0: funcional como validador.

Responsabilidades:

- Ler `book_data/outline.md`.
- Parsear capitulos, local, personagens, beats, plants e harvests.
- Chamar um juiz LLM usando `AUTOBOOK_JUDGE_MODEL`.
- Gerar diagnostico de continuidade com `continuity_score`, inconsistencias e fluxo temporal.

Comandos:

```bash
uv run python verify_continuity.py
uv run python verify_continuity.py --strict --threshold 7.0
```

Se `outline.md` nao existir, o script tenta reconstruir usando
`legacy/build_outline.py`.

## `resolve_continuity.py`

Status: funcional como fluxo fechado.

Responsabilidades:

- Ler o relatório de continuidade em `logs/eval_logs/continuity_report.json`.
- Fazer backup do `book_data/editorial.md` atual para `logs/edit_logs/`.
- Se a nota de continuidade for menor que 7.5 ou houver problemas críticos de severidade média/alta, gera um novo `book_data/editorial.md` corretivo com as diretrizes e regras mapeadas.
- Identifica capítulos com pontuação baixa (< 7.0) e os agenda para re-revisão de qualidade.
- No final, aciona automaticamente a pipeline de revisão editorial executando via subprocesso:
  ```bash
  uv run python run.py --pipeline editorial_revision --chapter <capitulos>
  ```

## Relatorios

O caminho esperado pelo fluxo moderno e `logs/eval_logs/continuity_report.json`.

