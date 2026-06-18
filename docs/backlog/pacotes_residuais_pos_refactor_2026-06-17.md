# Pacotes Residuais Pos-Refactor - 2026-06-17

Este arquivo e um registro de acompanhamento do backlog residual que surgiu
apos a auditoria senior do codigo. Os documentos originais de analise foram
removidos da arvore principal; este resumo preserva o resultado operacional sem
manter referencias quebradas.

## Validacao De Referencia

- `uv run --group dev ruff check .` sem erros.
- `uv run --with pytest pytest tests -q` com 320 testes passando.
- `uv run --with pytest pytest legacy/tests -q` sem testes coletados e exit code 0.

## Pacotes Executados

| Pacote | Estado | Resultado |
| --- | --- | --- |
| Pacote 1 | Concluido | Quebras funcionais e ruido operacional tratados. |
| Pacote 2 | Concluido | Modularizacao e higiene adicional em areas centrais. |
| Pacote 3 | Concluido | Ajustes solicitados diretamente em scripts e fluxos. |
| Pacote 4 | Concluido | Endurecimento e limpeza operacional. |
| Pacote 5 | Concluido | Ajustes finais antes dos pacotes residuais. |
| Pacote 6 | Concluido | Feedback editorial avancado e ingestion estruturada. |
| Pacote 7 | Concluido | Ajustes complementares de contratos e robustez. |
| Pacote 8 | Concluido | Rodada final de comparacao com auditoria e limpeza. |

## Resultado Consolidado

| Tema | Estado atual |
| --- | --- |
| Entrada principal | `main.py` delega para `run.main()`; `run.py` concentra wizard e CLI classica. |
| Testes legados | Fora do baseline moderno, ignorados de forma controlada. |
| Avaliacao | `evaluate.py` atua como fachada sobre `evaluation/`. |
| Prompts | Prompts de agentes, foundation, evaluation e ferramentas vivem em `prompts/{LANG}/`. |
| Git | Operacoes passam por `workspace/git.py` ou helpers de workspace testaveis. |
| Wizard | Decomposto em helpers e integrado a branch/workspace. |
| LLM | Erros de configuracao sao tipados e propagados. |
| Agentes | Estrategia atual: adapter moderno em `agent_system/` sobre `agents.py`. |
| Feedback | Criticas sao convertidas para `CriticReport` e consolidadas em `RevisionPlan`. |
| Tooling | `pyproject.toml` declara grupo `dev` e ruff gradual. |
| Scripts | Scripts raiz classificados em suportados, experimentais e historicos. |

## Backlog Futuro

Estes itens nao bloqueiam o refactor atual:

1. Promover ou arquivar scripts experimentais caso passem a fazer parte do
   fluxo suportado.
2. Ampliar emissao JSON nativa dos agentes criticos.
3. Expandir gradualmente a cobertura de lint para diretorios hoje excluidos.
4. Melhorar mensagens de terminal em scripts perifericos para manter idioma e
   acentuacao consistentes.
