# 06 - Feedback Lifecycle Spec

> [!NOTE]
> Gate A aprovado. A spec canonica de execucao esta em
> `fases/fase-08-feedback-lifecycle.md`.

## Objetivo
Especificar o ciclo de vida estruturado do feedback gerado por agentes críticos literários no Autobook, garantindo que toda crítica gerada seja obrigatoriamente lida, parseada e consumida por uma etapa posterior do pipeline de escrita para nortear as revisões de texto.

## Fora De Escopo
- Alterar o arquivo monolítico principal `pipelines/book_generation.py` ou a estrutura do loop de geração nesta fase inicial.
- Implementar validadores complexos ou métricas estáticas avançadas de estilo fora do fluxo de passagem de dados de feedback.

## Estado Atual (O Problema)
Atualmente, os agentes críticos literários (como os críticos de slop, continuidade e ritmo) analisam os rascunhos gerados e gravam relatórios textuais em Markdown (arquivos `critique_*.md`), mas a passagem de dados para o agente de escrita ou de síntese é pouco estruturada. Ocasionalmente, agentes críticos geram feedbacks volumosos que são simplesmente ignorados por etapas posteriores, causando desperdício de chamadas e processamento de contexto sem melhora real de qualidade de texto.

## Comportamento Desejado (Contrato Alvo e Fluxo)
- **Contrato de Fluxo de Dados:** O ciclo completo de dados de feedback deve respeitar a sequência linear:
  `critic_report` -> `revision_plan` (JSON/Markdown estruturado) -> `revised_text` -> `verification_report`.
- **Lógica de Execução Coordenada:** Nenhum agente crítico está autorizado a executar se sua respectiva saída de análise não estiver mapeada para leitura/consumo na etapa de síntese/revisão subsequente.
- **Estruturação da Implementação:** Para mitigar problemas de acoplamento e código duplicado em loops monolíticos difíceis de depurar, o ciclo de vida de feedback será planejado em três passos integrados com o refatoramento da pipeline:
  1. **Fase 8a (Documentação):** Formalização estrita dos contratos de entrada e saída de dados de feedback.
  2. **Fase 9 (Refatoramento):** Decompor `book_generation` em subpipelines menores reutilizáveis.
  3. **Fase 8b (Implementação):** Injeção física da lógica de feedback lifecycle diretamente dentro das subpipelines limpas resultantes da Fase 9.

## Arquivos Afetados Futuramente
- `pipelines/book_generation.py`
- `pipelines/subpipelines/` (novas subpipelines extraídas na Fase 9)
- [NEW] `tests/test_feedback_lifecycle.py`

## Contratos De Entrada
- Estrutura JSON ou arquivo estruturado gerado pelos críticos (`critic_report`).

## Contratos De Saida
- Plano de revisão unificado (`revision_plan`) contendo os pontos a serem corrigidos no texto.

## Testes Necessarios (Planejados)
1. **Passagem de Crítica:** Validar que a saída gerada por um crítico simulado é mapeada e injetada no construtor do prompt do agente de síntese.
2. **Plano de Revisão Vazio:** Validar que o fluxo operacional executa normalmente quando nenhum crítico gera apontamentos (plano de revisão vazio).
3. **Persistência de Logs:** Validar que o andamento do ciclo de feedback é corretamente registrado nos arquivos de logs de execução do pipeline.

## Criterios De Aceite
- O fluxo de dados do feedback entre os agentes críticos e os escritores é determinístico e auditável através de testes mockados.
- Testes confirmam que a saída dos críticos influenciou de forma mensurável o prompt do agente de síntese.

## Decisao Pos-Gate A

Conflitos entre criticas excludentes nao serao resolvidos por heuristica
complexa nesta fase. A primeira implementacao deve preservar origem,
severidade e instrucao de correcao de cada achado, deixando a priorizacao
explicita no `RevisionPlan`.
