# Auditoria Senior de Codigo - Autobook

Data: 2026-06-16

Este documento registra uma auditoria tecnica do codigo atual do Autobook com
foco em arquitetura, manutenibilidade, clean code, SOLID, code smells, riscos
funcionais e aderencia a documentacao operacional. Ele nao e um plano de
implementacao ainda; e o inventario de problemas e decisoes pendentes para
guiar a proxima rodada de planejamento.

## Escopo e Metodo

Foram analisados:

- entrada CLI e wizard: `run.py`, `cli/`, `workspace/`;
- pipelines: `pipelines/` e subpacotes `*_steps/`;
- agentes e prompts: `agents.py`, `agent_system/`, `prompt_loader.py`,
  `prompts/`;
- avaliacao, continuidade e scripts auxiliares: `evaluate.py`,
  `verify_continuity.py`, `resolve_continuity.py`, scripts de raiz e
  `legacy/`;
- documentacao operacional em `README.md` e `docs/`;
- testes modernos e testes legados.

Validacoes executadas durante a auditoria:

```bash
uv run --with pytest pytest tests -q
# 274 passed

uv run python -m compileall -q run.py pipelines agent_system cli workspace writing agents.py llm.py prompt_loader.py evaluate.py verify_continuity.py resolve_continuity.py typeset skills
# sucesso

uv run --with pytest pytest legacy/tests -q
# falha na coleta por imports legados removidos/renomeados
```

Tambem foram feitas buscas estaticas por arquivos, imports mortos, funcoes
duplicadas e divergencias entre documentacao e codigo. A analise estatica de
imports foi heuristica; os achados precisam ser tratados como candidatos antes
de remocao automatica.

## Resumo Executivo

O projeto passou por uma refatoracao importante e a suite moderna esta verde,
mas ainda ha dividas relevantes para considerar o codigo pronto como plataforma
generica de escrita.

Os principais riscos sao:

- partes criticas de continuidade ainda quebradas ou apontando para comandos
  inexistentes;
- hardcodes de obras especificas em prompts, avaliadores e scripts;
- documentacao principal parcialmente alinhada, mas ainda com comandos e
  caminhos historicos que podem induzir erro;
- scripts raiz e legacy sem fronteira clara entre ferramenta suportada,
  experimento e codigo obsoleto;
- excesso de logica em modulos grandes (`evaluate.py`, `foundation.py`,
  `cli/wizard.py`, `agents.py`);
- alguns fluxos aparentam funcionar nos testes unitarios, mas dependem de
  subprocessos Git, arquivos de obra e estado local que ainda nao tem contratos
  fortes.

## Achados Criticos

### C01 - `resolve_continuity.py` esta funcionalmente quebrado

Arquivos: `resolve_continuity.py`, `verify_continuity.py`,
`docs/continuity/continuity.md`, `docs/SNAPSHOT_V0.md`.

Problemas encontrados:

- ha duas funcoes `main()` no mesmo arquivo; a segunda sobrescreve a primeira;
- o script procura `eval_logs/continuity_report.json` na raiz, mas
  `verify_continuity.py` escreve em `logs/eval_logs/continuity_report.json`;
- o script tenta chamar `run_editorial.py`, que nao existe mais;
- os testes legados tambem tentam importar fluxos removidos como
  `run_editorial` e `run_pipeline`.

Impacto: o loop fechado de continuidade nao e confiavel. A documentacao ja
adverte parte disso, mas o arquivo continua no projeto como se fosse utilizavel.

Recomendacao: decidir se `resolve_continuity.py` sera migrado para
`run.py --pipeline editorial_revision --chapter ...`, reescrito como modulo
testavel, ou movido para `legacy/` como quebrado/historico.

### C02 - Caminho errado para `CRAFT.md` na pipeline foundation

Arquivo: `pipelines/foundation.py`.

O codigo usa `BASE_DIR / "doc" / "CRAFT.md"`, mas o arquivo real fica em
`docs/others/CRAFT.md`. Como o helper de leitura retorna string vazia quando o
arquivo nao existe, a pipeline segue sem erro e o prompt perde silenciosamente
as regras de craft.

