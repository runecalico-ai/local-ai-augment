# Async Testing

Comprehensive guide to testing asynchronous Python code with pytest.

## Table of Contents

- Setup and Configuration
- Basic Async Tests
- Async Fixtures
- Mocking Async Functions
- Testing Concurrent Operations
- Common Patterns
- Error Handling

## Setup and Configuration

### Installing pytest-asyncio

```bash
pip install pytest-asyncio
```

### Configuration

Add to `pytest.ini`:

```ini
[pytest]
asyncio_mode = auto
```

Or configure per-file:

```python
# tests/test_async.py
import pytest

pytest_plugins = ('pytest_asyncio',)
```

## Basic Async Tests

### Simple Async Test

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result == "expected_value"
```

### Testing Async Coroutines

```python
@pytest.mark.asyncio
async def test_fetch_data():
    async def fetch():
        await asyncio.sleep(0.1)
        return {"status": "success"}

    data = await fetch()
    assert data["status"] == "success"
```

### Testing with asyncio.gather

```python
@pytest.mark.asyncio
async def test_concurrent_fetches():
    async def fetch(n):
        await asyncio.sleep(0.01)
        return n * 2

    results = await asyncio.gather(
        fetch(1),
        fetch(2),
        fetch(3)
    )

    assert results == [2, 4, 6]
```

## Async Fixtures

### Basic Async Fixture

```python
import pytest

@pytest.fixture
async def async_client():
    """Provides an async HTTP client."""
    client = AsyncHTTPClient()
    await client.connect()
    yield client
    await client.disconnect()
```

### Async Fixture with Setup/Teardown

```python
@pytest.fixture
async def database():
    """Provides async database connection."""
    db = AsyncDatabase("test.db")
    await db.connect()
    await db.create_tables()

    yield db

    await db.drop_tables()
    await db.disconnect()

@pytest.mark.asyncio
async def test_insert_user(database):
    await database.insert("users", {"name": "Alice"})
    users = await database.query("SELECT * FROM users")
    assert len(users) == 1
```

### Async Factory Fixture

```python
@pytest.fixture
async def user_factory(database):
    """Factory for creating test users asynchronously."""
    created_users = []

    async def create_user(name="test_user", email=None):
        user = await database.create_user(
            name=name,
            email=email or f"{name}@example.com"
        )
        created_users.append(user)
        return user

    yield create_user

    # Cleanup
    for user in created_users:
        await database.delete_user(user.id)

@pytest.mark.asyncio
async def test_multiple_users(user_factory):
    alice = await user_factory(name="alice")
    bob = await user_factory(name="bob")

    assert alice.id != bob.id
