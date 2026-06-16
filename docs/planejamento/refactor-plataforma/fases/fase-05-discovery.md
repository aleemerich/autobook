# Fase 05: Discovery Dinamico

## Objetivo

Criar uma camada de descoberta do estado atual do projeto para uso futuro pelo
wizard, sem executar pipelines ou alterar arquivos.

## Contexto Obrigatorio

Ler:

- `docs/operacional/comandos.md`
- `docs/book-data/book-data.md`
- `pipelines/registry.py`
- `workspace/branching.py` se existir

## Arquivos Permitidos

```text
cli/discovery.py
tests/test_cli_discovery.py
```

## Fora De Escopo

- Nao perguntar nada ao usuario.
- Nao executar pipeline.
- Nao criar branch.
- Nao criar arquivos de obra.
- Nao chamar LLM.

## Comportamento Desejado

Criar uma funcao de descoberta:

```python
discover_project_state(base_dir: Path | None = None) -> ProjectState
```

`ProjectState` pode ser dataclass ou dict, contendo:

```text
current_branch
pipelines
available_languages
available_genres
has_seed
book_data_files
foundation_complete
chapter_numbers
logs_present
production_artifacts_present
recommended_next_steps
```

`recommended_next_steps` deve ser simples e conservador. Exemplo:

- se nao ha `seed.txt`: sugerir `ideation`;
- se ha `seed.txt` mas falta foundation: sugerir `foundation`;
- se foundation existe mas nao ha production artifacts: sugerir
  `production_planning` futuramente ou indicar ausente;
- se ha capitulos: sugerir avaliacao/continuidade/revisao.

## Passos

1. Criar `cli/discovery.py`.
2. Usar `pipelines.registry.list_pipelines()` quando disponivel.
3. Descobrir idiomas lendo subpastas em `prompts/`.
4. Descobrir generos lendo arquivos em `genres/{LANG}/`.
5. Detectar capitulos por `chapters/ch_*.md`.
6. Detectar arquivos de `book_data/`.
7. Criar testes com `tmp_path`.

## Testes Obrigatorios

```bash
uv run --with pytest pytest tests/test_cli_discovery.py
uv run --with pytest pytest tests
```

## Casos De Teste Minimos

- projeto vazio retorna estado sem seed.
- projeto com seed sugere foundation.
- projeto com `book_data/world.md`, `characters.md`, `outline.md`, `canon.md`
  marca foundation completa.
- capitulos `ch_01.md`, `ch_03.md` retornam numeros `[1, 3]`.
- idiomas sao detectados de `prompts/`.
- generos sao detectados de `genres/`.
- ausencia de pastas nao quebra discovery.

## Criterios De Aceite

- Discovery nao altera filesystem.
- Discovery nao chama LLM.
- Discovery nao depende de listas duplicadas quando registry existe.
- Retorno e estavel para o wizard consumir.

## Checklist Para O Executor

- [ ] Usei `tmp_path` nos testes.
- [ ] Nao criei arquivos fora dos testes.
- [ ] Nao chamei pipelines.
- [ ] Rodei testes obrigatorios.

## Checklist Para O Supervisor

- [ ] Discovery nao contem logica pesada de negocio.
- [ ] Os proximos passos sao sugestoes, nao execucoes.
- [ ] Nao ha hardcode desnecessario de pipelines se registry existe.

## Prompt Sugerido Para Delegar

```text
Implemente a Fase 05. Crie cli/discovery.py para descobrir estado do projeto
sem alterar arquivos, sem chamar LLM e sem executar pipelines. Use registry
quando disponivel. Adicione testes com tmp_path.
```

