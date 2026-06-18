# Legacy

`legacy/` preserva scripts, testes e ideias antigas. A pasta nao faz parte do
contrato operacional moderno.

## Politica Atual

- `legacy/tests` e ignorado por `pytest.ini`.
- Quando executado diretamente, `legacy/tests` retorna sucesso com nenhum teste
  coletado.
- Imports quebrados ou dependencias antigas dentro de legacy nao bloqueiam o
  baseline moderno.
- Codigo novo nao deve depender de `legacy/`.

## Como Tratar Arquivos Legados

| Situacao | Acao recomendada |
| --- | --- |
| Script ainda util | Migrar para raiz/pacote moderno, adicionar testes e documentar em `docs/scripts/`. |
| Ideia util, codigo velho | Criar novo modulo limpo baseado no comportamento desejado. |
| Sem uso atual | Manter como historico ou remover em rodada dedicada. |

## Comandos

```bash
uv run --with pytest pytest legacy/tests -q
```

Resultado esperado: nenhum teste coletado, exit code 0.

## Limite

Legacy nao deve ser usado para inferir arquitetura atual. Use
[../architecture/arquitetura.md](../architecture/arquitetura.md) e
[../pipelines/pipelines.md](../pipelines/pipelines.md).
