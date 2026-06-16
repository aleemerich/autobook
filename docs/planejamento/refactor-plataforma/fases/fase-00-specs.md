# Fase 00: Specs Antes De Codigo

## Objetivo

Criar as specs de arquitetura do refactor antes de alterar codigo. Esta fase
serve para transformar a direcao discutida em documentos menores e verificaveis.

## Contexto Obrigatorio

O executor deve ler:

- `docs/INDICE.md`
- `docs/SNAPSHOT_V0.md`
- `docs/analises/recomendacao_pipeline_producao.md`
- `docs/planejamento/como-transformar-parecer-em-specs.md`
- `docs/planejamento/refactor-plataforma/plano-migracao-modelos-medios.md`

## Arquivos Permitidos

Pode criar/editar somente:

```text
docs/planejamento/refactor-plataforma/*.md
docs/planejamento/refactor-plataforma/fases/*.md
docs/INDICE.md
```

## Fora De Escopo

- Nao alterar codigo Python.
- Nao alterar testes.
- Nao alterar README.
- Nao implementar wizard.
- Nao criar pipeline nova.

## Entregas

Criar ou completar:

```text
docs/planejamento/refactor-plataforma/00-decisao.md
docs/planejamento/refactor-plataforma/01-run-entrypoint.md
docs/planejamento/refactor-plataforma/02-pipeline-contract.md
docs/planejamento/refactor-plataforma/03-branch-workflow.md
docs/planejamento/refactor-plataforma/04-agent-registry.md
docs/planejamento/refactor-plataforma/05-prompt-layout.md
docs/planejamento/refactor-plataforma/06-feedback-lifecycle.md
docs/planejamento/refactor-plataforma/07-migration-plan.md
```

## Passos

1. Ler os documentos obrigatorios.
2. Verificar no repositorio os arquivos citados nas specs.
3. Criar cada spec com secoes:
   - objetivo;
   - fora de escopo;
   - estado atual;
   - comportamento desejado;
   - arquivos afetados;
   - testes necessarios;
   - criterios de aceite;
   - perguntas abertas.
4. Atualizar `docs/INDICE.md` se novos documentos forem adicionados.
5. Rodar verificacao de diff.

## Testes Obrigatorios

Como esta fase altera apenas docs:

```bash
git diff --check -- docs
```

## Criterios De Aceite

- Todas as specs listadas existem.
- Nenhuma spec contradiz o plano mestre.
- As specs preservam compatibilidade inicial com os comandos atuais.
- As specs deixam claro que `run.py` sem argumentos abre wizard futuramente.
- As specs deixam claro que `main` deve permanecer limpo e obras devem viver
  em branch propria.

## Checklist Para O Executor

- [ ] Li os documentos obrigatorios.
- [ ] Nao alterei codigo.
- [ ] Criei todas as specs da fase.
- [ ] Atualizei o indice se necessario.
- [ ] Rodei `git diff --check -- docs`.
- [ ] Listei duvidas abertas no final das specs.

## Checklist Para O Supervisor

- [ ] As specs sao implementaveis por fases.
- [ ] Nao ha proposta de reescrever tudo de uma vez.
- [ ] A ordem de migracao reduz retrabalho.
- [ ] As fases futuras nao dependem de decisoes ainda nao aprovadas.

## Prompt Sugerido Para Delegar

```text
Leia os documentos obrigatorios da Fase 00 e crie as specs listadas em
docs/planejamento/refactor-plataforma/. Nao altere codigo. Cada spec deve ter
objetivo, fora de escopo, estado atual, comportamento desejado, arquivos
afetados, testes necessarios, criterios de aceite e perguntas abertas. Rode
git diff --check -- docs ao final.
```

