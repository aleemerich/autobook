# autobook — Estudo Completo do Projeto

> Referencia historica: este estudo preserva uma leitura antiga do projeto e
> pode citar caminhos, comandos e artefatos obsoletos. Para o contrato atual,
> consulte `../INDICE.md`.

## Visão Geral
Pipeline multi-agente autônomo para escrever, revisar, diagramar, ilustrar e narrar livros com AI.
Fork do [autonovel](https://github.com/NousResearch/autonovel) da NousResearch.
Primeira obra produzida: "The Second Son of the House of Bells" (19 ch, 79K palavras) na branch `bells`.

Localização:
- WSL: `/home/alessandro/dev/autobook`
- Windows: `D:\Dev\autobook`

## Entry Point
`run.py` — orquestrador unificado via CLI:
```bash
uv run python run.py --pipeline [ideation|foundation|book_generation|editorial_revision] [--from-scratch] [--chapter CH_NUMS] [--yes]
```

## Arquitetura
**Command/Composite Pattern** em `pipelines/base.py`:
- `Step`: classe base atômica
- `Pipeline`: passo composto que executa sequência de steps

## 4 Pipelines

### 1. Ideation (`pipelines/ideation.py`)
- Questionário interativo no console
- Gera 3 conceitos diversos via LLM
- Usuário seleciona ou input customizado
- Opcionalmente gera mistério central
- Output: `seed.txt` + `book_data/MYSTERY.md` + `book_data/state.json`

### 2. Foundation (`pipelines/foundation.py`)
Gera 4 bíblias estruturais a partir de `seed.txt`:
1. `world.md` — Worldbuilding (Sanderson's Laws, Le Guin, TTRPG-quality)
2. `characters.md` — Fichas wound/want/need/lie + sliders + speech patterns
3. `outline.md` — 22 capítulos com beats, try-fail cycles, foreshadowing ledger
4. `canon.md` — Base de dados de fatos (80-120 entries)
- Auto-commit git
- Inicializa `state.json` com `chapters_drafted: 0`

### 3. Book Generation (`pipelines/book_generation.py`)
Gera capítulos sequencialmente com **4 fases por capítulo**:

**Fase 1 — Modular Beat Generation:**
- DraftingAgent escreve cada beat individualmente → `logs/tmp_draft/beat_NN_raw.md`
- Sliding window context: últimos 3 parágrafos do beat anterior + contexto do capítulo anterior
- Roadmap explícito com beats concluídos/atual/próximo/futuro

**Fase 2 — Independent Critics:**
- CanonCriticAgent: verifica lore/canon contra book_data (world.md, canon.md, characters.md)
- StyleCriticAgent: detecta AI clichés, slop, em-dash abuse
- FlowCriticAgent: avalia pacing e transições
- Suporte a critics configuráveis via `AUTOBOOK_CRITICS`

**Fase 3 — Sequential Synthesis:**
- SynthesisAgent aplica correções critique-by-critique
- Salva intermediários `chapter_step_NN_critique.md`

**Fase 4 — Evaluation & Self-Healing:**
- `evaluate_chapter()` → score threshold (padrão 6.0, max 3 tentativas)
- Sucesso: `verify_continuity.py --strict --threshold 7.0`
- Auto-commit + push por capítulo com msg "chNN: score X (attempt N)"
- Fallback: mantém melhor score se threshold não atingido

### 4. Editorial Revision (`pipelines/editorial_revision.py`)
- Revisão humano-dirigida via `book_data/editorial.md`
- Self-Healing Corrective Retry Loop (5 attempts, dynamic temperatures)

## Agentes (`agents.py`)

Hierarquia: `Agent` base → AgentFactory singleton

| Agente | Temp | Função |
|--------|------|--------|
| DraftingAgent | 0.8 | Rascunho bruto estrutural |
| StylistAgent | 0.7 | Refinamento género/tensão |
| TechnicalEditorAgent | 0.3 | Lore consistency, anti-slop, PT-BR |
| CanonCriticAgent | 0.3 | Auditoria canon/lore |
| StyleCriticAgent | 0.3 | Estilo e slop |
| FlowCriticAgent | 0.3 | Pacing e transições |
| SynthesisAgent | 0.3 | Correção baseada em crítica |

Regras embedding no system_prompt (TechnicalEditorAgent + CanonCriticAgent):
- Verification of lore consistency against book_data (world.md, canon.md, characters.md)
- POV and tone consistency per voice.md
- PT-PT → PT-BR localization
- Anti-slop guardrails

Lore completo via `book_data/lore_data` = world.md + canon.md + characters.md (carregados por DraftChaptersStep).

Skills em `skills/`:
- `create_agent.py`: CustomLocalizerAgent (ROLE_NAME="custom_localizer")
- `redundancy_detector.py`: detects repeated technical terms (configurable target_words, empty by default)

## LLM Client (`llm.py`)

Função `call_llm()` — unifica Anthropic/OpenAI/Gemini/OpenRouter via httpx.

Prioridades de modelo: `override_model` → env específico do provider → `AUTOBOOK_*_MODEL` → default.

Max tokens: 16000 (escrita) / 8000 (judge/review) para Anthropic. 8000/4000 para outros.

Retry: 3 tentativas com backoff exponencial (2s, 4s). Suporte a Retry-After header (429).

Failover: lista separada por vírgula em AUTOBOOK_JUDGE_MODEL.

OpenRouter: headers HTTP-Referer + X-Title. Detecta error payloads em 200 OK.

Timeout: AUTOBOOK_PIPELINE_TIMEOUT (padrão 3600s), AUTOBOOK_LLM_TIMEOUT opcional.

Diretrivas de idioma: carregadas via `load_prompt("directives.txt")` → append no system_prompt.

## Genre Strategy (`genre_strategy.py`)

Strategy pattern: AutoBOOK_GENRE carrega `genres/{LANG}/{genre}.txt` com fallback hierarquico:
1. `genres/{LANG}/{genre}.txt`
2. `genres/EN/{genre}.txt`
3. `genres/{LANG}/drama.txt`
4. `genres/EN/drama.txt`

Gêneros disponíveis: `genres/EN/` e `genres/PT-BR/` com `drama.txt`.

`drama.txt` (PT-BR): 26 regras incluindo meta ~3200 palavras, padrões a evitar (sensoriais tríades, "Ele não [verbo]", explicações excessivas, etc).

## Prompt Loader (`prompt_loader.py`)

- `load_prompt(name)`: carrega `prompts/{LANG}/{name}`, fallback EN
- `load_slop_config()`: carrega `prompts/{LANG}/slop.json`
- `load_genre_rules()`: wrapper para GenreStrategy
- `load_slop_rules_instruction()`: formata slop.json como instruções legíveis para LLM

Prompts disponíveis (PT-BR/EN):
- `draft_chapter_system.txt` + `draft_chapter_user.txt`
- `gen_revision_system.txt` + `gen_revision_user.txt`
- `continuity.json` + `editorial.json`
- `directives.txt`
- `slop.json`

## Anti-Slop (`slop.json`)

Estrutura JSON com:
- `tier1_banned`: palavras kill on sight (delve, utilize, leverage, etc)
- `tier2_suspicious`: suspeitas em clusters (3+ no mesmo parágrafo)
- `tier3_filler`: frases sem informação
- `transition_openers`: palavras que iniciam parágrafos
- `fiction_ai_tells`: tropos de IA em ficção
- `structural_ai_tics`: padrões estruturais de IA
- `telling_patterns`: padrões de telling vs showing
- `instruction_templates`: templates para injetar nos prompts

## Evaluate (`evaluate.py`)

Modos: `--foundation`, `--chapter=N`, `--full`
Output: stdout + `logs/eval_logs/{timestamp}.json`

Slop mecânico (`slop_score`):
- tier1/2/3 hits com contagens
- em-dash density (por 1000 palavras)
- sentence_length_cv (coeficiente variação)
- transition_opener_ratio
- slop_penalty (0-10)

LLM Judge usa modelo separado (AUTOBOOK_JUDGE_MODEL) para evitar self-congratulation.

## Voice Profile (`book_data/voice.md`)

Part 1 — Guardrails permanentes (all novels):
- Tier 1 Banned: 20+ palavras
- Tier 2 Suspicious: 30+ palavras (cluster detection)
- Tier 3 Filler: 11 padrões frasais
- Structural slop: 6 padrões (paragraph template, sentence uniformity, transitions, symmetry, hedge, em-dash, lists)
- Smell test: 4 perguntas

Part 2 — Voice Identity (per novel, gerada na foundation):
- Tone, Sentence Rhythm, Vocabulary Register, POV/Tense, Dialogue Conventions
- Exemplar Passages (3-5 parágrafos)
- Anti-Exemplars (3-5 parágrafos)

Estado atual: Part 2 vazia (placeholders HTML comments).

## Continuity Verification (`verify_continuity.py`)

Parser outline.md → LLM judge analisa timeline, repetições, conflitos espaciais, transições quebradas.
Output: `logs/eval_logs/continuity_*.json`

## Estado do Projeto

**book_data/ está VAZIO** (todos os .md com 0 bytes):
- world.md, characters.md, outline.md, canon.md, MYSTERY.md, editorial.md = 0 bytes
- state.json = 0 bytes
- voice.md = 6981 bytes (completo, apenas Part 1)

**chapters/ está VAZIO** (.gitkeep apenas)

O projeto está na fase inicial — nenhum livro foi gerado nesta branch ainda.

## Configuração .env

```env
AUTOBOOK_PROVIDER=openrouter
AUTOBOOK_PIPELINE_TIMEOUT=3600
AUTOBOOK_LOG_TRUNCATE_LIMIT=300
AUTOBOOK_LANGUAGE=PT-BR
AUTOBOOK_GENRE=drama
AUTOBOOK_WRITER_MODEL=openrouter/owl-alpha
AUTOBOOK_JUDGE_MODEL=nvidia/nemotron-3-super-120b-a12b:free,openrouter/owl-alpha,openrouter/free
AUTOBOOK_REVIEW_MODEL=nvidia/nemotron-3-super-120b-a12b:free
OPENROUTER_API_KEY=sk-or-v1-...
FAL_KEY=...
ELEVENLABS_API_KEY=...
```

## Dependências (pyproject.toml)
- Python >= 3.12
- httpx >= 0.28.1
- python-dotenv >= 1.2.2
- Instalar: `uv sync`

## Testes (tests/)
12 arquivos, ~40 testes:
- `test_continuity.py` — validação de continuidade
- `test_evaluate_unit.py` — unitário do evaluate
- `test_foundation_pipeline.py` — pipeline foundation
- `test_generation_flow.py` — fluxo de geração
- `test_ideation_pipeline.py` — pipeline ideação
- `test_integration.py` — testes de integração
- `test_language_support.py` — suporte multi-idioma
- `test_llm_connectivity.py` — conectividade LLM
- `test_llm_unit.py` — unitário LLM
- `test_logging.py` — logging
- `test_typeset.py` — typesetting

Rodar: `uv run --with pytest pytest tests/`

## Legacy (legacy/)
Scripts históricos do projeto original:
- `gen_art.py`, `gen_cover_composite.py`, `gen_cover_print.py` — geração de arte/capa
- `gen_audiobook.py` — geração de audiobook
- `seed.py` — geração de seeds
- `build_outline.py` — construção de outline
- `review.py` — revisão
- `draft_chapter.py` — draft de capítulo
- `run_drafts.py` — batch de drafts
- `reader_panel.py` — painel de leitores
- `build_arc_summary.py` — resumo de arco
- `gen_art_directions.py` — direções de arte
- `audiobook_voices.json` — vozes de audiobook

## Typeset (typeset/)
- `novel.tex` — template LaTeX principal
- `chapters_content.tex` — conteúdo dos capítulos
- `build_tex.py` — build LaTeX
- `epub_front_matter.md`, `epub_back_cover.md`, `epub_colophon.md` — EPUB
- `epub_style.css` — CSS EPUB
- `epub_metadata.yaml` — metadados EPUB

## Landing (landing/)
- `index.html` — landing page do livro

## Workflows

### Gerar livro completo (interativo):
```bash
uv run python run.py --pipeline ideation           # Criar seed
uv run python run.py --pipeline foundation         # Gerar bíblias
uv run python run.py --pipeline book_generation    # Gerar capítulos
uv run python run.py --pipeline editorial_revision # Revisar
```

### Gerar livro completo (autônomo):
```bash
uv run python run.py --pipeline book_generation --from-scratch --yes
```

### Regenerar capítulo específico:
```bash
uv run python run.py --pipeline book_generation --chapter 5
uv run python run.py --pipeline book_generation --chapter 1-3,7
```

## Changelog de Ideias Iteração

O projeto suporta rastreamento de evolução via:
- `doc/results.tsv` — log histórico de tentativas de capítulos
- `doc/arc_summary.md` — resumo de arco regenerável
- `logs/generation_attempts/chNN_attemptNN/` — arquivos intermediários por tentativa
- `logs/eval_logs/` — relatórios JSON de avaliação
- `logs/pipeline.log` — log consolidado do orquestrador

## Notas de Design
- Inspirado em karpathy/autoresearch (modify-evaluate-keep/discard loop)
- Sanderson's Laws para magic/systems
- Save the Cat beats para estrutura
- Dan Harmon's Story Circle
- MICE Quotient (Milieu/Idea/Character/Event)
- LLM-as-Judge com modelo separado (evitar self-congratulation)
- Git autosave para proteção de progresso
