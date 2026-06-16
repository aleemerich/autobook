# Fase 12: Docs E README [ROADMAP PRELIMINAR]

## Objetivo

Atualizar documentacao e README apos as mudancas estruturais globais do projeto.

## Status

> [!WARNING]
> **ROADMAP PRELIMINAR (BLOQUEADO):** Esta especificação é preliminar e **não deve ser executada** antes da aprovação do Gate A.

## Regras e Diretrizes de Documentação

- **Atualização Incremental Obrigatória:** Qualquer fase de implementação que altere o comportamento público do sistema (como CLI, comandos operacionais, formatos de arquivos de configuração ou APIs públicas) deve incluir obrigatoriamente a documentação atualizada correspondente na mesma entrega.
- **Papel da Fase 12:** A Fase 12 serve como um esforço final de consolidação, auditoria geral e revisão do README.md e docs/, mas **não substitui** o dever de documentação incremental durante cada uma das entregas das fases anteriores.
- README deve refletir comandos reais.
- Docs devem registrar branch por obra.
- Docs devem explicar wizard quando implementado.
- Docs devem explicar registry de pipelines e agentes quando implementados.
- Nao documentar recurso ainda nao implementado como funcional.

## Testes/Verificacoes

```bash
git diff --check -- README.md docs
uv run --with pytest pytest tests
```


