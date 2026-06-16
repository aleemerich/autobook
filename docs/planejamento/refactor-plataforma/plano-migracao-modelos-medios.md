# Plano de Migracao Para Execucao Por Modelos Medios

> [!IMPORTANT]
> **Status de Execução do Plano:**
> - **Fases 0 a 5:** Estão **prontas para delegação e execução imediata**.
> - **Fases 6 a 12:** Constituem um **roadmap preliminar estratégico**. Elas não estão autorizadas para execução sequencial automática e **exigem obrigatoriamente uma reavaliação arquitetural completa** após a conclusão das fases anteriores.
> - O plano completo existe para preservar a direção estratégica de longo prazo, não para autorizar execução sequencial automática sem validação intermediária.

Este documento define um plano de migracao robusto para que modelos medios
consigam implementar a reorganizacao da plataforma Autobook em fases pequenas,
testaveis e revisaveis.

O desenho assume dois papeis:

- **Executor:** modelo medio/barato, responsavel por implementar tarefas
  fechadas, com escopo pequeno e criterios objetivos.
- **Supervisor:** modelo mais forte ou humano tecnico, responsavel por revisar
  arquitetura, coerencia, regressao, testes e documentacao antes de aceitar cada
  fase.

## Viabilidade

E viavel usar modelos medios para grande parte da implementacao se o trabalho
for organizado com disciplina:

- uma fase por vez;
- specs pequenas;
- mudancas incrementais;
- testes antes/depois;
- contratos de arquivos claros;
- evitar refactors massivos;
- evitar tarefas abertas como "melhore a arquitetura";
- pedir sempre diff pequeno e verificavel;
- bloquear avanco se testes ou docs nao fecharem.

Nao e recomendavel usar modelos medios para decisoes arquiteturais amplas sem
supervisao. Eles podem executar bem quando recebem:

- arquivo-alvo;
- comportamento esperado;
- exemplos;
- criterios de aceite;
- comando de teste;
- restricoes explicitas do que nao alterar.

## Regra Geral De Trabalho

Cada tarefa deve seguir este ciclo:

```text
1. Ler docs obrigatorios
2. Inspecionar arquivos-alvo
3. Propor microplano
4. Implementar alteracao pequena
5. Rodar testes especificos
6. Rodar verificacao minima geral
7. Atualizar docs se necessario
8. Produzir resumo para revisao
9. Supervisor aprova ou pede correcao
```

## Documentos Obrigatorios Para Todo Executor

Antes de qualquer fase, o executor deve ler:

```text
docs/INDICE.md
docs/SNAPSHOT_V0.md
docs/analises/recomendacao_pipeline_producao.md
docs/planejamento/como-transformar-parecer-em-specs.md
docs/planejamento/refactor-plataforma/plano-migracao-modelos-medios.md
```

Se a tarefa tocar pipelines:

```text
docs/pipelines/pipelines.md
pipelines/base.py
run.py
```

Se tocar agentes:

```text
docs/agents/agentes.md
agents.py
prompt_loader.py
prompts/
```

Se tocar testes:

```text
docs/tests/tests.md
tests/
```

## Comandos Minimos De Verificacao

Para mudancas apenas em docs:

```bash
git diff --check -- docs
```

Para mudancas em codigo sem LLM real:

```bash
uv run --with pytest pytest tests
```

Para mudancas localizadas, rodar tambem testes especificos:

```bash
uv run --with pytest pytest tests/test_llm_unit.py
uv run --with pytest pytest tests/test_generation_flow.py
uv run --with pytest pytest tests/test_foundation_pipeline.py
```

`legacy/tests` nao e baseline de aceite neste momento.

## Fase 0: Especificacoes Antes De Codigo

### Objetivo

Criar specs suficientes para orientar o refactor sem depender da conversa.

### Entregas

Criar documentos:

