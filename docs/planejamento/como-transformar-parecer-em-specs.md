# Como Transformar o Parecer em Especificacoes de Implementacao

Este documento define como evoluir a recomendacao registrada em
`docs/analises/recomendacao_pipeline_producao.md` para documentos que possam
orientar alteracoes de codigo por qualquer modelo ou desenvolvedor.

## Objetivos

1. Preservar o raciocinio ja feito sobre falhas e direcao arquitetural.
2. Evitar que uma implementacao futura dependa de memoria da conversa.
3. Criar specs pequenas, verificaveis e executaveis.
4. Permitir migracao incremental do projeto sem reescrever tudo de uma vez.

## Estrutura Recomendada de Specs

Criar, quando formos implementar, uma pasta:

```text
docs/planejamento/production-planning/
```

Com documentos separados:

```text
00-contexto-e-decisao.md
01-artefatos-production.md
02-pipeline-production-planning.md
03-chapter-packet.md
04-book-generation-gates.md
05-continuity-graph.md
06-style-contract.md
07-agent-roster-routing.md
08-plano-de-migracao.md
09-testes-e-criterios-de-aceite.md
```

## Papel De Cada Documento

### `00-contexto-e-decisao.md`

Resumo curto da decisao:

- problema;
- premissas;
- alternativas consideradas;
- decisao adotada;
- o que nao sera feito agora.

### `01-artefatos-production.md`

Contrato dos arquivos em `book_data/production/`:

- nome;
- formato;
- campos obrigatorios;
- campos opcionais;
- exemplos;
- quem le;
- quem escreve;
- quando e atualizado.

### `02-pipeline-production-planning.md`

Spec da nova pipeline:

- entrada;
- saida;
- steps;
- ordem de execucao;
- erros esperados;
- comportamento quando arquivos ja existem;
- CLI esperada.

### `03-chapter-packet.md`

Define o pacote de contexto por capitulo:

- fonte dos dados;
- tamanho maximo recomendado;
- secoes obrigatorias;
- diferenca entre contexto de escrita e contexto de validacao;
- exemplos.

### `04-book-generation-gates.md`

Define o novo fluxo de geracao:

- preflight;
- drafting;
- extracao de delta;
- validacao;
- revisao;
- aceite;
- commit.

Cada gate deve declarar:

- entrada;
- saida;
- criterio de bloqueio;
- criterio de aviso;
- log produzido.

### `05-continuity-graph.md`

Define o modelo de continuidade:

- eventos;
- timeline;
- personagens;
- objetos;
- locais;
- conhecimento do leitor;
- conhecimento dos personagens;
- fios abertos.

### `06-style-contract.md`

Define como representar estilo:

- regras textuais;
- exemplos positivos/negativos;
- metricas mecanicas;
- limites aceitaveis;
- como detectar drift.

### `07-agent-roster-routing.md`

Define os papeis genericos e os gatilhos de ativacao:

- agentes sempre ativos;
- agentes condicionais;
- formato de prompt;
- formato de resposta;
- custo esperado;
- fallback quando o especialista falha.

### `08-plano-de-migracao.md`

Plano incremental:

1. adicionar artefatos sem mudar geracao;
2. gerar chapter packets;
3. adicionar validacao de continuidade local;
4. adicionar style drift;
5. adicionar roteamento de especialistas;
6. trocar fluxo antigo de `book_generation` por gates.

### `09-testes-e-criterios-de-aceite.md`

Define como provar que a mudanca funciona:

- testes unitarios;
- testes de parser;
- testes de roteamento;
- testes sem LLM;
- testes com mock de LLM;
- cenarios regressivos;
- criterios de qualidade.

## Padrao Para Cada Spec

Cada documento de especificacao deve seguir este formato:

```text
# Titulo

## Objetivo
## Fora de Escopo
## Estado Atual
## Comportamento Desejado
## Arquivos Afetados
## Contratos de Entrada
## Contratos de Saida
## Fluxo
## Erros e Fallbacks
## Testes Necessarios
## Criterios de Aceite
## Perguntas Abertas
```

## Regras Para Modelos Que Forem Implementar

Um modelo futuro deve:

- ler primeiro `docs/INDICE.md`;
- ler `docs/SNAPSHOT_V0.md`;
- ler `docs/analises/recomendacao_pipeline_producao.md`;
- ler a spec especifica da tarefa;
- inspecionar o codigo atual antes de editar;
- fazer mudancas incrementais;
- manter compatibilidade com o fluxo existente quando possivel;
- adicionar ou atualizar testes proporcionais ao risco;
- nao corrigir tudo em uma unica alteracao grande.

## Ordem Recomendada Para Discussao Futura

1. Definir o contrato de `book_data/production/`.
2. Definir `scope_plan.json` e `chapter_plan.json`.
3. Definir `continuity_graph.json`.
4. Definir `style_contract.md` e `style_metrics.json`.
5. Definir `agent_roster.json`.
6. Definir como `book_generation` consome esses arquivos.
7. So depois implementar.

## Decisao De Documentacao

Este documento nao e uma spec final. Ele e um guia para criar specs finais.
O parecer consolidado esta em:

```text
docs/analises/recomendacao_pipeline_producao.md
```

