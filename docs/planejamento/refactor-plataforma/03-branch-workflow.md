# 03 - Branch Workflow Spec

## Objetivo
Especificar a regra de gerenciamento de branch no Git para garantir que a branch principal (`main`/`master`) permaneça limpa de arquivos temporários de escrita de livros e que cada obra viva em sua própria branch isolada. Especificar os utilitários de suporte necessários em `workspace/branching.py`.

## Fora De Escopo
- Mover ou alterar os caminhos dos diretórios de escrita como `book_data/`, `chapters/` ou do arquivo `seed.txt` no repositório nesta fase.
- Executar ações reais e destrutivas no repositório de trabalho local do usuário (como trocar de branch com checkout destrutivo) durante a execução dos testes automáticos.

## Estado Atual
Atualmente, as pipelines de geração do Autobook são executadas diretamente sobre a branch ativa (frequentemente `main` ou `master`), gerando commits automáticos de escrita que poluem o histórico de commits do código-fonte do projeto com dezenas de capítulos e dados temporários de livros.

## Comportamento Desejado
- **Regra de Projeto:** A branch principal (`main`/`master`) deve ser considerada projeto limpo. Nenhuma obra ou capítulo pode ser gerado/escrito enquanto a branch principal estiver ativa.
- **Convenção de Branches:** As obras em desenvolvimento devem residir em uma branch exclusiva, seguindo a convenção de nomenclatura: `autobook/<slug>`, onde `<slug>` é a representação sanitizada e ASCII do título do livro.
- **Utilitários do Workspace:** Criar o módulo `workspace/branching.py` com:
  - `slugify_work_title(title: str) -> str`: Função pura que converte caracteres especiais e acentuações do título em um slug seguro.
  - `book_branch_name(title_or_slug: str) -> str`: Converte o slug ou título no nome de branch padronizado `autobook/<slug>`.
  - `is_main_branch(branch: str) -> bool`: Retorna True se a branch corresponder a `main` ou `master`.
  - `current_branch() -> str`: Obtém a branch Git atual executando comandos via subprocess (de forma isolada e tratável).
  - `ensure_not_main_for_generation(branch: str | None = None) -> None`: Lança uma exceção explicativa se a branch em verificação (ou a branch ativa obtida se nenhuma for informada) for uma branch principal (`main`/`master`).

## Diretrizes de Segurança
Todos os testes automáticos devem isolar e simular chamadas ao subprocess Git utilizando `unittest.mock`. Nenhuma ação destrutiva de Git (como checkouts automáticos ou exclusões de branches locais) está autorizada a rodar de forma automática nos testes, devendo sempre exigir confirmação expressa do usuário caso integrados a scripts interativos.

## Arquivos Afetados Futuramente
- [NEW] `workspace/__init__.py`
- [NEW] `workspace/branching.py`
- [NEW] `tests/test_workspace_branching.py`

## Contratos De Entrada
- Título da obra em formato string.
- Nome de branch atual em formato string.

## Contratos De Saida
- Nomes de branch sanitizados ou booleanos de validação.
- Levantamento de exceção de violação de branch em caso de uso inadequado da branch `main`/`master`.

## Testes Necessarios
1. **Slugify Pura:** Testar conversão de títulos complexos (ex: `"O Mistério da Floresta Azul!"` deve virar `"o-misterio-da-floresta-azul"`).
2. **Identificação de Branches:** Validar que `main` e `master` são reconhecidas como branches principais, e `autobook/livro-a` é aceita.
3. **Mock de Subprocess Git:** Garantir que o método `current_branch()` chama comandos git de leitura de forma isolada, e testar seu retorno simulando diferentes saídas de comando no mock.

## Criterios De Aceite
- Nenhuma modificação é feita na branch ativa real ou no workspace do Git local durante a execução do pytest.
- Uma exceção clara e documentada é lançada quando se tenta executar na branch principal.
- Compatibilidade mantida com as execuções de pipelines legadas sem quebra abrupta enquanto a integração total no wizard é adiada.

## Perguntas Abertas
- Como alertar o usuário de forma amigável no stub do wizard sobre a necessidade de alternar branches?
