# Fase 09: `book_generation` Em Subpipelines

## Objetivo

Separar `book_generation` em subpipelines reutilizaveis para permitir controle
real de continuidade, ritmo, criticas consumidas e revisao por etapa. Esta fase
e a principal preparacao para usar `production_planning` sem reescrever tudo
depois.

## Status

Definida pos-Gate A. Executar depois da Fase 8 aceita.

## Principio De Refatoracao

Nao alterar o resultado externo de uma vez. Primeiro extrair etapas com os
mesmos inputs e outputs atuais, depois ligar os novos contratos de feedback.

## Subfases Obrigatorias

Esta fase deve ser quebrada. Cada subfase precisa manter a suite passando.

1. **Fase 09A: Preparacao de contexto do capitulo**
   - Extrair montagem de contexto, lore, capitulos anteriores e dados de apoio.
   - Saida esperada: pacote de contexto testavel.

2. **Fase 09B: Planejamento do capitulo**
   - Isolar decisao de beat, objetivo narrativo e restricoes do capitulo.
   - Ainda pode usar dados atuais, sem depender de `production_planning`.

3. **Fase 09C: Drafting**
   - Isolar chamada ao agente de rascunho.
   - Testes devem mockar agente ou LLM.

4. **Fase 09D: Critica**
   - Isolar execucao dos criticos.
   - Converter saidas para contratos da Fase 8 quando possivel.

5. **Fase 09E: Revisao e sintese**
   - Garantir que `revision_plan` seja consumido na reescrita.
   - Nenhuma critica deve ser executada se sua saida nao for usada.

6. **Fase 09F: Validacao e persistencia**
   - Isolar salvamento de capitulo, relatorios e atualizacao de estado.
   - Manter nomes e formatos existentes enquanto nao houver fase dedicada para
     mudanca de formato.

## Arquivos Provaveis

```text
pipelines/book_generation.py
pipelines/book_generation/
  __init__.py
  context.py
  planning.py
  drafting.py
  critique.py
  revision.py
  validation.py
  persistence.py
tests/test_book_generation_subpipelines.py
```

O nome exato do pacote pode mudar se houver conflito com o arquivo atual. Se o
arquivo `pipelines/book_generation.py` impedir a criacao de um pacote com o
mesmo nome, usar uma pasta sem conflito, por exemplo
`pipelines/book_generation_steps/`.

## Fora De Escopo

- Implementar `production_planning`.
- Alterar formato publico dos capitulos.
- Alterar criterio de score existente sem fase dedicada.
- Criar wizard.
- Trocar provedores LLM.
- Reescrever prompts por qualidade literaria.

## Testes Esperados

```bash
uv run --with pytest pytest tests/test_book_generation_subpipelines.py
uv run --with pytest pytest tests/test_feedback_lifecycle.py
uv run --with pytest pytest tests
git diff --check -- pipelines writing tests docs/planejamento/refactor-plataforma
```

Testes minimos:

- cada subetapa pode ser exercitada com contexto fake.
- erros continuam propagando de forma clara.
- criticas entram no plano de revisao.
- revisao recebe o plano gerado.
- persistencia pode ser mockada sem escrever artefatos reais fora de tmp.

## Criterios De Aceite

- `BookGenerationPipeline` continua existindo para a CLI.
- O fluxo externo continua compativel.
- O codigo passa a ter pontos claros para inserir production planning,
  continuidade e especialistas.
- Feedback produzido na etapa de critica e consumido na etapa de revisao.

