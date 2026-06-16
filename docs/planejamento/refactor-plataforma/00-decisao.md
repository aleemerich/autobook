# 00 - Contexto e Decisão Arquitetural

## Objetivo
Registrar a decisão arquitetural para a reestruturação da plataforma Autobook, estabelecendo as premissas, alternativas consideradas e a ordem de execução das frentes de trabalho para o refatoramento modular.

## Estado Atual
O Autobook executa pipelines monolíticas rígidas (geração de livros com loops fixos, agentes estáticos em `agents.py` com prompts embutidos no código Python) e não possui isolamento de espaço de trabalho por obra, misturando arquivos de livro na branch principal (`main`/`master`).

## Premissas
1. **Redução de Custo de Contexto:** Utilizar chamadas de LLM menores e mais focadas em vez de prompts massivos com todo o contexto do livro.
2. **Modularidade:** Decompor processos monolíticos em etapas menores e testáveis (subpipelines).
3. **Isolamento de Negócio:** As obras devem ser desenvolvidas em branches separadas para manter a branch principal limpa.
4. **Retrocompatibilidade:** Manter compatibilidade com a CLI atual do projeto durante a transição.

## Alternativas Consideradas
1. **Reescrita Total Imediata:** Descartada por alto risco de regressão nos testes existentes.
2. **Abordagem Puramente Baseada em LLM:** Descartada devido à imprevisibilidade de prompts gigantescos.
3. **Refatoramento Híbrido Incremental (Adotada):** Manter o comportamento externo do sistema atual enquanto a infraestrutura básica e a modularização de agentes são instaladas em fases pequenas e revisáveis, seguidas por um gate de auditoria antes da implementação avançada de agentes e subpipelines.

## Comportamento Desejado
- Executar o refatoramento em fases granulares.
- Garantir que as Fases 0 a 5 sejam tratadas como **imediatamente executáveis**.
- Garantir que as Fases 6 a 12 permaneçam como **roadmap preliminar estratégico**, exigindo uma reavaliação obrigatória no **Gate A**.
- Registrar a decisão formal do supervisor sobre `agents.py` e a validação de `requires`/`produces`.

## Decisões Adotadas pelo Supervisor
1. **Depreciação de `agents.py`:** Não remover nem deprecá-lo agora. O arquivo de proxy `agents.py` na raiz será mantido intacto. A sua remoção/depreciação só deve ocorrer após o pacote `agent_system/` estar maduro, exaustivamente testado e com todos os imports migrados, o que constituirá uma fase futura e isolada (`fase-06x-deprecate-agents-py.md`), a ser detalhada somente após o Gate A.
2. **Validação de `requires` e `produces`:** Na Fase 1, estes metadados de dependência de pipelines são totalmente opcionais e não sofrerão nenhuma validação automatizada ou restritiva de execução. A utilidade prática desses metadados será avaliada pelo supervisor no Gate A antes de se propor qualquer linter ou verificação automática de conformidade.

## Ordem das Frentes (Fases)
1. **Fase 0 (Specs)**: Documentação de contratos e arquitetura.
2. **Fase 1 (Contrato de Pipelines)**: Adição de metadados opcionais em `Step`/`Pipeline`.
3. **Fase 2 (Registry de Pipelines)**: Centralização da descoberta de pipelines.
4. **Fase 3 (run.py com Wizard)**: Redirecionamento de execução sem argumentos para o stub de wizard.
5. **Fase 4 (Branch Workflow)**: Utilitários seguros para branches de obras.
6. **Fase 5 (Discovery)**: Detecção automática do estado do repositório.
7. **Gate A (Revisão Arquitetural)**: Auditoria obrigatória antes de prosseguir.
8. **Fases 6 a 12 (Roadmap Preliminar)**: Modularização de agentes, externalização de prompts, ciclo de vida de feedback, subpipelines de geração, planejamento de produção estruturado, wizard interativo e revisão de documentação.

## Arquivos Afetados Futuramente
- Todos os arquivos definidos nas fases de 0 a 12 do plano de migração.

## Contratos De Entrada
- Não se aplica (documento de contexto geral).

## Contratos De Saida
- Não se aplica (documento de contexto geral).

## Testes Necessarios
- Verificação do diff de documentação via `git diff --check`.

## Criterios De Aceite
- O documento deve listar com precisão todas as premissas e a ordem das fases.
- As restrições sobre `agents.py` e metadados de pipeline devem estar explícitas.

## Perguntas Abertas
- Nenhuma para esta especificação de contexto.
