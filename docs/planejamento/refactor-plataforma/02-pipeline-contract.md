# 02 - Pipeline Contract Spec (Fase 1)

## Objetivo
Especificar a evolução do contrato base de execução do Autobook, introduzindo metadados opcionais para os passos (`Step`) e pipelines (`Pipeline`), garantindo compatibilidade retroativa total com a base existente.

## Fora De Escopo
- Implementar o registro centralizado de pipelines (`pipelines/registry.py`), que é de escopo exclusivo da **Fase 2**.
- Implementar a camada de descoberta do estado do projeto (`cli/discovery.py`), que é de escopo exclusivo da **Fase 5**.
- Adicionar verificações ou validações automáticas baseadas nos metadados declarados durante a execução da Fase 1.

## Estado Atual
Atualmente, as classes `Step` e `Pipeline` em `pipelines/base.py` são muito simples. O construtor de `Step` aceita apenas `name`. Não há como declarar dependências de entrada/saída ou descrições textuais associadas a cada passo de forma declarativa.

## Comportamento Desejado
- **Contrato Estendido:** `Step` e `Pipeline` devem aceitar metadados adicionais e opcionais em seus construtores:
  - `name: str` (obrigatório, mantido como primeiro argumento posicional)
  - `description: str | None = None`
  - `requires: list[str] | None = None` (lista de dependências/entradas exigidas)
  - `produces: list[str] | None = None` (lista de artefatos produzidos)
- **Segurança de Efeitos Colaterais:** Para evitar o antipadrão Python de usar listas mutáveis como padrão de argumento, o construtor deve aceitar `None` para `requires` e `produces` e inicializar listas vazias internamente caso não fornecidos.
- **Compatibilidade Retroativa:** Instanciações existentes no formato antigo (ex: `Step("nome")` ou `Pipeline("nome", steps)`) devem continuar executando sem qualquer alteração sintática ou de comportamento.

## Notas sobre Fases Posteriores
- **Registro de Pipelines:** A descoberta e centralização de pipelines em um registro unificado é tratada pela **Fase 2**.
- **Descoberta do Estado:** A camada para inspecionar dinamicamente o status da obra e recomendar os próximos passos é tratada pela **Fase 5**.
- **Validação de Metadados:** Por decisão do supervisor, os campos `requires` e `produces` não serão validados automaticamente na Fase 1. A sua utilidade será avaliada pelo supervisor no Gate A, antes de se propor qualquer linter ou verificação obrigatória.

## Arquivos Afetados Futuramente
- `pipelines/base.py`
- [NEW] `tests/test_pipeline_base.py`

## Contratos De Entrada
- Instanciação de `Step` ou `Pipeline` com ou sem os argumentos adicionais.

## Contratos De Saida
- Atributos acessíveis no objeto instanciado: `name`, `description`, `requires` e `produces`.

## Testes Necessarios (Fase 1)
1. **Compatibilidade Básica:** Validar que `Step("nome")` instancia corretamente e expõe o nome, com listas vazias padrão para `requires` e `produces`.
2. **Definição de Metadados:** Validar que `Step("nome", description="desc", requires=["a"], produces=["b"])` armazena e expõe corretamente todos os valores.
3. **Pipeline Composite:** Validar que a classe `Pipeline` continua aceitando opcionalmente uma lista de passos no construtor e continua executando os passos na ordem correta ao chamar `.run(context)`.
4. **Propagação de Exceções:** Validar que erros lançados em passos individuais propagam normalmente através da pipeline, exatamente como ocorria antes da adição dos metadados.

## Criterios De Aceite (Fase 1)
- Nenhuma pipeline concreta existente no projeto precisa ser modificada nesta fase.
- A suite de testes moderna (`tests/`) continua executando com 100% de sucesso.
- O contrato antigo permanece totalmente válido e funcional.

## Perguntas Abertas
- Nenhuma pendência para a Fase 1.
