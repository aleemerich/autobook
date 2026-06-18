# Pipelines

Autobook pipelines use the Command/Composite pattern defined in
`pipelines/base.py`: each `Pipeline` contains an ordered list of `Step`s, and
each step receives a mutable context dictionary.

## Central Registry

`pipelines/registry.py` declares the available pipelines through
`PipelineSpec`.

| Pipeline | Class | Work branch protected | Relevant flags |
| --- | --- | --- | --- |
| `ideation` | `IdeationPipeline` | Yes | none |
| `foundation` | `FoundationPipeline` | Yes | none |
| `book_generation` | `BookGenerationPipeline` | Yes | `--from-scratch`, `--chapter` |
| `editorial_revision` | `EditorialRevisionPipeline` | Yes | `--chapter` |

All main pipelines require an `autobook/<slug>` branch.

## Entry Flow

```mermaid
flowchart TD
    A["run.py"] --> B{"empty argv?"}
    B -- yes --> C["cli/wizard.py"]
    C --> D["discover_project_state"]
    C --> E["select pipeline"]
    E --> F["run.main(argv)"]
    B -- no --> G["argparse"]
    F --> G
    G --> H["get_pipeline_spec"]
    H --> I{"requires_work_branch?"}
    I -- yes --> J["ensure_not_main_for_generation"]
    I -- no --> K["spec.factory()"]
    J --> K
    K --> L["pipeline.run(context)"]
```

## Ideation

Responsibility: turn initial creative input into a usable book seed and initial
state.

```mermaid
flowchart LR
    Q["Questionnaire or context"] --> C["concepts"]
    C --> S["selection"]
    S --> M["optional MYSTERY.md"]
    M --> State["state.json"]
```

Main helpers: `pipelines/ideation_steps/selection.py`.

Common outputs:

- `seed.txt`
- `book_data/MYSTERY.md`
- `book_data/state.json`

## Foundation

Responsibility: generate the structural bibles for the book from `seed.txt`,
`voice.md`, `MYSTERY.md` and `docs/en/others/CRAFT.md`.

```mermaid
flowchart LR
    Seed["seed.txt"] --> World["world.md"]
    World --> Characters["characters.md"]
    Characters --> Outline["outline.md"]
    Outline --> Canon["canon.md"]
    Canon --> State["state.json"]
```

Main helpers:

- `foundation_steps/context.py`
- `foundation_steps/persistence.py`

Outputs:

- `book_data/world.md`
- `book_data/characters.md`
- `book_data/outline.md`
- `book_data/canon.md`
- `book_data/state.json`

## Book Generation

Responsibility: generate chapters, critique, revise, evaluate, validate
continuity and persist the best attempt.

```mermaid
flowchart TD
    Context["context.py\nloads lore and outline"] --> Planning["planning.py\nbeats and prompts"]
    Planning --> Draft["drafting.py\ngenerates beats or chapter"]
    Draft --> Critique["critique.py\nindependent critics"]
    Critique --> Revision["revision.py\nRevisionPlan + synthesis"]
    Revision --> Persistence["persistence.py\nchapter, attempts, state, git"]
    Persistence --> Eval["evaluate.py"]
    Persistence --> Continuity["verify_continuity.py"]
```

Subpackage: `pipelines/book_generation_steps/`.

Important points:

- Chapter count comes from `outline.md`; there is no universal fixed count.
- Beats are used when found; without beats, the pipeline falls back to a full
  chapter draft.
- Critiques are converted to `CriticReport` and consolidated into
  `RevisionPlan`.
- Attempts, critiques and plans are archived under `logs/generation_attempts/`.
- `state.json` records sequential progress.

## Editorial Revision

Responsibility: apply revisions driven by `book_data/editorial.md`, evaluate
attempts and keep the best result.

```mermaid
flowchart TD
    Markdown["editorial.md"] --> Parsing["parsing.py"]
    Chapters["chapters/ch_XX.md"] --> Context["context.py"]
    Parsing --> Brief["revision.py\ncorrective brief"]
    Context --> Brief
    Brief --> Gen["gen_revision.py"]
    Gen --> Eval["evaluate.py"]
    Eval --> Decision{"target reached?"}
    Decision -- yes --> Commit["commit/push"]
    Decision -- no --> Retry["new attempt"]
    Retry --> Brief
```

Subpackage: `pipelines/editorial_revision_steps/`.

Main helpers:

- `config.py`
- `context.py`
- `evaluation.py`
- `parsing.py`
- `revision.py`

## `requires` And `produces` Metadata

`Step` and `Pipeline` support optional metadata:

```python
Step("Name", description="...", requires=["outline"], produces=["chapter"])
```

They exist for future discovery and documentation. In the current state, they
are not blocking dependency validators.
