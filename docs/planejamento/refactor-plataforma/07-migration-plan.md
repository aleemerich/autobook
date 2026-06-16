# 07 - Refactoring Migration Plan Spec

## Objetivo
Consolidar a ordem das fases do refatoramento da plataforma Autobook, dividindo as frentes de trabalho em entregas prontas para execução (Fases 0 a 5) e roadmap preliminar estratégico (Fases 6 a 12), estabelecendo o Gate A como ponto de auditoria arquitetural e definindo regras rígidas de supervisão e documentação incremental.

## Fora De Escopo
- Detalhar a implementação técnica ou contratos operacionais específicos para as fases do roadmap (Fases 6 a 12) além do alinhamento geral.
- Realizar alterações em arquivos de código Python ou de testes nesta rodada.

## Estado Atual
O plano de migração geral está delineado em `docs/planejamento/refactor-plataforma/plano-migracao-modelos-medios.md`, mas carecia de uma formalização de barreiras/gates arquiteturais rígidos entre a fase de infraestrutura básica e a fase de agentes/produção, correndo o risco de execuções automatizadas e desordenadas por modelos de linguagem.

## Comportamento Desejado (Consolidação do Plano)
- **Fases Prontas para Execução (Fases 0-5):**
  - **Fase 0 (Specs):** Criação das especificações da Fase 0 (esta especificação).
  - **Fase 1 (Contratos de Pipeline):** Metadados opcionais em `Step` e `Pipeline` sem validação inicial.
  - **Fase 2 (Registry):** Registro dinâmico descentralizado de pipelines em `pipelines/registry.py`.
  - **Fase 3 (run.py com Wizard):** Ponto de entrada executando stub de wizard sem argumentos.
  - **Fase 4 (Branch Workflow):** Utilitários puros e mockados de controle de branches Git em `workspace/branching.py`.
  - **Fase 5 (Discovery):** Descoberta automática não-destrutiva de estado do repositório em `cli/discovery.py`.
- **Gate A - Revisão Arquitetural Após Fases 0-5:**
  - Ponto de auditoria obrigatório para validar se a fundação está correta e estável. Bloqueia a execução das fases seguintes.
- **Roadmap Preliminar (Fases 6-12):**
  - **Fase 6 (Agent System):** Organização inicial do módulo `agent_system/`.
  - **Fase 7 (Externalização de Prompts):** Mover prompts das classes Python para arquivos `.txt`.
  - **Fase 8 (Feedback Lifecycle):** Ciclo estruturado de dados de feedback.
  - **Fase 9 (Subpipelines):** Decomposição de `book_generation` em subpipelines menores.
  - **Fase 10 (Production Planning):** Pipeline para plano de produção estruturado (artefatos gerados estritamente em branch de obra).
  - **Fase 11 (Wizard Completo):** Área de trabalho interativa integrada.
  - **Fase 12 (Revisão Geral):** Revisão de documentação geral.

## Regras de Execução e Qualidade
1. **Regra de Documentação Incremental:** Qualquer fase de implementação que altere comportamentos públicos (CLI, comandos operacionais, formatos de arquivos, APIs públicas) deve obrigatoriamente incluir a atualização incremental dos documentos operacionais na mesma entrega. A Fase 12 é apenas uma revisão final e não substitui esse dever.
2. **Regras de Supervisão (Políticas de Aceite):** O supervisor deve rejeitar entregas que realizem refatoramento amplo demais fora do escopo da fase, que causem quebra de retrocompatibilidade injustificada, que executem comandos Git destrutivos reais ou que gerem agentes sem consumo estruturado.
3. **Comandos Mínimos de Validação:**
   - Modificações de documentação:
     `git diff --check -- docs`
   - Modificações de código:
     `uv run --with pytest pytest tests`

## Arquivos Afetados Futuramente
- Todos os arquivos mapeados ao longo da execução das Fases 1 a 12.

## Contratos De Entrada
- Não se aplica (documento consolidado de planejamento).

## Contratos De Saida
- Não se aplica (documento consolidado de planejamento).

## Testes Necessarios
- Auditoria do diff de documentação via `git diff --check`.

## Criterios De Aceite
- Apresentação coerente de todas as fases, do Gate A e das regras de qualidade e segurança estabelecidas pelo supervisor.
- Divisão nítida entre fases executáveis (0-5) e de roadmap (6-12).

## Perguntas Abertas
- Como deve ser formalizada a aprovação de cada fase do Gate A (ex: arquivo de log, PR review, checkmark)?
