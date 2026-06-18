# Scripts Raiz

Este documento classifica os scripts Python localizados na raiz do projeto para
separar comandos suportados de utilitarios experimentais. A classificacao evita
que checks de qualidade e documentacao tratem prototipos como fluxo principal.

## Suportados

Estes scripts fazem parte do fluxo operacional atual ou sao fachadas estaveis:

| Script | Papel | Observacao |
| --- | --- | --- |
| `run.py` | Orquestrador principal e Wizard | Entrada recomendada para pipelines. |
| `main.py` | Delegador para `run.main()` | Mantido por compatibilidade com projetos Python. |
| `evaluate.py` | Fachada de avaliacao | Implementacao real vive no pacote `evaluation/`. |
| `verify_continuity.py` | Validador global de continuidade | Usado apos geracao e revisoes. |
| `resolve_continuity.py` | Resolucao assistida de continuidade | Aciona revisao editorial via `run.py`. |
| `gen_revision.py` | Reescrita de capitulo por brief | Usado pela pipeline de revisao editorial. |
| `apply_cuts.py` | Aplicacao de cortes gerados por auditoria | Utilitario operacional com suporte atual. |
| `gen_brief.py` | Geracao de briefs editoriais | Suportado, mas ainda concentra bastante logica e prompts. |
| `agents.py` | Implementacao legada de agentes | Suportado como backend do adapter `agent_system/`. |
| `llm.py` | Cliente LLM unificado | Suportado. |
| `prompt_loader.py` | Loader de prompts e configs localizadas | Suportado. |
| `genre_strategy.py` | Regras de genero | Suportado. |

## Experimentais

Estes scripts ainda sao uteis, mas nao devem ser tratados como contrato principal
sem uma rodada especifica de limpeza:

| Script | Motivo |
| --- | --- |
| `adversarial_edit.py` | Prompt e parser JSON proprios; precisa migrar para `prompts/` e utilitarios comuns. |
| `compare_chapters.py` | Prompt e parser JSON proprios; precisa padronizar encoding e status operacional. |
| `gen_audiobook_script.py` | Depende de fluxo de audiobook ainda nao consolidado; prompt hardcoded e parser proprio. |
| `voice_fingerprint.py` | Auditoria auxiliar de estilo; precisa padronizar encoding e formato de saida. |

## Legacy

Scripts e testes sob `legacy/` permanecem fora da suite moderna. Eles podem ser
consultados como referencia historica, mas nao fazem parte do contrato atual.

## Proximos Ajustes do Pacote R2

- Mover prompts dos scripts experimentais para `prompts/{LANG}/tools/`.
- Reusar `evaluation.json_utils` onde houver parsing de JSON de LLM.
- Padronizar `encoding="utf-8"` em leituras/escritas dos scripts experimentais.
- Decidir quais scripts experimentais devem virar suportados ou migrar para
  `legacy/`.
