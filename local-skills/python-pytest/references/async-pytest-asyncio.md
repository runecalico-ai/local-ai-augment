# Async Testing with pytest-asyncio

Use this file only when the repo already uses `pytest-asyncio`.

Mirror the repo's existing `asyncio_mode`, loop-scope settings, marker usage, and fixture decorators instead of inventing a new convention.

## Configuration

```ini
[pytest]
# Safe when multiple async plugins may coexist.
asyncio_mode = strict
asyncio_default_fixture_loop_scope = function
asyncio_default_test_loop_scope = function
```

For asyncio-only repos that already standardize on auto mode:

```ini
[pytest]
asyncio_mode = auto
```

## Basic Test

```python
import pytest
from myapp.async_utils import my_async_function

@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result == "expected_value"
```

## Async Fixtures

```python
import pytest
import pytest_asyncio
from myapp.database import AsyncDatabase

@pytest_asyncio.fixture
async def database(tmp_path):
    db = AsyncDatabase(str(tmp_path / "test.db"))
    await db.connect()
    await db.create_tables()
    try:
        yield db
    finally:
        await db.drop_tables()
        await db.disconnect()

@pytest.mark.asyncio
async def test_insert_user(database):
    await database.insert("users", {"name": "Alice"})
    users = await database.query("SELECT * FROM users")
    assert len(users) == 1
```

For broader fixture scopes, keep the loop scope at least as broad as the fixture scope:

```python
import pytest_asyncio
from myapp.main import create_app

@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def app():
    application = await create_app()
    try:
        yield application
    finally:
        await application.shutdown()
```

## Mocking and Concurrency

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_fetch_all_concurrent(monkeypatch):
    async def fake_fetch(url):
        return {"url": url, "status": "ok"}

    monkeypatch.setattr("myapp.asyncio_utils.fetch", fake_fetch)

    from myapp.asyncio_utils import fetch_all

    assert await fetch_all(["item-a", "item-b"]) == [
        {"url": "item-a", "status": "ok"},
        {"url": "item-b", "status": "ok"},
    ]

@pytest.mark.asyncio
async def test_async_api_call(monkeypatch):
    mock_response = AsyncMock(return_value={"status": "ok"})
    monkeypatch.setattr("myapp.client.fetch", mock_response)

    from myapp.client import get_data

    result = await get_data()
    assert result["status"] == "ok"
```

Use `asyncio.wait_for(...)` only as a guard around deterministic signals, not as a replacement for proper coordination.

## Framework Example

```python
import pytest
from httpx import ASGITransport, AsyncClient
from myapp.main import app

@pytest.mark.asyncio
async def test_fastapi_endpoint():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/users/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
```

## Debugging

Use plugin-specific debug settings only if the repo already uses `pytest-asyncio`:

```ini
[pytest]
asyncio_debug = true
```

```python
import pytest
import warnings

@pytest.fixture
def fail_on_unawaited_coroutines():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "error",
            message=r".*was never awaited.*",
            category=RuntimeWarning,
        )
        yield
```