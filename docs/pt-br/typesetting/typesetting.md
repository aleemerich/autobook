# Typesetting

Typesetting ainda e uma etapa auxiliar, nao uma pipeline principal registrada.
O script suportado e:

```bash
uv run python typeset/build_tex.py
```

Ele le capitulos em `chapters/` e gera:

```text
typeset/chapters_content.tex
```

## Fluxo

```mermaid
flowchart LR
    Chapters["chapters/ch_XX.md"] --> Script["typeset/build_tex.py"]
    Script --> Tex["typeset/chapters_content.tex"]
    Tex --> External["ferramentas externas de PDF/EPUB"]
```

## Estado Atual

- A geracao de conteudo LaTeX e suportada.
- A producao final de PDF/EPUB depende de ferramentas externas e nao e
  garantida por uma pipeline do Autobook.
- Artefatos de teste que existiam nesta pasta foram removidos da documentacao
  operacional.

## Regras Para Evoluir

- Se PDF/EPUB virar contrato, criar pipeline ou comando documentado.
- Adicionar testes para markdown complexo, acentos, capitulos vazios e ordem de
  arquivos.
- Nao misturar geracao de arte final com geracao narrativa no mesmo step.
