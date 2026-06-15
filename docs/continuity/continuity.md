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

Status v0: presente, mas nao confiavel como fluxo fechado.

Problemas conhecidos:

- O arquivo contem duas definicoes de `main()`.
- Usa caminhos divergentes para o relatorio de continuidade.
- No final chama `run_editorial.py`, que nao existe mais no projeto.
- O fluxo correto de revisao hoje passa por `run.py --pipeline editorial_revision`.

Uso recomendado neste v0:

- Usar `verify_continuity.py` para diagnostico.
- Transformar manualmente os problemas em instrucoes em `book_data/editorial.md`.
- Rodar `editorial_revision` pelo orquestrador principal.

## Relatorios

O caminho esperado pelo fluxo moderno e `logs/eval_logs/continuity_report.json`.

## Planejamento

Para tornar continuidade um loop fechado novamente:

1. Remover a duplicacao de `main()`.
2. Padronizar o caminho do relatorio.
3. Trocar a chamada final para:

```bash
uv run python run.py --pipeline editorial_revision --chapter <lista>
```

4. Adicionar testes para o fluxo completo sem chamadas reais a LLM.