```

### Scoped Async Fixtures

```python
@pytest.fixture(scope="session")
async def event_loop():
    """Provides session-scoped event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="module")
async def app():
    """Module-scoped application instance."""
    application = await create_app()
    yield application
    await application.shutdown()
```

## Mocking Async Functions

### Using AsyncMock

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch("myapp.api.fetch_user")
async def test_get_user_profile(mock_fetch):
    # Setup AsyncMock
    mock_fetch.return_value = {"id": 1, "name": "Alice"}

    # Test
    profile = await get_user_profile(1)

    assert profile["name"] == "Alice"
    mock_fetch.assert_awaited_once_with(1)
```

### Mocking Async Context Managers

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_async_context_manager():
    mock_session = MagicMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    mock_session.fetch = AsyncMock(return_value={"data": "value"})

    async with mock_session as session:
        result = await session.fetch()

    assert result == {"data": "value"}
    mock_session.__aenter__.assert_awaited_once()
    mock_session.__aexit__.assert_awaited_once()
```

### Mocking with Side Effects

```python
@pytest.mark.asyncio
@patch("myapp.api.fetch_data")
async def test_retry_logic(mock_fetch):
    # First call raises exception, second succeeds
    mock_fetch.side_effect = [
        Exception("Network error"),
        {"status": "ok"}
    ]

    result = await fetch_with_retry()
    assert result["status"] == "ok"
    assert mock_fetch.await_count == 2
```

### Mocking Async Generators

```python
@pytest.mark.asyncio
async def test_async_generator():
    async def mock_stream():
        for i in range(3):
            yield i

    with patch("myapp.stream.data_stream", return_value=mock_stream()):
        items = []
        async for item in data_stream():
            items.append(item)

        assert items == [0, 1, 2]
```

## Testing Concurrent Operations

### Testing Parallel Execution

```python
@pytest.mark.asyncio
async def test_parallel_api_calls():
    async def fetch(url):
        await asyncio.sleep(0.1)
        return f"Data from {url}"

    urls = ["url1", "url2", "url3"]
    results = await asyncio.gather(*[fetch(url) for url in urls])

    assert len(results) == 3
    assert all("Data from" in r for r in results)
```

### Testing Task Cancellation

```python
@pytest.mark.asyncio
async def test_task_cancellation():
    async def long_running_task():
        try:
            await asyncio.sleep(10)
            return "completed"
        except asyncio.CancelledError:
            return "cancelled"

    task = asyncio.create_task(long_running_task())
    await asyncio.sleep(0.01)
    task.cancel()

    result = await task
    assert result == "cancelled"
```

### Testing with Timeouts

```python
@pytest.mark.asyncio
async def test_operation_timeout():
    async def slow_operation():
        await asyncio.sleep(5)
        return "result"

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_operation(), timeout=0.1)
```

### Testing Race Conditions

```python
@pytest.mark.asyncio
async def test_first_completed():
    async def fast():
        await asyncio.sleep(0.01)
        return "fast"

    async def slow():
        await asyncio.sleep(1)
        return "slow"

    done, pending = await asyncio.wait(
        [fast(), slow()],
        return_when=asyncio.FIRST_COMPLETED
    )

    result = list(done)[0].result()
    assert result == "fast"

    # Cancel pending tasks
    for task in pending:
        task.cancel()
```

## Common Patterns

### Testing Async Iterators

```python
@pytest.mark.asyncio
async def test_async_iterator():
    class AsyncCounter:
        def __init__(self, max_count):
            self.max_count = max_count
            self.count = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.count >= self.max_count:
                raise StopAsyncIteration
            self.count += 1
            await asyncio.sleep(0.01)
            return self.count

    counter = AsyncCounter(3)
    items = []
    async for item in counter:
        items.append(item)

    assert items == [1, 2, 3]
```

### Testing WebSocket Connections

```python
@pytest.mark.asyncio
async def test_websocket_communication():
    async with websockets.connect("ws://localhost:8765") as ws:
        await ws.send("Hello")
        response = await ws.recv()
        assert response == "Hello back"
```

### Testing Message Queues

```python
@pytest.mark.asyncio
async def test_queue_processing():
    queue = asyncio.Queue()

    # Producer
    async def produce():
        for i in range(5):
            await queue.put(i)
            await asyncio.sleep(0.01)
        await queue.put(None)  # Sentinel

    # Consumer
    async def consume():
        items = []
        while True:
            item = await queue.get()
            if item is None:
                break
            items.append(item)
        return items

    producer_task = asyncio.create_task(produce())
    consumer_task = asyncio.create_task(consume())

    items = await consumer_task
    await producer_task

    assert items == [0, 1, 2, 3, 4]
```

### Testing Async Callbacks

```python
@pytest.mark.asyncio
async def test_async_callback():
    callback_called = False
    callback_value = None

    async def callback(value):
        nonlocal callback_called, callback_value
        callback_called = True
        callback_value = value

    await process_with_callback(data="test", on_complete=callback)

    assert callback_called
    assert callback_value == "processed: test"
```

## Error Handling

### Testing Async Exceptions

```python
@pytest.mark.asyncio
async def test_async_exception():
    async def failing_operation():
        await asyncio.sleep(0.01)
        raise ValueError("Operation failed")

    with pytest.raises(ValueError, match="Operation failed"):
        await failing_operation()
```

### Testing Exception Propagation

```python
@pytest.mark.asyncio
async def test_exception_in_gather():
    async def task_ok():
        await asyncio.sleep(0.01)
        return "ok"

    async def task_error():
        await asyncio.sleep(0.01)
        raise RuntimeError("Task error")

    with pytest.raises(RuntimeError, match="Task error"):
        await asyncio.gather(task_ok(), task_error())
```

### Testing Error Recovery

```python
@pytest.mark.asyncio
async def test_error_recovery():
    attempt_count = 0

    async def unreliable_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionError("Connection failed")
        return "success"

    result = await retry_async(unreliable_operation, max_attempts=5)

    assert result == "success"
    assert attempt_count == 3
```

## Integration with Async Frameworks

### Testing FastAPI

```python
import pytest
from httpx import AsyncClient
from myapp.main import app

@pytest.mark.asyncio
async def test_fastapi_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/users/1")
        assert response.status_code == 200
        assert response.json()["id"] == 1
```

### Testing aiohttp

```python
import pytest
from aiohttp import ClientSession

@pytest.fixture
async def aio_session():
    async with ClientSession() as session:
        yield session

@pytest.mark.asyncio
async def test_aiohttp_request(aio_session):
    async with aio_session.get("http://httpbin.org/get") as response:
        data = await response.json()
        assert response.status == 200
```

### Testing Trio (Alternative to asyncio)

```python
import pytest
import trio

@pytest.mark.trio
async def test_trio_function():
    async def background_task():
        await trio.sleep(0.1)
        return "done"

    result = await background_task()
    assert result == "done"
```

## Best Practices

### Do's

✅ Always mark async tests with `@pytest.mark.asyncio`
✅ Use `AsyncMock` for mocking async functions
✅ Clean up async resources in fixture teardown
✅ Use `asyncio.wait_for()` to prevent hanging tests
✅ Test both success and exception paths
✅ Use proper await syntax for all async operations

### Don'ts

❌ Don't mix sync and async code without proper bridging
❌ Don't forget to await async functions in tests
❌ Don't use `time.sleep()` in async code (use `asyncio.sleep()`)
❌ Don't ignore CancelledError exceptions
❌ Don't create unbounded async tasks without cleanup

## Debugging Async Tests

### Enable Debug Mode

```python
import asyncio
import logging

@pytest.fixture(autouse=True)
def enable_asyncio_debug():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    logging.getLogger("asyncio").setLevel(logging.DEBUG)
```

### Detecting Unawaited Coroutines

```python
import warnings

@pytest.fixture(autouse=True)
def warn_unawaited_coroutines():
    warnings.simplefilter("error", RuntimeWarning)
```