```text
docs/planejamento/refactor-plataforma/00-decisao.md
docs/planejamento/refactor-plataforma/01-run-entrypoint.md
docs/planejamento/refactor-plataforma/02-pipeline-contract.md
docs/planejamento/refactor-plataforma/03-branch-workflow.md
docs/planejamento/refactor-plataforma/04-agent-registry.md
docs/planejamento/refactor-plataforma/05-prompt-layout.md
docs/planejamento/refactor-plataforma/06-feedback-lifecycle.md
docs/planejamento/refactor-plataforma/07-migration-plan.md
```

### Instrucoes Para Executor

- Nao alterar codigo.
- Escrever specs curtas e objetivas.
- Cada spec deve conter: objetivo, fora de escopo, estado atual, comportamento
  desejado, arquivos afetados, testes necessarios e criterios de aceite.
- Nao inventar funcionalidades alem do que foi decidido.

### Criterios De Aceite

- Specs apontam caminhos reais do projeto.
- Specs preservam compatibilidade inicial com comandos atuais.
- Specs deixam claro que `run.py` sem argumentos abre wizard futuramente.
- Specs deixam claro que `main` deve ser projeto limpo e obra deve viver em
  branch propria.

### Revisao Do Supervisor

Verificar:

- se as specs sao implementaveis por fases;
- se nao ha acoplamento prematuro com `production_planning`;
- se o plano evita reescrever tudo de uma vez.

## Fase 1: Contrato Base De Pipelines Sem Mudar Comportamento

### Objetivo

Preparar `pipelines/base.py` para metadados e composicao sem quebrar pipelines
existentes.

### Arquivos Provaveis

```text
pipelines/base.py
tests/test_pipeline_base.py
docs/planejamento/refactor-plataforma/02-pipeline-contract.md
```

### Mudancas Esperadas

- Manter `Step.run(context)` e `Pipeline.run(context)`.
- Adicionar metadados opcionais:

```python
name: str
requires: list[str]
produces: list[str]
description: str | None
```

- Permitir que `Pipeline` continue sendo um `Step`.
- Nao exigir mudanca imediata nas pipelines antigas.

> [!NOTE]
> **Decisão do Supervisor (Validação):** Os metadados `requires` e `produces` são estritamente opcionais na Fase 1, sem qualquer validação obrigatória ou restrição de execução. O supervisor avaliará no Gate A a utilidade dos metadados declarados antes de propor qualquer validação automática ou linting.

### Fora De Escopo

- Nao refatorar `book_generation`.
- Nao criar wizard.
- Nao mudar CLI.

### Testes Necessarios

- Criar testes para:
  - step simples executa;
  - pipeline executa steps em ordem;
  - pipeline aceita metadados;
  - metadados sao opcionais;
  - erro em step propaga como antes.

### Criterios De Aceite

- Testes novos passam.
- Suite moderna `tests/` passa.
- Pipelines atuais continuam executaveis pelo contrato antigo.

### Tarefa Boa Para Modelo Medio

Sim. Escopo pequeno e fortemente testavel.

## Fase 2: Registry De Pipelines

### Objetivo

Criar uma fonte central de descoberta de pipelines sem remover imediatamente os
imports atuais de `run.py`.

### Arquivos Provaveis

```text
pipelines/registry.py
run.py
tests/test_pipeline_registry.py
```

### Mudancas Esperadas

Criar API:

```python
list_pipelines() -> dict[str, PipelineSpec]
get_pipeline(name: str) -> Pipeline
```

`PipelineSpec` pode ser simples:

```python
name
description
factory
supports_chapter
supports_from_scratch
```

### Fora De Escopo

- Nao autoimportar dinamicamente arquivos arbitrarios.
- Nao mudar nomes publicos dos pipelines.
- Nao remover compatibilidade com `--pipeline`.

### Testes Necessarios

- `list_pipelines` retorna os quatro pipelines atuais.
- `get_pipeline("ideation")` instancia pipeline correta.
- nome invalido gera erro claro.
- registry nao executa pipeline ao listar.

### Criterios De Aceite

- `run.py --pipeline ...` continua funcionando.
- Testes novos passam.
- Suite moderna passa.

