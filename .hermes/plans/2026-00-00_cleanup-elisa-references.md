# Plano de Limpeza — Desacoplar Livro da Elisa do Framework

**Objetivo:** Remover TODAS as referências ao livro da Elisa/Helena/entropia/Faraday da branch `main`, deixando o framework 100% agnóstico — pronto para gerar qualquer livro sem viés de história.

**Princípios:**
1. Nenhum personagem, lugar, conceito ou regra específica do livro da Elisa pode permanecer hardcoded
2. Nosso foco é a branch `main` — branches de livros podem manter suas referências
3. `genres/` drama.txt é agnóstico (genérico), manter; `high_tension_speculative_thriller.txt` é específico da Elisa, remover
4. `doc/` é referência/developer — manuscritos e arc_summary devem ir para branches de livro
5. Testes devem usar fixtures genéricas, não nomes/personagens específicos

---

## Arquivos que precisam ser limpos

### 1. `agents.py` — CRÍTICO (3 blocos de lore hardcoded)

**CanonCriticAgent (linhas ~113-132):**
- REMOVER: Helena Varga, Elisa, Jana Dragowska, IC 0.001 Dk, USZ, CERN Genebra, casaco cinza/jeans
- SUBSTITUIR por: instrução genérica "verificar canon.md para fatos estabelecidos"
- O agente deve usar `lore_data` passado no context, não regras hardcoded

**TechnicalEditorAgent (linhas ~75-106):**
- REMOVER: Faraday 20°C, Lena blonde ponytail, Helena olhos branco/cabelo madeira, third-person Elisa
- REMOVER: "POV (only Elisa's perspective)"
- SUBSTITUIR por: instrução genérica "seguir voice.md e lore_data do projeto atual"
- Regras PT-PT→PT-BR padrão já estão OK (são genéricas)

**SynthesisAgent (linha ~183):**
- REMOVER: "Maintain the third-person limited POV (Elisa)"
- SUBSTITUIR por: "Maintain the POV and tone defined in voice.md for this project"

### 2. `genres/PT-BR/high_tension_speculative_thriller.txt` & `genres/EN/high_tension_speculative_thriller.txt` — REMOVER INTEIRO

Estes ficheiros são 100% escritos para o livro da Elisa (12 regras com Elisa, Helena, Faraday, entropia, etc). Substituir por um género genérico ou remover.

### 3. `doc/manuscript.md` — MOVER (5603 linhas, ~460KB)

Contém Capítulo 1 completo + início do Capítulo 2 da Elisa. Deve ser movido para a branch de livro (`autobook/a-prova-final` ou `autobook/a-prova-final2`). Da main, deletar.

### 4. `doc/arc_summary.md` — MOVER (1556 linhas)

Arco completo do livro da Elisa (22 capítulos, personagens, enredo). Deve ir para branch de livro. Da main, deletar.

### 5. `prompts/PT-BR/continuity.json` & `prompts/EN/continuity.json` — LIMPAR

- REMOVER: Helena Oerlikon 5C, CERN ETH 3.17, Mirela, Tomás Delgado, Evromind, Yuki Tanaka, Dmitri Volsky, "Elisa's inner thoughts"
- SUBSTITUIR por: exemplos genéricos ou template vazio
- Manter: estrutura do JSON, formato dos campos, exemplo de quality_improvement (sem nome)

### 6. `skills/redundancy_detector.py` — LIMPAR DEFAULTS

Linha 15: `target_words` padrão contém termos do livro da Elisa:
- REMOVER: `"0,001", "0.001", "boltzmann", "entropia", "granito"`
- MANTER: `"pedra", "rocha"` (genéricos)
- ADD: `"incremento", "entalpia"` (exemplos genéricos de termos técnicos que se repetem)
- Ou melhor: deixar target_words vazio por default e aceitar como parâmetro

### 7. `resolve_continuity.py` — LIMPAR

- Mesmo conteúdo que continuity.json (Oerlikon, Evromind, Yuki Tanaka, Dmitri Volsky, Marcus, Elisa)
- Substituir por template genérico

### 8. `tests/test_continuity.py` — LIMPAR FIXTURES

- "Elisa's Discovery" → "Chapter 1 Title" genérico
- "Elisa's Apartment, Hottingen" → "Protagonist's Apartment"
- "Elisa", "Marcus" como nomes de personagens → "Protagonist", "Secondary"
- "CERN 2018 backup data" → "archival research data"
- Todos os asserts com nomes específicos

### 9. `tests/test_generation_flow.py` — LIMPAR

- "Elisa wake up..." → "Protagonist wake up..."
- "Elisa talks to Helena..." → "Protagonist talks to Subject..."
- Beat descriptions genéricas

### 10. `tests/test_typeset.py` — LIMPAR

- "Elisa was looking at..." → "The protagonist was looking..."

### 11. `legacy/tests/test_editorial.py` — OPCIONAL (legacy, menos crítico)

- "Helena gives Elisa a physical key" → genérico