Impacto: a fundacao gerada pode sair pior sem que teste ou log indiquem o
problema. Tambem ha divergencia com `README.md`, que ainda cita `doc/` na
estrutura.

Recomendacao: corrigir o caminho ou mover esse conteudo para um local de prompt
configuravel, com teste que falhe quando o arquivo essencial estiver ausente.

### C03 - A plataforma ainda nao e generica para qualquer obra

Arquivos principais: `pipelines/foundation.py`, `evaluate.py`,
`gen_audiobook_script.py`, `book_data/`, `docs/others/*`.

Ha referencias fortes a obras especificas e universos concretos:

- `foundation.py` contem prompts de fundacao com nomes, mundo e regras de uma
  obra especifica;
- `evaluate.py` contem rubricas com elementos como `ECO-9`, vigilancia por
  implantes, `Marina`, `Cass` e regras de mundo especificas;
- `gen_audiobook_script.py` tem personagens fixos;
- `book_data/` versiona artefatos de uma obra atual ou exemplo.

Impacto: o projeto se apresenta como framework de escrita, mas parte da logica
de producao e avaliacao ainda carrega vies especifico. Isso afeta qualidade,
reuso e confiabilidade quando o usuario tenta criar outra obra.

Recomendacao: separar claramente `template/framework`, `sample_project` e
`workspace de obra`. Hardcodes devem migrar para prompts/configs por obra ou
para `book_data/production/` quando a pipeline de planejamento existir.

### C04 - `book_data/` versionado conflita com a regra de main limpa

Arquivos: `book_data/*`, `workspace/project.py`, `workspace/branching.py`,
`run.py`, documentacao operacional.

A regra nova exige que geracoes de obra acontecam em branches `autobook/<slug>`
e que `main/master` fiquem limpas. Porem `book_data/` esta versionado com
conteudo de obra. Isso pode ser intencional como exemplo, mas o projeto nao
declara essa decisao de forma suficientemente forte no codigo.

Impacto: novos usuarios podem confundir dados exemplo com estado real da obra.
Tambem dificulta validar se uma branch principal esta realmente limpa de
artefatos autorais.

Recomendacao: decidir entre manter `book_data/` como fixture exemplar
documentada ou mover dados de obra para um workspace nao versionado/exemplo
separado.

## Achados Altos

### A01 - `main.py` e um entrypoint falso

Arquivo: `main.py`.

O arquivo imprime apenas `Hello from autobook!`, enquanto a entrada real e
`run.py`. Isso e ruido operacional e pode confundir ferramentas, usuarios e
modelos automatizados.

Recomendacao: remover, converter para delegar a `run.main()`, ou documentar
explicitamente como stub nao suportado. A melhor opcao e delegar a `run.py` se
o empacotamento exigir `main.py`.

### A02 - Testes legados quebram na coleta

Arquivos: `legacy/tests/*`, `legacy/*`.

`legacy/tests` nao pertence ao baseline atual, mas esta no repositorio e falha
ao coletar por imports de modulos inexistentes. Isso e aceitavel apenas se a
pasta estiver claramente marcada como historica e excluida do workflow.

Recomendacao: mover testes legados para documentacao/arquivo morto, corrigir
imports para refletir scripts reais, ou configurar explicitamente o pytest para
nao coleta-los.

### A03 - `evaluate.py` e um god module com regras de dominio misturadas

Arquivo: `evaluate.py`.

O modulo tem mais de mil linhas e mistura:

- configuracao de juiz;
- deteccao mecanica de slop;
- prompts longos;
- chamadas LLM;
- reparo de JSON;
- carregamento de capitulos;
- avaliacao de capitulos e livro;
- CLI.

Tambem ha parametros pouco confiaveis, como `call_judge(..., max_tokens=...)`
sem repasse efetivo de `max_tokens` para `llm.call_llm`, e rubricas de canon
presas a obras especificas.

Impacto: alto custo de manutencao e risco de alterar uma regra de avaliacao e
quebrar outro fluxo. A avaliacao e central para qualidade, logo esse modulo
precisa virar uma area bem contratada.

