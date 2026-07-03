# Scripts

O fluxo principal passa por `run.py`, mas o repositorio contem scripts
auxiliares. Eles sao classificados para evitar confundir ferramentas laterais
com contrato central.

## Classificacao

| Grupo | Regra |
| --- | --- |
| Suportado | Usado por pipelines ou documentado como comando operacional. Deve ter testes e mocks. |
| Experimental | Util para exploracao, mas nao bloqueia o fluxo principal. |
| Historico | Mantido por contexto; nao deve ser ampliado sem decisao explicita. |

## Suportados

| Script | Papel |
| --- | --- |
| `run.py` | Entrada principal: wizard e CLI classica. |
| `main.py` | Delegador simples para `run.main()`. |
| `evaluate.py` | Fachada de avaliacao. |
| `verify_continuity.py` | Verificacao de continuidade global. |
| `resolve_continuity.py` | Converte achados de continuidade em fluxo editorial via `run.py`. |
| `gen_revision.py` | Reescrita editorial usada por `editorial_revision`. |
| `gen_brief.py` | Gera brief auxiliar quando usado manualmente. |
| `typeset/build_tex.py` | Gera `typeset/chapters_content.tex`. |
| `typeset/build_epub.py` | Gera `typeset/novel.epub` a partir dos capitulos e metadados. |
| `typeset/build_final.py` | Gera PDF/EPUB finais e orienta instalacao de dependencias externas. |

## Experimentais Ou Auxiliares

| Script | Papel |
| --- | --- |
| `compare_chapters.py` | Compara versoes de capitulos com prompt externo. |
| `adversarial_edit.py` | Sugere edicoes adversariais. |
| `apply_cuts.py` | Aplica cortes editoriais controlados. |
| `voice_fingerprint.py` | Extrai/imprime impressao de voz. |
| `gen_audiobook_script.py` | Gera roteiro de audiobook com cast opcional. |

Esses scripts possuem hardening inicial, mas so devem virar contrato central se
ganharem documentacao, testes e uso recorrente no fluxo principal.

## Historicos

Arquivos em `legacy/` preservam implementacoes antigas e nao fazem parte do
baseline moderno.

## Regras Para Novos Scripts

- Usar `encoding="utf-8"` em leitura/escrita textual.
- Reutilizar `llm.py`, `prompt_loader.py` e `evaluation/json_utils.py` quando
  aplicavel.
- Nao executar Git destrutivo sem helper testavel.
- Adicionar testes sem rede, sem LLM real e sem subprocesso real quando possivel.