### Tarefa Boa Para Modelo Medio

Sim, se a API for especificada antes.

## Fase 3: Ajuste De `run.py` Para Wizard Futuro

### Objetivo

Permitir que `run.py` sem argumentos chame um wizard, preservando o
comportamento atual quando argumentos forem passados.

### Arquivos Provaveis

```text
run.py
cli/wizard.py
tests/test_run_entrypoint.py
```

### Mudancas Esperadas

- Se `len(sys.argv) == 1`, chamar `cli.wizard.main()`.
- Se houver argumentos, manter parser atual.
- `cli/wizard.py` pode inicialmente ser minimo e seguro:

```text
mostrar status basico e sair
```

ou:

```text
exibir mensagem informando que o wizard completo ainda sera implementado
```

### Fora De Escopo

- Nao implementar wizard completo.
- Nao criar branch ainda.
- Nao alterar pipelines.

### Testes Necessarios

- Sem argumentos chama wizard mockado.
- Com argumentos nao chama wizard.
- `--pipeline ideation` segue caminho antigo.

### Criterios De Aceite

- Compatibilidade CLI preservada.
- Entrada sem args nao falha mais por ausencia de `--pipeline`.

### Tarefa Boa Para Modelo Medio

Sim, desde que o wizard seja stub/controlado nesta fase.

## Fase 4: Workflow De Branch Por Obra

### Objetivo

Criar utilitarios para garantir que obras sejam geradas em branches proprias e
que `main` permaneca limpo.

### Arquivos Provaveis

```text
workspace/
  branching.py
  state.py
tests/test_workspace_branching.py
docs/planejamento/refactor-plataforma/03-branch-workflow.md
```

### Mudancas Esperadas

Criar funcoes:

```python
current_branch() -> str
is_main_branch(branch: str) -> bool
slugify_work_title(title: str) -> str
book_branch_name(title_or_slug: str) -> str
ensure_not_main_for_generation(...)
```

Possivel convencao:

```text
autobook/<slug-da-obra>
```

### Fora De Escopo

- Nao executar `git checkout -b` automaticamente ainda, a menos que spec
  posterior aprove.
- Nao mover `book_data/` para outra pasta.
- Nao alterar comandos existentes de geracao nesta fase.

### Testes Necessarios

- slugify com acentos, espacos e caracteres especiais.
- deteccao de `main`/`master`.
- nome de branch previsivel.
- comandos Git mockados, sem tocar repo real.

### Criterios De Aceite

- Nenhum teste executa Git destrutivo.
- Regras de branch documentadas.
- Utilitarios prontos para serem usados pelo wizard depois.

### Tarefa Boa Para Modelo Medio

Sim, se proibirmos comandos destrutivos e exigirmos mocks.

## Fase 5: Discovery Dinamico Para Wizard

### Objetivo

Criar uma camada que descubra estado atual do projeto sem hardcodes frageis.

### Arquivos Provaveis

```text
cli/discovery.py
tests/test_cli_discovery.py
```

### Descobertas Esperadas

- pipelines disponiveis via registry;
- idiomas disponiveis em `prompts/`;
- generos disponiveis em `genres/`;
- existencia de `seed.txt`;
- completude de `book_data/`;
- capitulos existentes;
- branch atual;
- logs principais existentes.

### Fora De Escopo

- Nao interagir com usuario.
- Nao executar pipeline.
- Nao criar arquivos.

### Testes Necessarios

- usar diretorios temporarios;
- simular `prompts/`, `genres/`, `book_data/`, `chapters/`;
- testar ausencia de pastas;
- testar retorno estruturado.

### Criterios De Aceite

- Discovery retorna dict/dataclass estavel.
- Nao depende de nomes hardcoded alem dos contratos do projeto.
- Nao chama LLM.

### Tarefa Boa Para Modelo Medio

Sim.

## Gate A: Revisao Arquitetural Apos Fases 0-5

