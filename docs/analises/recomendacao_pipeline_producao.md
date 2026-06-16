# Recomendacao: Pipeline de Planejamento de Producao

Este documento registra a analise e a recomendacao arquitetural discutida apos
o snapshot v0 da documentacao. Ele deve servir como memoria de contexto para
qualquer modelo ou pessoa que retome o projeto no futuro.

## Objetivo

Melhorar a qualidade da geracao de livros no Autobook sem depender de modelos
topo de linha em todas as etapas.

O sistema deve assumir que:

- os modelos usados podem variar em capacidade;
- por custo, o mesmo modelo pode ser usado para escrita e revisao;
- modelos grandes ainda podem perder informacao relevante em contexto longo;
- aumentar o numero de chamadas e aceitavel se isso melhorar controle,
  continuidade e qualidade;
- prompts extensos e genericos nao sao suficientes para resolver continuidade,
  ritmo e especializacao.

## Problemas Observados

### Continuidade

Durante a geracao de capitulos, ocorreram:

- repeticoes desnecessarias de descobertas, debates ou eventos;
- quebras de linha temporal;
- inconsistencias de estado de personagem, local, objeto ou conhecimento;
- agentes de conferencia deixando passar problemas importantes.

Diagnostico: a continuidade nao pode depender apenas de um critico lendo prosa
longa. Ela precisa de estado estruturado, verificacoes antes da escrita e
extracao de fatos depois da escrita.

### Quantidade vs Qualidade

O numero de capitulos nao deve ser fixo. Ele precisa derivar de:

- quantidade de material narrativo;
- densidade de mundo;
- quantidade de arcos de personagem;
- numero de fios de misterio/subtrama;
- estilo desejado;
- tamanho alvo do livro;
- ritmo pretendido.

Diagnostico: um outline fixo de 22 capitulos empurra livros simples para
enchimento e livros complexos para compressao artificial.

### Falha de Papeis Especializados

Agentes especializados em pesquisa, matematica, direito, medicina, tecnologia
ou qualquer dominio especifico nao devem atuar em todo capitulo, mas tambem nao
podem faltar quando o capitulo depende desse dominio.

Diagnostico: o sistema precisa de roteamento dinamico por capitulo/cena, com
gatilhos explicitos de especialidade.

### Falha de Ritmo e Estilo

O estilo costuma aparecer nos primeiros capitulos e se diluir nos seguintes,
resultando em prosa generica.

Diagnostico: estilo precisa virar contrato persistente e mensuravel. Nao basta
repetir "escreva no estilo X" dentro do prompt.

## Decisao Recomendada

Adotar uma linha hibrida:

> Manter papeis genericos no codigo, mas criar uma pipeline intermediaria que
> gere uma configuracao especifica de producao para cada livro.

Nao recomendamos:

- criar agentes totalmente customizados por livro como codigo novo permanente;
- usar um grande conjunto fixo de agentes agnosticos atuando sempre em todos os
  livros e capitulos;
- depender de um unico juiz LLM amplo para validar qualidade e continuidade.

Recomendamos:

- papeis genericos estaveis;
- prompts e checklists especificos por livro;
- roteamento dinamico de especialistas;
- memoria estruturada de continuidade;
- contratos de estilo;
- gates de validacao antes e depois da escrita.

## Nova Pipeline Proposta

Inserir uma etapa entre `foundation` e `book_generation`:

```text
ideation
foundation
production_planning
book_generation
editorial_revision
continuity_resolution
typeset/export
```

Nome sugerido:

```text
production_planning
```

Responsabilidade: transformar os documentos de fundacao em um plano operacional
de producao do livro.

## Artefatos Esperados

Diretorio sugerido:

```text
book_data/production/
```

Arquivos sugeridos:

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

### `scope_plan.json`

Define tamanho e escopo:

- faixa de palavras alvo;
- numero de capitulos sugerido;
- justificativa para o numero de capitulos;
- media aproximada de palavras por capitulo;
- densidade de subtramas;
- ritmo esperado.

### `chapter_plan.json`

Substitui ou complementa o outline fixo. Cada capitulo deve ter funcao
narrativa clara:

- objetivo dramático;
- cenas/beats;
- mudancas de estado;
- informacoes reveladas;
- promessas plantadas;
- promessas pagas;
- especialistas potencialmente necessarios.

### `style_contract.md`

Contrato de voz e ritmo do livro:

- exemplos positivos;
- exemplos negativos;
- cadencia;
- densidade de dialogo;
- densidade sensorial;
- nivel de introspeccao;
- padroes de abertura/fechamento;
- vocabulario recorrente permitido;
- vocabulario proibido;
- regras por tipo de cena.

### `style_metrics.json`

Metricas mecanicas para acompanhar drift:

- tamanho medio de frase;
- variacao de tamanho de frase;
- proporcao de dialogo;
- densidade de termos de estilo;
- densidade de abstracoes;
- densidade de travessoes;
- repeticoes;
- sinais de prosa generica.

### `continuity_graph.json`

Estado estruturado do livro:

