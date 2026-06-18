# Pipelines

As pipelines do Autobook usam o padrao Command/Composite definido em
`pipelines/base.py`: cada `Pipeline` contem uma lista ordenada de `Step`s, e
cada step recebe um dicionario de contexto mutavel.

## Registro Central

`pipelines/registry.py` declara as pipelines disponiveis por meio de
`PipelineSpec`.

| Pipeline | Classe | Protegida por branch | Flags relevantes |
| --- | --- | --- | --- |
| `ideation` | `IdeationPipeline` | Sim | nenhuma especial |
| `foundation` | `FoundationPipeline` | Sim | nenhuma especial |
| `book_generation` | `BookGenerationPipeline` | Sim | `--from-scratch`, `--chapter` |
| `editorial_revision` | `EditorialRevisionPipeline` | Sim | `--chapter` |

Todas as pipelines principais exigem branch `autobook/<slug>`.

## Fluxo De Entrada

```mermaid
flowchart TD
    A["run.py"] --> B{"argv vazio?"}
    B -- sim --> C["cli/wizard.py"]
    C --> D["discover_project_state"]
    C --> E["seleciona pipeline"]
    E --> F["run.main(argv)"]
    B -- nao --> G["argparse"]
    F --> G
    G --> H["get_pipeline_spec"]
    H --> I{"requires_work_branch?"}
    I -- sim --> J["ensure_not_main_for_generation"]
    I -- nao --> K["spec.factory()"]
    J --> K
    K --> L["pipeline.run(context)"]
```

## Ideation

Responsabilidade: transformar entradas criativas iniciais em uma semente de
obra e estado inicial.

```mermaid
flowchart LR
    Q["Questionario ou contexto"] --> C["conceitos"]
    C --> S["selecao"]
    S --> M["MYSTERY.md opcional"]
    M --> State["state.json"]
```

Helpers principais: `pipelines/ideation_steps/selection.py`.

Saidas comuns:

- `seed.txt`
- `book_data/MYSTERY.md`
- `book_data/state.json`

## Foundation

Responsabilidade: gerar as biblias estruturais da obra a partir de `seed.txt`,
`voice.md`, `MYSTERY.md` e `docs/en/others/CRAFT.md`.

```mermaid
flowchart LR
    Seed["seed.txt"] --> World["world.md"]
    World --> Characters["characters.md"]
    Characters --> Outline["outline.md"]
    Outline --> Canon["canon.md"]
    Canon --> State["state.json"]
```

Helpers principais:

- `foundation_steps/context.py`
- `foundation_steps/persistence.py`

Saidas:

- `book_data/world.md`
- `book_data/characters.md`
- `book_data/outline.md`
- `book_data/canon.md`
- `book_data/state.json`

## Book Generation

Responsabilidade: gerar capitulos, criticar, revisar, avaliar, validar
continuidade e persistir a melhor tentativa.

```mermaid
flowchart TD
    Context["context.py\ncarrega lore e outline"] --> Planning["planning.py\nbeats e prompts"]
    Planning --> Draft["drafting.py\ngera beats ou capitulo"]
    Draft --> Critique["critique.py\ncriticos independentes"]
    Critique --> Revision["revision.py\nRevisionPlan + synthesis"]
    Revision --> Persistence["persistence.py\ncapitulo, attempts, state, git"]
    Persistence --> Eval["evaluate.py"]
    Persistence --> Continuity["verify_continuity.py"]
```

Subpacote: `pipelines/book_generation_steps/`.

Pontos importantes:

- Quantidade de capitulos vem do `outline.md`; nao ha numero fixo universal.
- Beats sao usados quando encontrados; sem beats, o pipeline cai para draft de
  capitulo inteiro.
- Criticas sao convertidas para `CriticReport` e consolidadas em
  `RevisionPlan`.
- Tentativas, criticas e planos sao arquivados em `logs/generation_attempts/`.
- `state.json` registra progresso sequencial.

## Editorial Revision

Responsabilidade: aplicar revisoes orientadas por `book_data/editorial.md`,
avaliar tentativas e preservar o melhor resultado.

```mermaid
flowchart TD
    Markdown["editorial.md"] --> Parsing["parsing.py"]
    Chapters["chapters/ch_XX.md"] --> Context["context.py"]
    Parsing --> Brief["revision.py\nbrief corretivo"]
    Context --> Brief
    Brief --> Gen["gen_revision.py"]
    Gen --> Eval["evaluate.py"]
    Eval --> Decision{"atingiu alvo?"}
    Decision -- sim --> Commit["commit/push"]
    Decision -- nao --> Retry["nova tentativa"]
    Retry --> Brief
```

Subpacote: `pipelines/editorial_revision_steps/`.

Helpers principais:

- `config.py`
- `context.py`
- `evaluation.py`
- `parsing.py`
- `revision.py`

## Metadados `requires` E `produces`

`Step` e `Pipeline` suportam metadados opcionais:

```python
Step("Nome", description="...", requires=["outline"], produces=["chapter"])
```

Eles existem para discovery e documentacao futura. No estado atual, nao sao
validadores bloqueantes de dependencias.