Antes de iniciar qualquer atividade das Fases 6 a 12, o supervisor deve realizar uma reavaliação arquitetural obrigatória para validar o progresso acumulado e confirmar se as premissas de desenho continuam válidas.

**Questões de Verificação do Gate A:**
1. **Contrato de Pipeline:** O novo contrato base de pipelines funcionou de forma limpa e flexível para acomodar metadados?
2. **Registry:** O registry centralizado de pipelines ficou limpo, elegante e evita importações dinâmicas arriscadas?
3. **Compatibilidade CLI:** O script `run.py` permaneceu plenamente compatível com a CLI antiga e seus respectivos argumentos?
4. **Preparação para o Wizard:** A chamada de `run.py` sem argumentos está corretamente redirecionada para o stub do wizard?
5. **Segurança do Branch Workflow:** O workflow de branches para desenvolvimento de livros está seguro, isolado e sem comandos destrutivos perigosos para o usuário?
6. **Robustez do Discovery:** A camada de discovery consegue mapear com precisão o estado do projeto para guiar de forma limpa o wizard interativo futuro?
7. **Validação da Ordem do Roadmap:** A ordem lógica das fases subsequentes (6 a 12) ainda faz sentido prático para evitar retrabalho?
8. **Reavaliação de Decisões:** Há alguma decisão de design (especialmente sobre agents/prompts e subpipelines do `book_generation`) que precise ser alterada antes de prosseguir?

> [!CAUTION]
> **BLOQUEIO DE EXECUÇÃO:** Nenhuma tarefa da Fase 6 em diante pode ser iniciada antes que este Gate A seja formalmente avaliado, documentado e aprovado pelo supervisor.

## Fase 6: Organizacao Inicial De Agentes Sem Migrar Tudo [ROADMAP PRELIMINAR]

> [!WARNING]
> **Fase de Roadmap:** Esta fase faz parte do roadmap preliminar e **não deve ser executada** antes da aprovação do Gate A.

### Objetivo

Preparar estrutura nova de agentes mantendo `agents.py` compativel usando um pacote intermediário para evitar conflitos de importação no Python.

### Arquivos Provaveis

```text
agents.py
agent_system/
  __init__.py
  base.py
  registry.py
  factory.py
tests/test_agents_registry.py
```

### Mudancas Esperadas

- Criar a estrutura sob a pasta `agent_system/` (em vez de `agents/`) para evitar conflitos de imports com o arquivo `agents.py` na raiz do projeto.
- Criar `agent_system/base.py` com classe base equivalente.
- Criar registry simples de papéis em `agent_system/registry.py`.
- Manter `from agents import AgentFactory` funcionando (redirecionando para `agent_system`), ou adotar transição controlada de imports se necessário.

### Recomendação de Design

Decisão fechada para mitigar conflitos de nomes do Python: usar obrigatoriamente a pasta `agent_system/` como pacote intermediário. Não criar pasta `agents/` enquanto existir o arquivo `agents.py` na raiz para não quebrar o sistema de imports do Python.

> [!NOTE]
> **Decisão do Supervisor (Depreciação de `agents.py`):** O arquivo `agents.py` na raiz do projeto não será removido nem deprecado agora. A sua remoção/depreciação ocorrerá em uma fase futura dedicada (`fase-06x-deprecate-agents-py.md`), a ser planejada e executada somente após o pacote `agent_system/` estar consolidado, testado e com todos os imports migrados, nunca antes do Gate A.

### Fora De Escopo

- Nao mover todos os prompts.
- Nao alterar `book_generation` profundamente.
- Nao remover classes antigas ainda.

### Testes Necessarios

- registry registra papel;
- factory cria agente;
- papel inexistente gera erro claro;
- compatibilidade com agentes atuais.

### Criterios De Aceite

- `tests/` passa.
- Nenhum import atual quebra.
- Plano de migracao para prompts fica documentado.

### Tarefa Boa Para Modelo Medio

Moderada. Requer cuidado com imports. Supervisor deve revisar antes de aceitar.

