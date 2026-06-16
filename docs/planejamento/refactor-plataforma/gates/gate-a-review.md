# Gate A: Revisão Arquitetural Após Fases 0-5

Este documento avalia se a fundação técnica das Fases 0 a 5 está madura, consistente e segura para autorizar o avanço em direção ao detalhamento da Fase 6 e demais fases do roadmap estratégico preliminar.

---

## 1. Objetivo do Gate A
* Auditar as implementações de base realizadas nas Fases 0-5.
* Analisar a compatibilidade com a CLI atual do Autobook.
* Registrar riscos e pendências estruturais não bloqueantes.
* Liberar ou bloquear o detalhamento e escrita da especificação final para a **Fase 6** (Organização Inicial do Sistema de Agentes).

---

## 2. Resumo das Fases 0-5

### Fase 0: Especificações
* **Objetivo:** Criar as especificações de design técnico para o refatoramento modular de pipelines, agente de roteamento e workflow de branches.
* **Arquivos:** `00-decisao.md`, `01-run-entrypoint.md`, `02-pipeline-contract.md`, `03-branch-workflow.md`, `04-agent-registry.md`, `05-prompt-layout.md`, `06-feedback-lifecycle.md`, `07-migration-plan.md`.
* **Status:** Concluído.
* **Testes:** Validação de diffs de documentação (`git diff --check`).
* **Observações:** A especificação guiou com precisão as fases seguintes, isolando adequadamente as frentes.

### Fase 1: Contrato Base de Pipelines
* **Objetivo:** Adicionar metadados declarativos opcionais (`description`, `requires`, `produces`) a `Step` e `Pipeline` sem causar quebras.
* **Arquivos:** `pipelines/base.py`, `tests/test_pipeline_base.py`.
* **Status:** Concluído.
* **Testes:** `tests/test_pipeline_base.py` (9 testes cobrindo defaults, cópias isoladas de listas de metadados e propagação de erros).
* **Observações:** O design garantiu 100% de compatibilidade retroativa para as pipelines concretas existentes.

### Fase 2: Registry de Pipelines
* **Objetivo:** Criar um registro centralizado para expor metadados das pipelines e gerenciar instanciações limpas.
* **Arquivos:** `pipelines/registry.py`, `run.py`, `tests/test_pipeline_registry.py`, `tests/conftest.py`.
* **Status:** Concluído.
* **Testes:** `tests/test_pipeline_registry.py` (6 testes validando o registry de forma isolada e o mock de integração no `run.py`).
* **Observações:** O registry foi implementado de forma estática e explícita, sem recorrer a importações dinâmicas e inseguras de arquivos arbitrários.

### Fase 3: run.py com Wizard Stub
* **Objetivo:** Modificar `run.py` para abrir um assistente interativo padrão (stub) quando executado sem parâmetros.
* **Arquivos:** `run.py` (ajustes), `cli/__init__.py`, `cli/wizard.py`, `tests/test_run_entrypoint.py`.
* **Status:** Concluído.
* **Testes:** `tests/test_run_entrypoint.py` (4 testes validando parsing de argumentos e redirecionamento correto).
* **Observações:** Corrigidas a duplicação no argparse e o acúmulo de Tee loggers nos fluxos padrão dos testes.

### Fase 4: Workflow de Branch por Obra
* **Objetivo:** Implementar utilitários de tratamento de nomes e validações de branches para impedir escritas na branch principal (`main`/`master`).
* **Arquivos:** `workspace/__init__.py`, `workspace/branching.py`, `tests/test_workspace_branching.py`.
* **Status:** Concluído.
* **Testes:** `tests/test_workspace_branching.py` (7 testes mockando subprocess de git e cobrindo slugify, detecção e bloqueio de branches).
* **Observações:** Sem comandos destrutivos. As validações operam com mock estrito, preservando o repositório local do desenvolvedor.

### Fase 5: Discovery Dinâmico
* **Objetivo:** Criar uma camada de inspeção passiva (somente-leitura) para mapear o status atual do repositório da obra (sementes, arquivos lore, capítulos e logs).
* **Arquivos:** `cli/discovery.py`, `tests/test_cli_discovery.py`.
* **Status:** Concluído.
* **Testes:** `tests/test_cli_discovery.py` (5 testes isolando estados vazios, com sementes, com fundações e ordenamento de capítulos).
* **Observações:** Não realiza alterações no filesystem e mapeia corretamente a branch atual e as sugestões de próximos passos.