Recomendacao: dividir em pacotes (`evaluation/config.py`,
`evaluation/slop.py`, `evaluation/prompts.py`, `evaluation/judge.py`,
`evaluation/reports.py`) antes de evoluir novas metricas.

### A04 - `foundation.py` ainda concentra prompts e responsabilidades demais

Arquivo: `pipelines/foundation.py`.

Apesar da extracao de helpers, o arquivo ainda contem prompts longos, logica de
geracao de varias bíblias e detalhes de commit. As instrucoes de fundacao
tambem estao acopladas a um tipo de obra.

Impacto: qualquer mudanca de estilo, genero ou estrutura de fundacao exige
editar codigo Python em vez de artefatos de prompt/configuracao.

Recomendacao: externalizar prompts de foundation por idioma/genero e manter no
codigo apenas orquestracao, contratos de entrada/saida e persistencia.

### A05 - Git e subprocessos nao tem contrato uniforme de erro

Arquivos: `pipelines/book_generation_steps/persistence.py`,
`pipelines/editorial_revision_steps/revision.py`,
`pipelines/foundation_steps/persistence.py`, `workspace/branching.py`.

Ha diferencas importantes:

- algumas chamadas usam `check=True`;
- outras fazem `git add`, `commit` e `push` sem verificar retorno;
- alguns fluxos capturam excecao e continuam;
- outros propagam erro;
- `run_continuity_and_git_push` pode registrar sucesso parcial sem garantir
  que commit/push foram aplicados.

Impacto: a CLI pode parecer ter completado uma etapa, mas o repositorio pode
nao conter commit/push correspondente.

Recomendacao: criar um adaptador Git unico com politicas explicitas:
read-only, criar branch, commit obrigatorio, commit tolerante a "nothing to
commit", push opcional e mensagens padronizadas.

### A06 - Interatividade da ideation bloqueia automacao real

Arquivo: `pipelines/ideation.py`.

A pipeline chama `input()` diretamente em varios passos. Isso impede execucao
nao interativa limpa via CI, wizard ou modelos delegados, mesmo quando `run.py`
tem flags como `--yes`.

Impacto: o wizard consegue iniciar execucao, mas pode travar em prompts de
terminal internos nao coordenados.

Recomendacao: separar perguntas em uma camada de interface e transformar a
pipeline em fluxo parametrizavel por contexto/configuracao.

### A07 - `llm.py` encerra o processo em vez de sinalizar erro

Arquivo: `llm.py`.

`call_llm` usa `sys.exit(1)` em alguns erros de configuracao. Isso acopla uma
biblioteca de infraestrutura ao processo CLI e dificulta testes, reuso e
tratamento por pipelines.

Impacto: pipelines nao conseguem decidir fallback, retry externo ou mensagem de
erro contextual quando a falha vem da camada LLM.

Recomendacao: trocar `sys.exit` por excecoes tipadas e deixar `run.py` decidir
como apresentar a falha ao usuario.

### A08 - Registro moderno de agentes ainda e um adapter sobre legado

Arquivos: `agent_system/*`, `agents.py`.

`agent_system` introduz contratos e registry, mas a factory moderna delega para
o singleton legado em `agents.py` e acessa `_agents_registry` diretamente. Alem
disso, `BaseAgent` ainda nao e uma base real dos agentes concretos.

Impacto: a arquitetura documentada e parcialmente aspiracional. O sistema
funciona, mas ainda nao ha separacao clara entre contrato moderno e legado.

Recomendacao: manter o adapter por enquanto, mas registrar como divida
arquitetural. A migracao completa deve acontecer depois que prompts e skills
estiverem estabilizados.

### A09 - Fallbacks silenciosos podem ocultar dados essenciais ausentes

Arquivos: `pipelines/book_generation_steps/context.py`,
`pipelines/foundation_steps/context.py`, `prompt_loader.py`.

Exemplos:

- outline ausente ou malformado pode cair em total fixo de 22 capitulos;
- capitulo sem outline vira `Capitulo N`;
- arquivos de fundacao ausentes podem virar string vazia;
- prompt de agente ausente cai para fallback hardcoded.

