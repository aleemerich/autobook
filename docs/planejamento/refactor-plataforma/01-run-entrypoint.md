# 01 - run.py Entrypoint Spec

## Objetivo
Especificar a alteração do ponto de entrada principal (`run.py`) do Autobook para permitir a execução de um wizard interativo quando chamado sem argumentos, mantendo a plena compatibilidade com a CLI existente quando chamada com argumentos.

## Fora De Escopo
- Implementar a lógica de interface ou negócio do wizard interativo completo (somente o stub inicial de resposta).
- Alterar as assinaturas das pipelines existentes ou o comportamento de seus steps de execução.

## Estado Atual
Atualmente, `run.py` usa a biblioteca `argparse` com a opção `--pipeline` configurada como `required=True`. Se o script for chamado sem argumentos, o parser do argparse exibe uma mensagem de erro e aborta a execução, impedindo qualquer fallback automático para um assistente interativo.

## Comportamento Desejado
- **Chamada Sem Argumentos:** A execução de `uv run python run.py` (sem argumentos na linha de comando) deve importar e executar o método `main()` de `cli/wizard.py`.
- **Chamada Com Argumentos:** A execução de comandos como `uv run python run.py --pipeline ideation` deve ignorar o wizard e seguir o fluxo do parser do argparse existente, executando as pipelines com seus parâmetros corretos.
- **Design Recomendado (Testável):** Refatorar o método `main` em `run.py` para aceitar parâmetros, ex: `main(argv: list[str] | None = None)`. O valor default de `argv` deve ser `sys.argv[1:]`. Se a lista estiver vazia, chama-se o stub do wizard. Caso contrário, passa-se a lista para o `argparse.ArgumentParser.parse_args(argv)`.

## Arquivos Afetados Futuramente
- `run.py`
- [NEW] `cli/__init__.py`
- [NEW] `cli/wizard.py`
- [NEW] `tests/test_run_entrypoint.py`

## Contratos De Entrada
- Linha de comando com argumentos como `--pipeline`, `--chapter`, `--from-scratch` e `--yes`.

## Contratos De Saida
- Código de retorno 0 em execuções de sucesso.
- Código de retorno 1 ou mensagens no `stderr` em caso de falha de parsing de argumento inválido ou erro de pipeline.

## Testes Necessarios
1. **Sem Argumentos:** Testar que a execução de `run.py` sem argumentos importa e invoca a função `cli.wizard.main` (pode ser validado mockando a função com `unittest.mock`).
2. **Com Argumentos Válidos:** Testar que a passagem de argumentos (ex: `--pipeline ideation`) executa a pipeline correta e não invoca o wizard.
3. **Preservação de Argumentos Opcionais:** Testar que `--chapter`, `--from-scratch` e `--yes` são repassados e interpretados corretamente sem interferência do stub do wizard.

## Criterios De Aceite
- Execução limpa sem argumentos, exibindo a mensagem do stub do wizard (ex: "Autobook wizard ainda em preparacao. Use run.py --pipeline <nome> para executar pipelines.").
- Todas as execuções de testes existentes no repositório continuam passando sem regressões.
- Nenhuma dependência externa adicional de CLI (como `prompt_toolkit` ou `rich`) introduzida nesta fase.

## Perguntas Abertas
- Qual padrão de exibição visual será adotado no stub para harmonizar com as mensagens gerais de pipeline?
