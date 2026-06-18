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
| `adversarial_edit.py` | Prompt ja externalizado e JSON comum reutilizado; ainda precisa decisao se vira fluxo suportado. |
| `compare_chapters.py` | Prompt ja externalizado e JSON comum reutilizado; ainda precisa decisao se vira fluxo suportado. |
| `gen_audiobook_script.py` | Prompt ja externalizado; fluxo de audiobook ainda nao esta consolidado como produto principal. |
| `voice_fingerprint.py` | Auditoria auxiliar de estilo com encoding padronizado; ainda precisa contrato de saida/documentacao propria. |

## Legacy

Scripts e testes sob `legacy/` permanecem fora da suite moderna. Eles podem ser
consultados como referencia historica, mas nao fazem parte do contrato atual.

## Proximos Ajustes do Pacote R2

- Decidir quais scripts experimentais devem virar suportados ou migrar para
  `legacy/`.
- Criar testes dedicados para os scripts experimentais que forem promovidos.
