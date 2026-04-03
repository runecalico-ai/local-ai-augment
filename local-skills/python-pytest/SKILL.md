---
name: python-pytest
description: Use when writing, reviewing, debugging, or refactoring Python pytest tests, fixing flaky or failing pytest runs, or working with fixtures, parametrization, mocking, monkeypatch, or async tests.
---

# Python Pytest

Expert guidance for writing maintainable Python tests with pytest while matching repository conventions before introducing new fixtures, markers, or plugins.

## When to Use This Skill

- Writing new pytest test files
- Reviewing or refactoring existing tests
- Debugging flaky or failing tests
- Setting up fixtures or parametrization
- Implementing mocking or async tests

## When Not to Use This Skill

- The repo is still centered on `unittest` or another non-pytest runner.
- The task is a non-test Python change and pytest behavior is not the focus.
- The main problem is the project runner or build pipeline rather than pytest tests themselves.

## Procedure

1. Inspect the repository first: existing `tests/`, `conftest.py`, `pytest.ini` or `pyproject.toml`, custom markers, shared helpers, async plugins, loop-scope settings, and current test commands.
2. Reuse local patterns before adding new ones. Do not invent markers, directory layouts, snapshot tooling, async plugins, or coverage commands if the repo already has conventions.
3. Match the task type to the workflow: for bug fixes or behavior changes, write or update the minimal failing test first; for review or debugging work, inspect or reproduce the current failure before adding tests.
4. Prefer simple defaults when the repo has no pattern: function-scoped fixtures, bare `assert`, `tmp_path`, `monkeypatch`, parametrization, and boundary mocks.
5. Run the narrowest target first, then broaden to the repo's standard command once the local test passes.
6. Open the linked reference files only for advanced fixture composition, async behavior, complex mocking, or framework-specific examples. Treat them as patterns to adapt, not drop-in templates.

## Quick Reference

| Situation | Default action |
| --- | --- |
| New behavior or bug | Write the smallest failing test first |
| Review or debug task | Inspect the current suite or reproduce the failure before editing tests |
| Shared setup | Reuse an existing fixture before adding a new shared one |
| Async code | Detect the repo's async test plugin before choosing markers or fixtures |
| External I/O | Prefer mocks or fakes; use the repo's existing integration selection mechanism if real services are required |
| Optional dependency unavailable | Prefer `pytest.importorskip(...)` or `skipif(...)` with a reason |
| Known tracked bug | Prefer `xfail(strict=True)` and constrain the expected failure mode when known |
| Coverage or parallel runs | Use only repo-supported plugins and commands |

## Optional Capabilities

- Async tests are plugin-dependent. Reuse the repo's current async plugin and mode. In `pytest-asyncio`, `strict` is the safe default when async plugins may coexist; `auto` is a convenience mode for asyncio-only repos that already standardize on it.
- Coverage commands such as `--cov` require `pytest-cov`.
- Parallel execution with `-n` requires `pytest-xdist`.
- Snapshot tests are repo-specific; only use snapshot markers or tooling if the repo already has them.

## Review and Debug

### Review Checklist

- Match the repo's existing fixtures, markers, plugins, and test layout before suggesting new ones.
- Prefer behavior-focused assertions over deep implementation-detail mocking.
- Check determinism, isolation, and scope: no shared state, real network access, or sleep-driven coordination in unit tests.
- Flag dependency or config changes explicitly instead of smuggling them in through examples.

### Debug Checklist

- Confirm the failing target first: collection error, fixture resolution error, plugin/config issue, or behavioral failure.
- Inspect `conftest.py`, pytest config, installed plugins, marker registration, and any async test helpers before changing tests.
- For flaky tests, remove real sleeps, shared globals, and order-dependent assertions before adding retries or broader changes.
- Re-run the narrowest failing target first, then the repo's broader command once the local issue is fixed.

## Core Principles

- Match the repo's fixtures, markers, plugins, async backend, and runner before adding anything new.
- Prefer one focused test over a full suite scaffold.
- Patch at the lookup site, not the provider definition.
- Prefer deterministic signals over sleeps, live network calls, shared globals, or ad hoc retries.
- Use skip/xfail only for genuine environment limits or tracked known issues, never to hide a new failure.

## Common Mistakes

- Copying framework-specific examples wholesale instead of adapting the repo's existing patterns.
- Adding marker registration, plugin config, or direct `pytest` commands without checking the repo runner first.
- Introducing `pytest-asyncio` markers or fixtures in a repo that uses `anyio`, `pytest-trio`, or marker-free auto mode.
- Reaching for SQLite or a new database harness before reusing the repo's current one.
- Overusing autouse fixtures, deep mocks, or boilerplate AAA comments when explicit fixtures and direct assertions are enough.

## Reference Map

- **[Fixture Patterns](./references/fixture-patterns.md)**: Advanced fixture composition, autouse caveats, transaction patterns, and teardown guidance.
- **[Mocking Strategies](./references/mocking-strategies.md)**: Boundary mocking, patch-target rules, time/randomness patterns, and repository seams.
- **[Async Testing Index](./references/async-testing.md)**: Plugin-neutral async decision guide and failure triage.
- **[Pytest-Asyncio Patterns](./references/async-pytest-asyncio.md)**: `pytest-asyncio` configuration, fixtures, and concurrency patterns.
- **[AnyIO Patterns](./references/async-anyio.md)**: `anyio`-based async tests and task-group patterns.
- **[Pytest-Trio Patterns](./references/async-pytest-trio.md)**: Trio-specific test and nursery patterns.
- **[Framework-Specific Example Fragments](./references/test-templates.md)**: Stack-specific examples to adapt only when the repo already uses that stack.
