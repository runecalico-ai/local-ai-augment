# Async Testing with pytest-trio

Use this file only when the repo already depends on `pytest-trio` and uses Trio-native test patterns.

Mirror the repo's existing Trio markers and cancel-scope patterns instead of translating examples from `pytest-asyncio`.

## Signals That This Is Trio

- Tests use `@pytest.mark.trio`
- The codebase uses `trio.open_nursery()`
- Timeouts and cancellation use `trio.fail_after()` or `trio.move_on_after()`

## Basic Test

```python
import pytest
from myapp.api import fetch_data

@pytest.mark.trio
async def test_fetch_data():
    result = await fetch_data()
    assert result["status"] == "ok"
```

## Nursery Pattern

```python
import pytest
import trio

@pytest.mark.trio
async def test_background_task():
    seen = []

    async def worker():
        seen.append("done")

    async with trio.open_nursery() as nursery:
        nursery.start_soon(worker)

    assert seen == ["done"]
```

## Timeout and Cancellation

```python
import pytest
import trio

@pytest.mark.trio
async def test_timeout_guard():
    event = trio.Event()
    event.set()

    with trio.fail_after(1):
        await event.wait()
```

Use Trio's cancel scopes as failure guards, not as replacements for deterministic coordination.

## Common Mistakes

- Adding `pytest-asyncio` configuration to a Trio-native repo.
- Mixing `asyncio` primitives such as `asyncio.Event()` into Trio tests.
- Copying AnyIO or `pytest-asyncio` examples without translating them to nurseries and Trio cancellation semantics.