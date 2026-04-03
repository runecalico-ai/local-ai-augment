# Async Testing

Plugin-neutral guide for choosing the right async pytest pattern.

Inspect the repo's async plugin, markers, fixture decorators, loop-scope settings, and test runner before copying any async example. Do not add a plugin because a reference happens to show it.

## Start Here

1. Search the repo for `@pytest.mark.asyncio`, `@pytest.mark.anyio`, `@pytest.mark.trio`, `pytest_asyncio.fixture`, `anyio_backend`, and Trio task-group usage.
2. Inspect pytest config for async settings such as `asyncio_mode`, `asyncio_default_fixture_loop_scope`, and `asyncio_default_test_loop_scope`.
3. Reuse the repo's current async runner and plugin. If the repo does not already signal a plugin choice, stop and clarify before inventing one.

## Choose a Reference

| Repo signal | Open this reference |
| --- | --- |
| `@pytest.mark.asyncio`, `pytest_asyncio.fixture`, `asyncio_mode` | [Pytest-Asyncio Patterns](async-pytest-asyncio.md) |
| `@pytest.mark.anyio`, `anyio_backend`, `anyio.create_task_group()` | [AnyIO Patterns](async-anyio.md) |
| `@pytest.mark.trio`, `trio.open_nursery()`, `trio.fail_after()` | [Pytest-Trio Patterns](async-pytest-trio.md) |
| No clear async pattern yet | Inspect CI and dependencies first, then ask before adding a plugin |

## Common Rules Across Async Backends

- Treat timeouts as failure ceilings, not coordination primitives.
- Use deterministic signals such as events, queues, task-group completion, or callback flags instead of sleeps.
- Patch the lookup site and mock the async boundary rather than deep internals.
- Avoid live network and persistent database side effects unless the repo's integration mechanism already allows them.
- Use `tmp_path`-backed or repo-provided ephemeral resources for async fixtures that touch the filesystem.

## Failure Triage

- `Unknown mark` or `fixture not found`: wrong plugin, missing dependency, or wrong runner.
- `ScopeMismatch`, closed-loop, or event-loop reuse errors: inspect fixture scope, loop-scope settings, and backend-specific decorators.
- `collected 0 items` or import failures: confirm the repo's standard runner, interpreter, and plugin environment.
- Flaky async tests: remove real sleeps, shared globals, and order-dependent assertions before adding retries.

## Plugin References

- [Pytest-Asyncio Patterns](async-pytest-asyncio.md)
- [AnyIO Patterns](async-anyio.md)
- [Pytest-Trio Patterns](async-pytest-trio.md)