Impacto: o sistema continua rodando, mas com contexto degradado, o que reduz
qualidade e dificulta diagnostico.

Recomendacao: diferenciar fallback toleravel de input obrigatorio. Para dados
estruturais da obra, preferir erro claro ou modo `--allow-degraded-context`.

## Achados Medios

### M01 - Wizard cresceu para alem de uma camada de UI

Arquivo: `cli/wizard.py`.

O wizard ja mistura exibicao de estado, montagem de comando, escolha de
pipeline, criacao de branch, escrita de workspace metadata e chamada de
`run.main(argv)`.

Recomendacao: extrair helpers de apresentacao, selecao e execucao para
facilitar testes e futuras telas sem transformar o wizard em novo god module.

### M02 - `run.py` altera `sys.stdout` e `sys.stderr` globalmente

Arquivo: `run.py`.

O `Tee` global resolve logging simples, mas abre arquivos sem ciclo de vida
claro e altera streams globais dentro de `main()`. Isso pode impactar testes,
subexecucoes e uso como biblioteca.

Recomendacao: mover logging para `logging` padrao ou usar contexto controlado
no CLI.

### M03 - Prompts hardcoded continuam espalhados

Arquivos: `pipelines/foundation.py`, `evaluate.py`, `verify_continuity.py`,
`gen_brief.py`, `gen_revision.py`, `agents.py`.

Agentes principais ja carregam prompts externos, mas varias partes criticas
ainda possuem prompts longos dentro de Python.

Recomendacao: criar uma politica unica para prompts: todo prompt operacional
deve estar em `prompts/{LANG}/...`, com testes de placeholders.

### M04 - Duplicacao de reparo/parse de JSON LLM

Arquivos: `evaluate.py`, `verify_continuity.py`,
`pipelines/editorial_revision_steps/parsing.py`.

Ha varias rotinas de extracao/reparo de JSON ou parsing tolerante de resposta
LLM. Isso cria comportamento inconsistente.

Recomendacao: criar modulo comum `llm_json.py` ou `utils/structured_output.py`
com politicas e testes compartilhados.

### M05 - Ordenacao de criticas na revisao depende de nome de arquivo

Arquivo: `pipelines/book_generation_steps/revision.py`.

`list_critique_files` ordena alfabeticamente. Isso pode nao refletir a ordem
editorial desejada dos criticos ou a ordem declarada em `critics_roles`.

Recomendacao: ordenar por `critics_roles` quando disponivel e deixar ordem
alfabetica apenas como fallback.

### M06 - `RevisionPlan` existe, mas o feedback ainda nao e realmente estruturado

Arquivos: `writing/feedback.py`,
`pipelines/book_generation_steps/critique.py`,
`pipelines/book_generation_steps/revision.py`.

As criticas sao convertidas para um unico `CriticFinding` com severidade
`medium` e texto completo. Isso e um passo bom de compatibilidade, mas ainda
nao entrega feedback granular.

Recomendacao: evoluir prompts de criticos para saida estruturada validada e
usar `RevisionPlan` para orientar a revisao por item.

### M07 - Workspace metadata valida pouco conteudo semantico

Arquivo: `workspace/project.py`.

O contrato valida campos obrigatorios e `schema_version`, mas nao valida se
`created_at` e ISO parseavel nem se `branch` segue `autobook/<slug>`.

Recomendacao: reaproveitar `is_book_branch` e validar data ISO para tornar o
arquivo confiavel como fonte de estado.

### M08 - `pyproject.toml` nao declara ferramentas de qualidade

Arquivo: `pyproject.toml`.

O projeto usa testes com `uv run --with pytest`, mas `pytest` nao esta nas
dependencias/dev dependencies do projeto. Tambem nao ha configuracao de linter,
formatter, type checker ou coverage.

Recomendacao: adicionar grupo dev para `pytest`, e avaliar `ruff`, `mypy` ou
`pyright` em modo gradual.

### M09 - Documentacao ainda mistura estado atual e material historico

