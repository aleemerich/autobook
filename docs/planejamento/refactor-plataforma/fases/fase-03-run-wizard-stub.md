# Fase 03: `run.py` Abre Wizard Sem Argumentos

## Objetivo

Alterar `run.py` para abrir um wizard quando nenhum argumento for passado,
mantendo o comportamento atual quando argumentos forem informados.

## Contexto Obrigatorio

Ler:

- `run.py`
- `pipelines/registry.py` se existir
- `docs/planejamento/refactor-plataforma/01-run-entrypoint.md`

## Arquivos Permitidos

```text
run.py
cli/__init__.py
cli/wizard.py
tests/test_run_entrypoint.py
```

## Fora De Escopo

- Nao implementar wizard completo.
- Nao criar branch.
- Nao executar pipeline pelo wizard.
- Nao alterar argumentos existentes.

## Comportamento Desejado

```bash
uv run python run.py
```

deve chamar `cli.wizard.main()`.

```bash
uv run python run.py --pipeline ideation
```

deve seguir o comportamento atual.

O wizard nesta fase pode ser stub:

```text
Autobook wizard ainda em preparacao.
Use run.py --pipeline <nome> para executar pipelines.
```

## Passos

1. Criar pacote `cli/`.
2. Criar `cli/wizard.py` com `main()`.
3. Ajustar `run.py` para detectar ausencia de argumentos antes do parser
   exigir `--pipeline`.
4. Criar testes com mock de `cli.wizard.main`.
5. Garantir que chamadas com argumentos nao acionam wizard.

## Testes Obrigatorios

```bash
uv run --with pytest pytest tests/test_run_entrypoint.py
uv run --with pytest pytest tests
```

## Casos De Teste Minimos

- sem argumentos chama wizard.
- com `--pipeline` nao chama wizard.
- parser ainda aceita `--chapter`.
- parser ainda aceita `--from-scratch`.

## Criterios De Aceite

- `run.py` sem args nao falha.
- `run.py` com args preserva comportamento.
- Wizard nao contem logica de negocio ainda.

## Checklist Para O Executor

- [ ] Criei stub simples.
- [ ] Nao implementei fluxo interativo completo.
- [ ] Preservei parser antigo.
- [ ] Rodei testes obrigatorios.

## Checklist Para O Supervisor

- [ ] Sem argumentos e tratado antes de `argparse` exigir `--pipeline`.
- [ ] Wizard nao tem lista hardcoded complexa.
- [ ] Compatibilidade CLI foi preservada.

## Prompt Sugerido Para Delegar

```text
Implemente a Fase 03. Crie um stub de wizard em cli/wizard.py e altere run.py
para chama-lo apenas quando nenhum argumento for passado. Nao implemente wizard
completo. Preserve todos os argumentos atuais. Adicione testes.
```