### 12. `doc/PROJECT_STUDY.md` — LIMPAR

Contém referências à Elisa em seções descritivas. Atualizar para descrição genérica do framework.

---

## Arquivos que NÃO precisam de alteração

- `pipelines/base.py` — genérico ✓
- `pipelines/book_generation.py` — usa agent factory, sem lore hardcoded ✓
- `pipelines/foundation.py` — genérico ✓
- `pipelines/ideation.py` — genérico ✓
- `pipelines/editorial_revision.py` — genérico ✓
- `llm.py` — genérico ✓
- `prompt_loader.py` — genérico ✓
- `genre_strategy.py` — genérico ✓
- `evaluate.py` — genérico ✓
- `verify_continuity.py` — genérico ✓
- `voice_fingerprint.py` — genérico ✓
- `book_data/voice.md` — Part 1 genérica, Part 2 vazia ✓
- `genres/PT-BR/drama.txt` — genérico ✓
- `genres/EN/drama.txt` — genérico ✓
- `genres/PT-BR/cyber_horror.txt` — genérico ✓
- `prompts/*/directives.txt` — genérico ✓
- `prompts/*/slop.json` — genérico ✓
- `prompts/*/draft_chapter_*.txt` — genérico ✓
- `prompts/*/gen_revision_*.txt` — genérico ✓
- `prompts/*/editorial.json` — genérico ✓
- `main.py` — genérico ✓
- `run.py` — genérico ✓
- `pyproject.toml` — genérico ✓
- `.env.example` — genérico ✓
- `book_data/MYSTERY.md`, `world.md`, `characters.md`, `outline.md`, `canon.md`, `editorial.md`, `state.json` — vazios ✓

---

## Proposta de branches de preservação

Antes de limpar a main, garantir que os dados do livro da Elisa estejam seguros:
- `autobook/a-prova-final` — já tem chapters + arc_summary (versão antiga)
- `autobook/a-prova-final2` — tem extensão da história
- O `manuscript.md` e `arc_summary.md` da main devem ser commited na branch `autobook/a-prova-final2` antes de deletar da main

---

## Ordem de Execução (TDD-friendly)

1. **Preservar** — Commit `doc/manuscript.md` e `doc/arc_summary.md` na branch de livro
2. **Deletar** `doc/manuscript.md` e `doc/arc_summary.md` da main
3. **Remover** `genres/*/high_tension_speculative_thriller.txt` (PT-BR e EN)
4. **Refactor** `agents.py` — blocos CanonCriticAgent, TechnicalEditorAgent, SynthesisAgent
5. **Refactor** `skills/redundancy_detector.py` — defaults genéricos
6. **Refactor** `prompts/*/continuity.json` — remover nomes/lugares da Elisa
7. **Refactor** `resolve_continuity.py` — mesmo tratamento
8. **Refactor** `tests/test_continuity.py` — fixtures genéricos
9. **Refactor** `tests/test_generation_flow.py` — beats genéricos
10. **Refactor** `tests/test_typeset.py` — texto genérico
11. **Testar (GATE)** — `uv run --with pytest pytest tests/ -v` — TODOS passam sem falhas
12. **Verificar** — grep sem resultados (excluindo .git/, .venv/, __pycache__/)
13. **Commit** — `git commit -m "chore: decouple framework from Elisa book — agnostic main branch"`

---

## Gate de Testes — OBRIGATÓRIO entre cada tarefa

**Nenhuma tarefa avança sem que TODOS os testes passem.**

Comando: `uv run --with pytest pytest tests/ -v`

Critérios de aceitação (permanecem durante toda a limpeza):
- **0 testes falhados** (FAILED)
- **0 erros de coleta** (ERROR — import quebrado, fixture não encontrada, syntax error)
- **0 testes skip** a não ser que já existissem antes da limpeza
- Output final: `passed` com o mesmo número de testes ou mais (se testes novos adicionados)

Protocolo de falha no teste:
1. **PARA** imediatamente — não avança para a próxima tarefa
2. **DIAGNOSTICA** — lê o traceback completo, identifica raíz da falha
3. **CORRIGI** — ajusta o código ou teste até a falha desaparecer
4. **RE-EXECUTA** — `uv run --with pytest pytest tests/ -v` até 0 falhas
5. Só então avança para a próxima tarefa de limpeza

Se 3+ tentativas de correção falharem no mesmo ficheiro:
- **PARA** e reporta ao Alessandro com o erro exato antes de continuar

Nota: a baseline atual é de **39 testes passando** (sem falhas). Este número não pode diminuir durante a limpeza.

---

## Estimativa

- 13 tarefas + gate de testes entre cada uma
- Cada tarefa: edição focada, 1-3 ficheiros, depois `pytest` completo
- Tempo total estimado: 45-90 minutos (testes adicionam ~30 min)
- Risco: médio — alterações em agents.py e continuity.json podem quebrar testes que dependem de fixtures específicas; o gate captura imediatamente