---

## 3. Checklist de Verificação

* **O contrato de pipeline funcionou?**
  * *Sim.* Steps e Pipelines aceitam metadados de forma transparente e as listas mutáveis fornecidas são isoladas via cópia (`list(requires)`).
* **O registry ficou centralizado e simples?**
  * *Sim.* O registry unificou a declaração das pipelines iniciais sem o uso de imports dinâmicos complexos.
* **`run.py` continuou compatível com CLI atual?**
  * *Sim.* A CLI clássica do Autobook responde exatamente com o mesmo comportamento para comandos com argumentos.
* **`run.py` sem argumentos chama wizard stub?**
  * *Sim.* O assistente inicial stub é disparado e retorna mensagem informativa limpa ao usuário.
* **Branch workflow está seguro e sem comandos destrutivos?**
  * *Sim.* As funções puras e utilitários não executam checkout ou manipulação real de Git.
* **Discovery é somente leitura?**
  * *Sim.* Não há criação ou modificação de arquivos ou pastas no disco.
* **Discovery consegue alimentar o wizard futuro?**
  * *Sim.* O retorno no formato `ProjectState` provê um mapa completo dos caminhos e estado atual.
* **As Fases 6-12 ainda fazem sentido na ordem atual?**
  * *Sim.* A ordem de estruturação de agentes (`Fase 6`), externalização de prompts (`Fase 7`), feedback e subpipelines (`Fase 8` e `Fase 9`) antes da pipeline de produção planning completa (`Fase 10`) garante menor acúmulo de retrabalho.
* **Há alguma correção obrigatória antes da Fase 6?**
  * *Não.* A fundação técnica está totalmente consolidada e sem quebras.

---

## 4. Pontos de Atenção
* **Cobertura de Testes de Pipelines no Discovery:** O arquivo `tests/test_cli_discovery.py` não valida explicitamente a correspondência dos pipelines retornados do registry no objeto de estado, testando de forma geral.
* **Cobertura de Logs e Artefatos no Discovery:** A suite de testes não simula a presença física de logs e artefatos de produção em book_data/production para checar se eles são coletados pelo discovery.
* **Comportamento Limite no Branch Name:** A chamada de `book_branch_name("")` com string vazia poderia resultar em um slug nulo, gerando `"autobook/"`. Esse comportamento limite não impacta agora porque o assistente interativo que utiliza essa função ainda não foi implementado.
* **Imutabilidade das Specs:** A especificação de dados de pipeline `PipelineSpec` poderia ser imutável (`frozen=True` no `@dataclass`), mas a mutação acidental em runtime é nula e não bloqueia a execução.
* **Decisão do Supervisor sobre Validação:** Por diretriz superior, os metadados `requires` e `produces` continuam sem validação obrigatória. Essa restrição permanece como pretendido.

---

## 5. Decisão do Gate
A decisão tomada pelo supervisor é:

**APROVADO COM CORREÇÕES NÃO BLOQUEANTES**

### Correções Não-Bloqueantes Planejadas (Ações de Melhoria Futura):
1. **Melhorar Testes do Discovery:** Adicionar nos testes de discovery a simulação e asserção de diretórios de logs e diretórios de produção, bem como a validação estrita da chave de pipelines.
2. **Robustez no Branch Name:** Tratar a string vazia no utilitário de branch do workspace para evitar a geração de nomes inválidos (ex: retornar exceção ou fallback se o título for inteiramente sanitizado como nulo).
3. **PipelineSpec Imutável:** Congelar a especificação das pipelines adicionando `frozen=True` na declaração do dataclass.

---

## 6. Próximas Ações Recomendadas
* **Bloqueio de Código da Fase 6:** A Fase 6 de código **não deve ser iniciada** sem a aprovação prévia de seu respectivo detalhamento.
* **Detalhamento da Fase 6:** A próxima etapa deve focar exclusivamente no detalhamento técnico e na escrita das especificações para a Fase 6 (Organização Inicial do Sistema de Agentes) de modo a mitigar conflitos e unificar os contratos de base dos agentes.
