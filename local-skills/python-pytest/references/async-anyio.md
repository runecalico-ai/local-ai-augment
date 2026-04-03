# Async Testing with AnyIO

Use this file only when the repo already uses the AnyIO pytest plugin.

Reuse the repo's current backend selection, markers, and fixture style. Do not mix `@pytest.mark.anyio` with `pytest-asyncio`-specific decorators or config unless the repo already does so intentionally.

## Signals That This Is AnyIO

- Tests use `@pytest.mark.anyio`
- The repo defines an `anyio_backend` fixture
- Concurrency examples use `anyio.create_task_group()` or `anyio.fail_after()`

## Basic Test

```python
import pytest
from myapp.api import fetch_data

@pytest.mark.anyio
async def test_fetch_data():
    result = await fetch_data()
    assert result["status"] == "ok"
```

## Backend Selection

```python
import pytest

@pytest.fixture
def anyio_backend():
    return "asyncio"  # Mirror the repo's existing backend choice.
```

If the repo already parametrizes backends, mirror that matrix instead of collapsing it to one backend.

## Async Fixtures

```python
import pytest
from myapp.http import AsyncHTTPClient

pytestmark = pytest.mark.anyio

@pytest.fixture
async def async_client(anyio_backend):
    client = AsyncHTTPClient()
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()
```

## Task Groups and Timeouts

```python
import anyio
import pytest

@pytest.mark.anyio
async def test_background_task():
    seen = []

    async def worker():
        seen.append("done")

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(worker)

    assert seen == ["done"]

@pytest.mark.anyio
async def test_guard_timeout():
    event = anyio.Event()
    event.set()

    with anyio.fail_after(1):
        await event.wait()
```

Use `fail_after()` or `move_on_after()` only as a guard around deterministic signals, not as a coordination primitive.

## Common Mistakes

- Adding `@pytest.mark.asyncio` because an example elsewhere used it.
- Mixing raw `asyncio` task orchestration into code that the repo already expresses through AnyIO task groups.
- Forgetting to mirror the repo's `anyio_backend` fixture or backend matrix.