## Fase 7: Externalizacao Gradual De Prompts De Agentes [ROADMAP PRELIMINAR]

> [!WARNING]
> **Fase de Roadmap:** Esta fase faz parte do roadmap preliminar e **não deve ser executada** antes da aprovação do Gate A.

### Objetivo

Mover prompts hardcoded dos agentes para arquivos em `prompts/{LANG}/agents/`
sem mudar comportamento funcional.

### Arquivos Provaveis

```text
prompts/EN/agents/
prompts/PT-BR/agents/
prompt_loader.py
agent_system/
tests/test_agent_prompts.py
```

### Mudancas Esperadas

- Criar loader para prompt de agente.
- Comecar por 1 ou 2 agentes simples.
- Manter fallback para prompt hardcoded se arquivo nao existir durante
  transicao.

### Fora De Escopo

- Nao reescrever todos os prompts numa unica tarefa.
- Nao mudar semantica de agentes.

### Testes Necessarios

- carrega prompt em idioma ativo;
- fallback para EN;
- erro claro quando prompt obrigatorio falta;
- agente recebe system prompt esperado.

### Criterios De Aceite

- Primeiros agentes migrados funcionam.
- Padrao fica documentado.
- Suite moderna passa.

### Tarefa Boa Para Modelo Medio

Sim, se migrar poucos agentes por vez.

## Fase 8: Feedback Lifecycle [ROADMAP PRELIMINAR]

> [!WARNING]
> **Fase de Roadmap:** Esta fase faz parte do roadmap preliminar e **não deve ser executada** antes da aprovação do Gate A.

### Objetivo

Garantir que todo feedback produzido por agente seja consumido por uma etapa posterior.

**Estratégia Recomendada para Evitar Retrabalho:**
A implementação real deste ciclo deve ser dividida e coordenada em relação à extração das subpipelines para evitar retrabalho de refatoramento em código monolítico:
1. **Fase 8a (Documentação):** Formalizar o contrato de feedback (`critic_report -> revision_plan -> revised_text`).
2. **Fase 9 (Extração):** Decompor o `book_generation` monolítico em subpipelines.
3. **Fase 8b (Implementação):** Implementar o feedback lifecycle diretamente dentro das subpipelines já extraídas e limpas.

### Arquivos Provaveis

```text
pipelines/book_generation.py
pipelines/subpipelines/
tests/test_feedback_lifecycle.py
docs/planejamento/refactor-plataforma/06-feedback-lifecycle.md
```

### Mudancas Esperadas

Introduzir contrato:

```text
critic_report -> revision_plan -> revised_text -> verification_report
```

Implementação planejada para a Fase 8b:
- preservar arquivos `critique_*.md`;
- adicionar etapa que cria plano estruturado simples;
- garantir que synthesis receba explicitamente o plano;
- adicionar verificacao simples de aplicacao.

### Fora De Escopo

- Nao implementar `production_planning`.
- Nao mudar o algoritmo completo de geracao ainda.

### Testes Necessarios

- criticas geradas sao listadas;
- plano de revisao inclui referencias as criticas;
- synthesis recebe plano;
- se nao houver critica, fluxo continua com plano vazio;
- logs sao gravados.

### Criterios De Aceite

- Nenhum agente critico atua sem sua saida ser lida depois.
- Teste prova a passagem de dados.

### Tarefa Boa Para Modelo Medio

Moderada. Precisa supervisor revisar porque toca fluxo central.

## Fase 9: Refactor De `book_generation` Em Subpipelines [ROADMAP PRELIMINAR]

> [!WARNING]
> **Fase de Roadmap:** Esta fase faz parte do roadmap preliminar e **não deve ser executada** antes da aprovação do Gate A.

### Objetivo

Separar `book_generation` em blocos reutilizaveis.

### Subpipelines Sugeridas

```text
ChapterPreparationPipeline
DraftingPipeline
CritiquePipeline
RevisionPipeline
ValidationPipeline
PersistencePipeline
```

### Arquivos Provaveis

