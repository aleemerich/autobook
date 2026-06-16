# Fase 01: Contrato Base De Pipelines

## Objetivo

Evoluir `pipelines/base.py` para suportar metadados opcionais em `Step` e
`Pipeline`, sem mudar o comportamento externo das pipelines atuais.

## Contexto Obrigatorio

Ler:

- `docs/planejamento/refactor-plataforma/plano-migracao-modelos-medios.md`
- `docs/planejamento/refactor-plataforma/02-pipeline-contract.md` se existir
- `pipelines/base.py`
- `run.py`
- `docs/pipelines/pipelines.md`

## Arquivos Permitidos

```text
pipelines/base.py
tests/test_pipeline_base.py
docs/planejamento/refactor-plataforma/02-pipeline-contract.md
```

## Fora De Escopo

- Nao alterar `run.py`.
- Nao alterar pipelines concretas.
- Nao criar registry.
- Nao criar wizard.
- Nao alterar comportamento de execucao.

## Comportamento Desejado

`Step` deve continuar aceitando o uso atual:

```python
Step("Nome")
```

Mas deve aceitar metadados opcionais:

```python
Step(
    name="Nome",
    description="Descricao curta",
    requires=["artifact_a"],
    produces=["artifact_b"],
)
```

`Pipeline` deve continuar sendo um `Step` e deve continuar executando steps em
ordem.

## Passos

1. Abrir `pipelines/base.py`.
2. Adicionar parametros opcionais em `Step.__init__`.
3. Guardar `requires` e `produces` como listas novas, nunca como default mutavel.
4. Adicionar parametros opcionais equivalentes em `Pipeline.__init__`.
5. Garantir que `Pipeline.add_step()` continue funcionando.
6. Criar `tests/test_pipeline_base.py`.
7. Rodar testes especificos e suite moderna.

## Testes Obrigatorios

```bash
uv run --with pytest pytest tests/test_pipeline_base.py
uv run --with pytest pytest tests
```

## Casos De Teste Minimos

- `Step("x")` preserva `name`.
- `Step("x", requires=["a"], produces=["b"])` guarda metadados.
- `Pipeline("p")` executa steps em ordem.
- `Pipeline` aceita metadados.
- Excecao levantada por step continua propagando.

## Criterios De Aceite

- Nenhuma pipeline concreta precisa ser alterada.
- Todos os testes modernos passam.
- O contrato antigo permanece valido.
- Metadados nao sao obrigatorios.

## Checklist Para O Executor

- [ ] Nao alterei `run.py`.
- [ ] Nao alterei pipelines concretas.
- [ ] Adicionei testes de base.
- [ ] Rodei os testes obrigatorios.
- [ ] Documentei qualquer risco.

## Checklist Para O Supervisor

- [ ] O diff e pequeno.
- [ ] Nao houve mudanca de comportamento externo.
- [ ] Nao ha default mutavel perigoso.
- [ ] Tests cobrem compatibilidade antiga e metadados novos.

## Prompt Sugerido Para Delegar

```text
Implemente a Fase 01. Altere apenas pipelines/base.py,
tests/test_pipeline_base.py e, se necessario, a spec 02-pipeline-contract.md.
Adicione metadados opcionais em Step/Pipeline sem quebrar o uso atual. Rode os
testes obrigatorios e reporte arquivos alterados, testes e riscos.
```

