# Fase 11: Wizard Como Area De Trabalho

## Objetivo

Transformar `run.py` sem argumentos em uma area de trabalho interativa para o
usuario produzir uma obra, usando o estado real do projeto em vez de listas
hardcoded.

## Status

Definida pos-Gate A. Executar depois da Fase 10 aceita.

## Papel Do Wizard

O wizard nao deve ser apenas menu. Ele deve orientar o usuario na sequencia
correta:

```text
obra nova ou existente
  -> branch de obra
  -> ideation
  -> foundation
  -> production_planning
  -> book_generation
  -> editorial_revision
```

## Capacidades Iniciais

- Mostrar branch atual.
- Avisar quando estiver em `main` ou `master`.
- Criar branch de obra mediante confirmacao explicita.
- Usar `cli.discovery.discover_project_state`.
- Listar pipelines via `pipelines.registry`.
- Mostrar idiomas e generos disponiveis.
- Mostrar arquivos de obra encontrados.
- Sugerir proximo passo conservador.
- Exibir comando equivalente antes de executar.
- Permitir sair sem alterar nada.

## Regras De Seguranca

- Nenhuma acao destrutiva sem confirmacao.
- Nenhum checkout ou criacao de branch em testes reais.
- Execucao de pipelines deve ser mockavel.
- Wizard nao deve conter lista hardcoded de pipelines.
- Wizard deve respeitar bloqueio de escrita em `main`/`master`.

## Fora De Escopo

- Interface grafica.
- Otimizacao de ergonomia fina.
- Execucao paralela de pipelines.
- Edicao interativa complexa de arquivos.
- Substituir a CLI classica com argumentos.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_cli_wizard.py
uv run --with pytest pytest tests/test_run_entrypoint.py
uv run --with pytest pytest tests
git diff --check -- cli run.py workspace tests docs/planejamento/refactor-plataforma
```

Testes minimos:

- `run.py` sem argumentos chama wizard.
- wizard mostra estado vindo de discovery.
- wizard usa registry para listar pipelines.
- wizard bloqueia ou alerta em branch principal.
- criacao de branch e execucao de pipeline sao mockadas.
- usuario pode cancelar sem efeitos colaterais.

## Criterios De Aceite

- Usuario consegue entender o estado da obra pelo terminal.
- Main/master permanecem limpas por padrao.
- A CLI antiga continua funcionando com argumentos.
- Wizard usa sempre fontes atuais do projeto, nao listas fixas duplicadas.

