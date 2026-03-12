# Async Programming Patterns

## Async Basics

### Basic Async Function

```python
import asyncio

async def fetch_data(url: str) -> str:
    """Fetch data asynchronously.

    Args:
        url: URL to fetch data from.

    Returns:
        Response content as string.
    """
    # Simulate I/O operation
    await asyncio.sleep(1)
    return f"Data from {url}"

# Run async function
async def main():
    """Main async function."""
    result = await fetch_data('https://example.com')
    print(result)

# Execute
asyncio.run(main())
```

### Running Multiple Tasks

```python
async def fetch_multiple(urls: list[str]) -> list[str]:
    """Fetch multiple URLs concurrently.

    Args:
        urls: List of URLs to fetch.

    Returns:
        List of responses.
    """
    # Create tasks for concurrent execution
    tasks = [fetch_data(url) for url in urls]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks)

    return results

# Usage
urls = ['https://example.com', 'https://example.org', 'https://example.net']
results = asyncio.run(fetch_multiple(urls))
```

## Task Management

### Creating and Managing Tasks

```python
async def background_task(name: str, delay: int) -> str:
    """Background task that takes some time."""
    print(f"Task {name} started")
    await asyncio.sleep(delay)
    print(f"Task {name} completed")
    return f"Result from {name}"

async def main():
    """Create and manage multiple tasks."""
    # Create tasks (they start immediately)
    task1 = asyncio.create_task(background_task('A', 2))
    task2 = asyncio.create_task(background_task('B', 1))
    task3 = asyncio.create_task(background_task('C', 3))

    # Do other work while tasks run
    print("Tasks are running in background...")

    # Wait for specific task
    result = await task2
    print(f"Got result: {result}")

    # Wait for all remaining tasks
    results = await asyncio.gather(task1, task3)
    print(f"All results: {results}")

asyncio.run(main())
```

### Task Timeout

```python
async def slow_operation() -> str:
    """Slow operation that might timeout."""
    await asyncio.sleep(5)
    return "Done"

async def with_timeout():
    """Run operation with timeout."""
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=2.0)
        print(result)
    except asyncio.TimeoutError:
        print("Operation timed out")

asyncio.run(with_timeout())
```

### Cancellation

```python
async def cancellable_task(name: str) -> None:
    """Task that can be cancelled."""
    try:
        for i in range(10):
            print(f"{name}: Step {i}")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print(f"{name}: Cancelled!")
        raise  # Re-raise to propagate cancellation

async def main():
    """Create and cancel a task."""
    task = asyncio.create_task(cancellable_task('Worker'))

    # Let it run for a bit
    await asyncio.sleep(3)

    # Cancel the task
    task.cancel()

    try:
        await task
    except asyncio.CancelledError:
        print("Task was cancelled")

asyncio.run(main())
```

## Async Context Managers

### Basic Async Context Manager

```python
from typing import AsyncIterator
from contextlib import asynccontextmanager

class AsyncResource:
    """Async resource with context manager."""

    async def __aenter__(self):
        """Async enter."""
        print("Acquiring resource...")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async exit."""
        print("Releasing resource...")
        await asyncio.sleep(0.1)

    async def use(self) -> str:
        """Use the resource."""
        return "Resource used"

async def main():
    """Use async context manager."""
    async with AsyncResource() as resource:
        result = await resource.use()
        print(result)

asyncio.run(main())


# Using asynccontextmanager decorator
@asynccontextmanager
async def managed_resource(name: str) -> AsyncIterator[str]:
    """Create managed async resource."""
    print(f"Setting up {name}")
    await asyncio.sleep(0.1)

    try:
        yield name
    finally:
        print(f"Cleaning up {name}")
        await asyncio.sleep(0.1)

async def use_managed():
    """Use managed resource."""
    async with managed_resource("Database") as db:
        print(f"Using {db}")

asyncio.run(use_managed())
```

## Async Iterators and Generators

### Async Iterator

