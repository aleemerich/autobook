# Legacy

`legacy/` preserves old scripts, tests and ideas. The folder is not part of the
modern operational contract.

## Current Policy

- `legacy/tests` is ignored by `pytest.ini`.
- When run directly, `legacy/tests` returns success with no tests collected.
- Broken imports or old dependencies inside legacy do not block the modern
  baseline.
- New code should not depend on `legacy/`.

## How To Treat Legacy Files

| Situation | Recommended action |
| --- | --- |
| Script still useful | Migrate to a modern root/package location, add tests and document in `docs/*/scripts/`. |
| Useful idea, old code | Create a clean new module based on the desired behavior. |
| No current use | Keep as historical or remove in a dedicated cleanup round. |

## Commands

```bash
uv run --with pytest pytest legacy/tests -q
```

Expected result: no tests collected, exit code 0.

## Boundary

Legacy should not be used to infer the current architecture. Use
[../architecture/arquitetura.md](../architecture/arquitetura.md) and
[../pipelines/pipelines.md](../pipelines/pipelines.md).