```text
pipelines/book_generation.py
pipelines/subpipelines/chapter_preparation.py
pipelines/subpipelines/drafting.py
pipelines/subpipelines/critique.py
pipelines/subpipelines/revision.py
pipelines/subpipelines/validation.py
pipelines/subpipelines/persistence.py
tests/test_generation_flow.py
```

### Estrategia

Nao mover tudo de uma vez.

Ordem:

1. extrair preparacao;
2. extrair drafting;
3. extrair critica;
4. extrair sintese/revisao;
5. extrair validacao;
6. extrair persistencia/git.

Cada extracao deve manter testes existentes passando.

### Fora De Escopo

- Nao adicionar `production_planning` ainda.
- Nao mudar formato dos capitulos.
- Nao mudar criterio de score.

### Testes Necessarios

- testes atuais de generation flow adaptados;
- testes unitarios para cada subpipeline;
- mocks para LLM, evaluate e git.

### Criterios De Aceite

- comportamento externo preservado;
- codigo fica reutilizavel;
- cada subpipeline tem teste proprio;
- feedback lifecycle continua valido.

### Tarefa Boa Para Modelo Medio

Parcialmente. Deve ser dividida em varias tarefas pequenas. Supervisor deve
revisar cada extracao.

## Fase 10: Production Planning [ROADMAP PRELIMINAR]

> [!WARNING]
> **Fase de Roadmap:** Esta fase faz parte do roadmap preliminar e **não deve ser executada** antes da aprovação do Gate A. Ela só deve ser detalhada após a consolidação completa das fases anteriores de infraestrutura (registry, discovery e branch workflow).

### Objetivo

Implementar a pipeline `production_planning` proposta em `docs/analises/recomendacao_pipeline_producao.md` já utilizando a base refatorada.

**Regra Crítica de Segurança:**
A pipeline `production_planning` **só deve gerar/salvar artefatos de obra dentro de um branch dedicado da obra** (ex: `autobook/<slug>`). Fica terminantemente proibido gerar ou persistir artefatos de produção diretamente na branch `main` ou `master`, salvo em execuções de testes automatizados locais ou modo dry-run explicitamente controlado.

### Pre-requisitos

- pipeline registry;
- contratos de pipeline;
- discovery;
- prompt layout;
- agent registry basico;
- subpipelines/gates ou base pronta para eles.

### Entregas

```text
pipelines/production_planning.py
book_data/production/
tests/test_production_planning.py
docs/production-planning.md
```

### Artefatos

```text
scope_plan.json
chapter_plan.json
style_contract.md
style_metrics.json
continuity_graph.json
agent_roster.json
validation_rubrics.json
retrieval_index.json
```

### Fora De Escopo

- Nao substituir completamente `book_generation` na primeira versao.
- Nao exigir que todos os artefatos sejam perfeitos no v1.

### Testes Necessarios

- cria diretorio `book_data/production/`;
- gera artefatos com mocks de LLM;
- valida JSON minimo;
- falha com mensagem clara quando entradas faltam;
- registry lista nova pipeline.

### Criterios De Aceite

- pipeline executa com LLM mockado;
- artefatos sao validaveis;
- docs explicam como consumir os artefatos;
- `run.py --pipeline production_planning` funciona.

### Tarefa Boa Para Modelo Medio

Moderada/alta. Deve ser implementada apos as fases anteriores.

## Fase 11: Wizard Como Area De Trabalho [ROADMAP PRELIMINAR]

> [!WARNING]
> **Fase de Roadmap:** Esta fase faz parte do roadmap preliminar e **não deve ser executada** antes da aprovação do Gate A.

### Objetivo

Transformar `run.py` sem argumentos em area de trabalho interativa.

### Pre-requisitos

- pipeline registry;
- discovery;
- branch workflow;
- production planning ou stub claro.

### Capacidades Iniciais

- mostrar branch atual;
- avisar se esta em `main`;
- listar estado da obra;
- listar proximos passos possiveis;
- criar branch de obra mediante confirmacao;
- chamar pipelines existentes;
- mostrar comandos equivalentes antes de executar.