```python
from typing import AsyncIterator

class AsyncCounter:
    """Async iterator that counts."""

    def __init__(self, start: int, end: int):
        self.current = start
        self.end = end

    def __aiter__(self):
        """Return async iterator."""
        return self

    async def __anext__(self) -> int:
        """Get next value."""
        if self.current >= self.end:
            raise StopAsyncIteration

        await asyncio.sleep(0.1)  # Simulate async operation
        value = self.current
        self.current += 1
        return value

async def main():
    """Use async iterator."""
    async for num in AsyncCounter(1, 5):
        print(num)

asyncio.run(main())
```

### Async Generator

```python
async def async_range(start: int, end: int) -> AsyncIterator[int]:
    """Async generator for range."""
    for i in range(start, end):
        await asyncio.sleep(0.1)
        yield i

async def main():
    """Use async generator."""
    async for num in async_range(1, 5):
        print(num)

asyncio.run(main())


# Async generator for streaming data
async def read_stream(source: str) -> AsyncIterator[str]:
    """Stream data from source."""
    for i in range(10):
        await asyncio.sleep(0.1)
        yield f"Chunk {i} from {source}"

async def process_stream():
    """Process streaming data."""
    async for chunk in read_stream("Database"):
        print(f"Processing: {chunk}")

asyncio.run(process_stream())
```

## Async HTTP with aiohttp

### Basic HTTP Client

```python
import aiohttp

async def fetch_url(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch URL using session."""
    async with session.get(url) as response:
        return await response.text()

async def fetch_all(urls: list[str]) -> list[str]:
    """Fetch multiple URLs concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results

# Usage
urls = ['https://example.com', 'https://example.org']
results = asyncio.run(fetch_all(urls))
```

### Error Handling in Async HTTP

```python
async def fetch_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    max_retries: int = 3
) -> str | None:
    """Fetch URL with retries."""
    for attempt in range(max_retries):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == max_retries - 1:
                print(f"Failed after {max_retries} attempts: {e}")
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return None
```

## Queue-Based Processing

### Async Queue

```python
from asyncio import Queue

async def producer(queue: Queue[int], name: str, count: int) -> None:
    """Produce items and put in queue."""
    for i in range(count):
        item = i
        await queue.put(item)
        print(f"Producer {name} added {item}")
        await asyncio.sleep(0.1)

async def consumer(queue: Queue[int], name: str) -> None:
    """Consume items from queue."""
    while True:
        item = await queue.get()
        print(f"Consumer {name} processing {item}")
        await asyncio.sleep(0.3)
        queue.task_done()

async def main():
    """Run producer-consumer pattern."""
    queue: Queue[int] = Queue(maxsize=5)

    # Create producers
    producers = [
        asyncio.create_task(producer(queue, 'A', 5)),
        asyncio.create_task(producer(queue, 'B', 5)),
    ]

    # Create consumers
    consumers = [
        asyncio.create_task(consumer(queue, '1')),
        asyncio.create_task(consumer(queue, '2')),
    ]

    # Wait for producers to finish
    await asyncio.gather(*producers)

    # Wait for queue to be empty
    await queue.join()

    # Cancel consumers
    for c in consumers:
        c.cancel()

asyncio.run(main())
```

## Async Database Operations

### Async Database with aiosqlite

```python
import aiosqlite

async def create_table(db_path: str) -> None:
    """Create database table."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT
            )
        ''')
        await db.commit()

async def insert_user(db_path: str, name: str, email: str) -> int:
    """Insert user into database."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)',
            (name, email)
        )
        await db.commit()
        return cursor.lastrowid

async def get_all_users(db_path: str) -> list[tuple]:
    """Get all users from database."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute('SELECT * FROM users') as cursor:
            return await cursor.fetchall()

async def main():
    """Database operations."""
    db_path = 'users.db'

    await create_table(db_path)

    # Insert users concurrently
    tasks = [
        insert_user(db_path, 'Alice', 'alice@example.com'),
        insert_user(db_path, 'Bob', 'bob@example.com'),
    ]
    user_ids = await asyncio.gather(*tasks)
    print(f"Created users: {user_ids}")

    # Fetch all users
    users = await get_all_users(db_path)
    print(f"All users: {users}")

asyncio.run(main())
```

## Synchronization Primitives

### Lock

