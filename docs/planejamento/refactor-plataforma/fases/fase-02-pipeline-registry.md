# Fase 02: Registry De Pipelines

## Objetivo

Criar uma fonte central para listar e instanciar pipelines disponiveis, sem
remover compatibilidade com `run.py --pipeline`.

## Contexto Obrigatorio

Ler:

- `pipelines/base.py`
- `run.py`
- `pipelines/ideation.py`
- `pipelines/foundation.py`
- `pipelines/book_generation.py`
- `pipelines/editorial_revision.py`
- `docs/planejamento/refactor-plataforma/02-pipeline-contract.md`

## Arquivos Permitidos

```text
pipelines/registry.py
run.py
tests/test_pipeline_registry.py
```

## Fora De Escopo

- Nao alterar comportamento das pipelines.
- Nao criar wizard.
- Nao renomear pipelines publicas.
- Nao autoimportar modulos arbitrarios do filesystem.

## Comportamento Desejado

Criar API em `pipelines/registry.py`:

```python
list_pipelines() -> dict
get_pipeline(name: str)
get_pipeline_spec(name: str)
```

Cada spec deve conter, no minimo:

```text
name
description
factory
supports_chapter
supports_from_scratch
```

Pipelines publicas iniciais:

```text
ideation
foundation
book_generation
editorial_revision
```

## Passos

1. Criar `pipelines/registry.py`.
2. Registrar as quatro pipelines atuais.
3. Fazer `list_pipelines()` retornar dados sem instanciar/rodar pipelines.
4. Fazer `get_pipeline(name)` instanciar sob demanda.
5. Atualizar `run.py` para usar registry se isso puder ser feito sem quebrar
   comportamento.
6. Criar testes.

## Testes Obrigatorios

```bash
uv run --with pytest pytest tests/test_pipeline_registry.py
uv run --with pytest pytest tests
```

## Casos De Teste Minimos

- `list_pipelines()` contem os quatro nomes atuais.
- `get_pipeline("ideation")` retorna instancia de pipeline.
- nome invalido levanta erro claro.
- listar pipelines nao executa nenhum step.
- `run.py` continua aceitando `--pipeline`.

## Criterios De Aceite

- CLI atual continua valida.
- Registry e fonte unica de descoberta para fases futuras.
- Testes nao chamam LLM.

## Checklist Para O Executor

- [ ] Criei `pipelines/registry.py`.
- [ ] Testei nomes validos e invalidos.
- [ ] Nao rodei pipelines durante listagem.
- [ ] Mantive nomes publicos atuais.
- [ ] Rodei testes obrigatorios.

## Checklist Para O Supervisor

- [ ] Registry nao adiciona import dinamico inseguro.
- [ ] `run.py` segue simples.
- [ ] Nao houve mudanca de semantica dos argumentos.

## Prompt Sugerido Para Delegar

```text
Implemente a Fase 02. Crie pipelines/registry.py com list_pipelines,
get_pipeline_spec e get_pipeline para as quatro pipelines atuais. Preserve o
comportamento de run.py --pipeline. Adicione testes sem chamadas LLM.
```

