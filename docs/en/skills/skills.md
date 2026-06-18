# Skills

The `skills/` folder contains Python extensions that can register agents or
auxiliary capabilities.

## Current Files

| File | Status | Role |
| --- | --- | --- |
| `skills/create_agent.py` | Functional as example/extension | Defines `CustomLocalizerAgent` and registers through `register(factory)`. |
| `skills/redundancy_detector.py` | Functional utility | Defines `RedundancyDetector` to detect repeated terms. |

## Integration With `AgentFactory`

`agents.py` has `AgentFactory.load_skill_agent(skill_name, **kwargs)`. The
method looks for `skills/{skill_name}.py`, dynamically imports the module and
expects it to expose a `register(factory)` function.

Minimum contract for a loadable skill:

```python
def register(factory):
    factory.register_agent("role_name", AgentClass)
```

After registration, the agent can be created with:

```python
factory.get_agent("role_name", **kwargs)
```

## Current State

Extensibility exists and is tested through the factory contract. There is still
no dedicated CLI to list or validate skills.

## Recommended Improvements

1. Define a standard metadata contract per skill.
2. Add examples of real usage inside pipelines.
3. Add validation/listing support if skills become a larger extension surface.
4. Separate utilities that are not agents from skills that register agents.