Arquivos: `README.md`, `docs/INDICE.md`,
`docs/fluxo-detalhado/guia-completo-fluxos.md`,
`docs/legacy/legacy.md`, `docs/continuity/continuity.md`.

O indice melhorou, mas ainda existem comandos historicos, caminhos antigos e
promessas nao suportadas. O `README.md`, por exemplo, ainda menciona `doc/` na
estrutura e "full pipeline from scratch" de forma simplificada demais para a
nova regra de branch e fundacao.

Recomendacao: marcar documentos historicos com cabecalho explicito ou reduzir
o README a comandos suportados e testados.

## Achados Baixos e Higiene

### B01 - Imports mortos candidatos

Candidatos detectados por analise estatica simples:

- `adversarial_edit.py`: `os`;
- `agents.py`: `List`;
- `compare_chapters.py`: `os`, `random`;
- `gen_audiobook_script.py`: `os`;
- `gen_revision.py`: `os`;
- `genre_strategy.py`: `Dict`;
- `pipelines/editorial_revision_steps/config.py`: `Path`;
- `prompt_loader.py`: `Dict`, `Any`;
- `resolve_continuity.py`: `os`.

Alguns imports em `__init__.py` e reexports publicos foram ignorados de forma
intencional. Antes de remover, rodar testes e confirmar que nao sao usados via
efeito colateral.

### B02 - Uso inconsistente de `encoding`

Ha leituras/escritas com `read_text()` ou `open()` sem encoding explicito em
scripts de raiz e typeset. O projeto opera com conteudo literario e portugues,
entao `encoding="utf-8"` deveria ser padrao.

### B03 - Mensagens misturam portugues com e sem acentos

Varios erros usam ASCII por historico do projeto, enquanto outros textos de
wizard/documentacao usam portugues acentuado. Nao e bug funcional, mas a
experiencia fica inconsistente.

### B04 - Arquivos raiz precisam de classificacao

Scripts como `gen_brief.py`, `gen_revision.py`, `adversarial_edit.py`,
`apply_cuts.py`, `compare_chapters.py`, `voice_fingerprint.py` e
`gen_audiobook_script.py` podem ser uteis, mas hoje nao ha fronteira clara
entre ferramenta suportada, experimento, script legado e comando operacional.

## Aderencia a Documentacao

Pontos alinhados:

- `run.py` e o entrypoint real;
- pipelines atuais registradas: `ideation`, `foundation`, `book_generation`,
  `editorial_revision`;
- wizard sem argumentos existe e e interativo;
- branch guard para pipelines protegidas existe;
- baseline moderno de testes esta documentado como 274 testes;
- `legacy/tests` esta fora do baseline moderno.

Pontos divergentes ou incompletos:

- `README.md` ainda cita estrutura `doc/`, mas o projeto usa `docs/`;
- comandos de "pipeline completa do zero" precisam considerar branch
  `autobook/<slug>` e precondicoes de fundacao;
- documentacao de continuidade reconhece problemas, mas o script quebrado
  continua como codigo ativo;
- docs historicos em `docs/fluxo-detalhado/` ainda podem ser lidos como
  operacionais apesar de conterem comandos/flags antigos;
- a documentacao de arquitetura descreve a direcao moderna, mas o sistema de
  agentes ainda depende do legado.

## Recomendada Sequencia de Tratamento

1. Corrigir ou aposentar os quebrados obvios:
   `resolve_continuity.py`, `main.py`, caminho de `CRAFT.md`, testes legados.
2. Separar codigo generico de artefatos de obra especifica:
   `book_data/`, prompts de `foundation.py`, rubricas de `evaluate.py`,
   audiobook.
3. Endurecer contratos de execucao:
   Git adapter, LLM exceptions, inputs obrigatorios vs fallbacks.
4. Refatorar modulos grandes:
   primeiro `evaluate.py`, depois `foundation.py`, depois `cli/wizard.py`.
5. Evoluir qualidade real:
   feedback estruturado, critic routing, production planning e validacoes por
   contrato de estilo/continuidade.

O arquivo complementar
`docs/analises/auditoria_codigo_backlog_2026-06-16.md` transforma estes achados
em uma lista acionavel para planejamento.