### Fora De Escopo

- UI sofisticada;
- dependencia pesada de TUI;
- automacao destrutiva sem confirmacao.

### Testes Necessarios

- input mockado;
- descoberta mockada;
- chamadas de pipeline mockadas;
- branch creation mockada;
- nenhum teste deve trocar branch real.

### Criterios De Aceite

- `uv run python run.py` abre wizard.
- `uv run python run.py --pipeline ...` continua funcionando.
- wizard nao tem lista hardcoded de pipelines; usa registry/discovery.

### Tarefa Boa Para Modelo Medio

Sim, se discovery e registry ja existirem.

## Fase 12: Revisao De Docs E README [ROADMAP PRELIMINAR]

> [!WARNING]
> **Fase de Roadmap:** Esta fase faz parte do roadmap preliminar e **não deve ser executada** antes da aprovação do Gate A.

### Objetivo

Atualizar documentacao e README apos as mudancas estruturais globais.

> [!IMPORTANT]
> **Regra Geral de Atualização de Documentos:**
> - Qualquer fase do projeto que altere o comportamento público (CLI, comandos operacionais, formatos de arquivos, APIs públicas de pipeline ou agente) deve obrigatoriamente incluir a atualização incremental dos documentos operacionais na mesma entrega.
> - A Fase 12 funciona como um esforço final de consolidação, auditoria e revisão geral, mas **não substitui** o dever de documentar incrementalmente cada alteração em sua respectiva fase.

### Arquivos

```text
README.md
docs/INDICE.md
docs/SNAPSHOT_V0.md
docs/operacional/comandos.md
docs/pipelines/pipelines.md
docs/agents/agentes.md
docs/configuration/configuration.md
```

### Criterios De Aceite

- README nao promete comandos inexistentes.
- Docs explicam branch por obra.
- Docs explicam wizard.
- Docs explicam pipeline registry.
- Docs explicam agent registry e prompts externos.
- Baseline de testes atualizado.

### Tarefa Boa Para Modelo Medio

Sim, mas supervisor deve checar contra codigo real.

## Politica De Supervisao

O supervisor deve rejeitar entregas que:

- fazem refactor amplo demais;
- removem compatibilidade sem justificativa;
- alteram comportamento sem teste;
- adicionam agentes/prompts sem uso real;
- deixam feedback de agente sem consumidor;
- executam Git real em testes;
- usam `legacy/tests` como baseline;
- atualizam docs sem checar codigo;
- implementam wizard com listas hardcoded que deveriam vir de discovery.

## Template De Tarefa Para Modelo Medio

Use este modelo ao delegar:

```text
Tarefa: <nome curto>

Leia antes:
- <docs>
- <arquivos>

Objetivo:
<comportamento desejado>

Fora de escopo:
- <lista>

Arquivos que pode alterar:
- <lista>

Requisitos:
- <lista objetiva>

Testes obrigatorios:
- <comandos>

Criterios de aceite:
- <lista>

Ao final, responda:
- arquivos alterados
- testes rodados
- riscos ou duvidas
```

## Primeira Tarefa Recomendada Para Delegar

Comecar pela Fase 0:

```text
Criar specs em docs/planejamento/refactor-plataforma/
sem alterar codigo.
```

Motivo: e uma tarefa segura para calibrar o executor medio e produzir contexto
melhor antes de mexer na base.

## Specs Quebradas Por Fase

As fases foram quebradas em documentos menores em:

```text
docs/planejamento/refactor-plataforma/fases/
```

Use essas specs como unidade primaria de delegacao. Este documento permanece
como plano mestre e referencia de supervisao.

## Conclusao

O plano e viavel, mas depende de disciplina de escopo. Modelos medios devem
executar tarefas pequenas e verificaveis. O supervisor deve manter a coerencia
arquitetural, revisar diffs e impedir que o projeto acumule automacoes
incompletas ou agentes sem uso efetivo.