```python
class SharedResource:
    """Shared resource with async lock."""

    def __init__(self):
        self._value = 0
        self._lock = asyncio.Lock()

    async def increment(self) -> None:
        """Thread-safe increment."""
        async with self._lock:
            current = self._value
            await asyncio.sleep(0.1)  # Simulate work
            self._value = current + 1

    @property
    def value(self) -> int:
        """Get current value."""
        return self._value

async def worker(resource: SharedResource, name: str, count: int) -> None:
    """Worker that increments resource."""
    for _ in range(count):
        await resource.increment()
        print(f"Worker {name} incremented")

async def main():
    """Test shared resource."""
    resource = SharedResource()

    workers = [
        asyncio.create_task(worker(resource, 'A', 5)),
        asyncio.create_task(worker(resource, 'B', 5)),
    ]

    await asyncio.gather(*workers)
    print(f"Final value: {resource.value}")  # Should be 10

asyncio.run(main())
```

### Event

```python
async def waiter(event: asyncio.Event, name: str) -> None:
    """Wait for event."""
    print(f"{name} waiting for event...")
    await event.wait()
    print(f"{name} received event!")

async def main():
    """Test event."""
    event = asyncio.Event()

    # Create waiters
    waiters = [
        asyncio.create_task(waiter(event, 'Worker 1')),
        asyncio.create_task(waiter(event, 'Worker 2')),
        asyncio.create_task(waiter(event, 'Worker 3')),
    ]

    # Let them start waiting
    await asyncio.sleep(1)

    # Signal event
    print("Signaling event...")
    event.set()

    # Wait for all waiters
    await asyncio.gather(*waiters)

asyncio.run(main())
```

### Semaphore

```python
async def access_resource(sem: asyncio.Semaphore, name: str) -> None:
    """Access limited resource."""
    async with sem:
        print(f"{name} acquired resource")
        await asyncio.sleep(2)
        print(f"{name} released resource")

async def main():
    """Limit concurrent access."""
    # Only 2 tasks can access resource at once
    semaphore = asyncio.Semaphore(2)

    tasks = [
        asyncio.create_task(access_resource(semaphore, f'Task {i}'))
        for i in range(5)
    ]

    await asyncio.gather(*tasks)

asyncio.run(main())
```

## Error Handling in Async Code

### Handling Task Exceptions

```python
async def failing_task(name: str) -> str:
    """Task that might fail."""
    await asyncio.sleep(1)
    if name == 'fail':
        raise ValueError(f"Task {name} failed")
    return f"Success: {name}"

async def main():
    """Handle task exceptions."""
    tasks = [
        asyncio.create_task(failing_task('ok1')),
        asyncio.create_task(failing_task('fail')),
        asyncio.create_task(failing_task('ok2')),
    ]

    # gather with return_exceptions=True
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Task {i} failed: {result}")
        else:
            print(f"Task {i} succeeded: {result}")

asyncio.run(main())
```

### Try-Except in Async Functions

```python
async def safe_operation(value: int) -> int | None:
    """Safe async operation with error handling."""
    try:
        await asyncio.sleep(0.1)
        if value < 0:
            raise ValueError("Value must be positive")
        return value * 2
    except ValueError as e:
        print(f"Error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
    finally:
        print("Cleanup completed")

async def main():
    """Test error handling."""
    result1 = await safe_operation(5)
    result2 = await safe_operation(-3)
    print(f"Results: {result1}, {result2}")

asyncio.run(main())
```

## Async Patterns Best Practices

1. **Use asyncio.run() for entry point**: Don't manage event loop manually
2. **Create tasks for concurrent work**: Use `asyncio.create_task()`
3. **Use gather for parallel execution**: `await asyncio.gather(*tasks)`
4. **Context managers for resources**: Use async with for cleanup
5. **Timeout long operations**: Use `asyncio.wait_for()`
6. **Handle cancellation**: Catch `asyncio.CancelledError`
7. **Use semaphores for rate limiting**: Control concurrent access
8. **Queue for producer-consumer**: Async-safe message passing
9. **Return exceptions from gather**: `return_exceptions=True` for error handling
10. **Avoid blocking calls**: Use async libraries (aiohttp, aiosqlite)
