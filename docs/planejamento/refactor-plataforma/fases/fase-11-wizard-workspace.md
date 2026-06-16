# Fase 11: Wizard Como Area De Trabalho

## Objetivo

Transformar `run.py` sem argumentos em area de trabalho interativa para o
usuario produzir uma obra.

## Status

Executar depois de registry, discovery e branch workflow.

## Capacidades Iniciais

- mostrar branch atual;
- avisar quando estiver em `main`;
- listar estado da obra;
- sugerir proximos passos;
- criar branch de obra mediante confirmacao;
- chamar pipelines existentes;
- mostrar comando equivalente antes de executar.

## Regras

- Wizard usa discovery e registry.
- Wizard nao deve conter lista hardcoded de pipelines.
- Nenhuma acao destrutiva sem confirmacao.
- Testes devem mockar input, Git e execucao de pipeline.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_cli_wizard.py
uv run --with pytest pytest tests
```