- linha temporal;
- eventos;
- estado dos personagens;
- estado de objetos;
- locais;
- conhecimento do leitor;
- conhecimento de cada personagem;
- fios abertos;
- fatos canonicos.

### `agent_roster.json`

Equipe dinamica do livro:

- agentes sempre ativos;
- agentes condicionais;
- gatilhos de ativacao;
- entradas que cada agente recebe;
- saidas esperadas;
- formato de resposta.

### `validation_rubrics.json`

Rubricas especificas do livro:

- continuidade;
- estilo;
- pacing;
- aderencia a genero;
- qualidade de cena;
- especialidades tecnicas;
- criterios minimos de aceite.

### `retrieval_index.json`

Indice de recuperacao de contexto:

- quais fontes consultar por tipo de cena;
- quais secoes de `world.md`, `characters.md`, `canon.md` e `voice.md` sao
  relevantes para cada capitulo;
- como montar pacotes curtos de contexto.

## Principio Para Modelos Menores ou Mais Baratos

O sistema deve reduzir a dificuldade de cada chamada ao modelo.

Preferir:

- tarefas pequenas;
- prompts curtos;
- saidas estruturadas;
- checklists objetivos;
- validacoes mecanicas;
- comparacoes locais;
- varias chamadas simples.

Evitar:

- prompts gigantes;
- "julgue a qualidade do livro inteiro";
- pedir raciocinio literario amplo sem estrutura;
- usar a biblia completa como contexto padrao;
- confiar em um unico agente de conferencia.

Exemplo de tarefa ruim:

```text
Leia tudo e diga se ha problemas de continuidade.
```

Exemplo de tarefa melhor:

```text
Compare o estado final do capitulo 4, o plano do capitulo 5 e o texto gerado
do capitulo 5. Responda em JSON:
- o personagem sabe algo que nao deveria?
- algum evento foi repetido?
- algum objeto mudou de posse/local?
- a sequencia temporal e possivel?
```

## Fluxo Recomendado Por Capitulo

Fluxo-alvo para uma versao futura de `book_generation`:

```text
1. Build chapter packet
2. Plan scenes
3. Continuity preflight
4. Specialist routing
5. Draft beat(s)
6. Extract factual delta
7. Continuity validation
8. Style drift validation
9. Specialist validation
10. Revision synthesis
11. Final evaluation
12. Commit chapter and update state
```

## Gates Recomendados

### Continuity Preflight

Antes de escrever:

- verificar estado anterior;
- verificar o que o capitulo deve mudar;
- impedir repeticao de descoberta;
- listar fatos que nao podem ser contraditos.

### Factual Delta Extraction

Depois de escrever:

- extrair eventos novos;
- extrair mudancas de estado;
- extrair informacoes reveladas;
- extrair objetos introduzidos;
- extrair promessas abertas.

### Continuity Validation

Comparar delta contra `continuity_graph.json`.

### Style Drift Validation

Comparar capitulo contra `style_contract.md` e `style_metrics.json`.

### Specialist Validation

Ativar somente especialistas necessarios para o capitulo.

## Papeis Genericos Recomendados

Papeis base mantidos no codigo:

- `ScenePlanner`
- `DraftWriter`
- `ContinuityArchitect`
- `TimelineAuditor`
- `StyleKeeper`
- `PacingEditor`
- `ResearchSpecialist`
- `DomainSpecialist`
- `RevisionSynthesizer`
- `ReaderAdvocate`

Papeis especificos devem ser instancias configuradas, nao necessariamente
classes novas. Exemplo:

```json
{
  "agent": "DomainSpecialist",
  "specialty": "cryptography",
  "trigger": "chapter contains cipher, encryption, mathematical proof, puzzle logic",
  "output_format": "json_checklist"
}
```

## Criterios De Sucesso

A mudanca deve ser considerada bem-sucedida se:

- capitulos deixam de repetir descobertas ja feitas;
- inconsistencias temporais diminuem;
- o estilo permanece consistente depois dos primeiros capitulos;
- o numero de capitulos passa a variar conforme escopo;
- especialistas atuam quando necessario, sem custo fixo em todo capitulo;
- modelos menores conseguem executar tarefas fechadas com menos erro;
- o sistema produz registros estruturados que permitam debug.

## Decisoes Abertas

- Qual formato exato de `continuity_graph.json`?
- O `outline.md` continua sendo fonte primaria ou passa a ser derivado de
  `chapter_plan.json`?
- Quais gates bloqueiam commit e quais apenas geram aviso?
- O quanto deve ser mecanico vs LLM em estilo e continuidade?
- Como lidar com modelos que nao obedecem JSON?
- Qual politica de custo por capitulo e aceitavel?

## Proxima Etapa Recomendada

Antes de alterar codigo, criar documentos de especificacao para:

1. contrato de artefatos em `book_data/production/`;
2. desenho da pipeline `production_planning`;
3. novo fluxo de `book_generation` baseado em gates;
4. formato de `chapter_packet`;
5. estrategia de validacao mecanica e por LLM;
6. plano de migracao incremental sem quebrar o fluxo atual.

