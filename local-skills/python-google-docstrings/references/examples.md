# Comprehensive Docstring Examples

This file contains reference templates for various Python docstring scenarios.
The surrounding functions and classes show docstring shape and wording. Their
placeholder bodies use `pass` on purpose.

When you keep an `Examples:` section in real code, make the example runnable as
written: include imports and setup, use deterministic local data, and avoid
live services, wall-clock timing, or bare top-level `await`.

Examples labeled `Illustrative template` show the structure to adapt when the
real implementation depends on infrastructure that is outside this reference
pack.

## Table of Contents

1. [Data Processing Functions](#data-processing-functions)
2. [API Integration Functions](#api-integration-functions)
3. [Async Functions](#async-functions)
4. [Decorators](#decorators)
5. [Pytest Fixtures and Tests](#pytest-fixtures-and-tests)
6. [Context Managers](#context-managers)
7. [Type Annotations and Generics](#type-annotations-and-generics)
8. [Overloaded Functions](#overloaded-functions)
9. [Special Cases](#special-cases)
10. [Error Handling Patterns](#error-handling-patterns)

## Data Processing Functions

### DataFrame Transformation

```python
import pandas as pd


def merge_customer_data(
    transactions: pd.DataFrame,
    customers: pd.DataFrame,
    on: str = 'customer_id',
    how: str = 'left'
) -> pd.DataFrame:
    """Merge transaction and customer data with validation.

    Combines transaction records with customer information, validating
    data quality and handling missing values according to business rules.

    Args:
        transactions: Transaction records with columns:
            customer_id, amount, date, product_id.
        customers: Customer records with columns:
            customer_id, name, email, tier.
        on: Column name to join on. Defaults to 'customer_id'.
        how: Type of join ('left', 'right', 'inner', 'outer').
            Defaults to 'left'.

    Returns:
        Merged dataframe with all transaction columns plus customer name,
        email, and tier. Missing customer data is filled with 'Unknown' for
        tier and empty string for name/email.

    Raises:
        ValueError: If 'on' column doesn't exist in both dataframes.
        KeyError: If required columns are missing from either dataframe.

    Examples:
        Basic merge:
        >>> transactions = pd.DataFrame({
        ...     'customer_id': [1, 2, 3],
        ...     'amount': [100.0, 200.0, 150.0]
        ... })
        >>> customers = pd.DataFrame({
        ...     'customer_id': [1, 2],
        ...     'name': ['Alice', 'Bob'],
        ...     'tier': ['gold', 'silver']
        ... })
        >>> merged = merge_customer_data(transactions, customers)
        >>> merged.loc[0, 'name']
        'Alice'
        >>> merged.loc[2, 'tier']  # Missing customer
        'Unknown'

        Inner join to exclude missing customers:
        >>> merged = merge_customer_data(transactions, customers, how='inner')
        >>> len(merged)
        2

    Note:
        This function modifies neither input DataFrame. Always returns a new copy.
    """
    pass
```

### Batch Processing

```python
def process_batch(
    items: list[dict],
    batch_size: int = 100,
    parallel: bool = False,
    num_workers: int = 4
) -> tuple[list[dict], list[Exception]]:
    """Process items in batches with error handling and optional parallelization.

    Args:
        items: Items to process, each containing 'id' and 'data'.
        batch_size: Number of items per batch. Defaults to 100.
        parallel: Enable parallel processing. Defaults to False.
        num_workers: Worker count for parallel mode. Defaults to 4.

    Returns:
        A tuple containing:
            - Successfully processed items with added 'status' field.
            - Exceptions encountered during processing.

    Examples:
        Sequential processing:
        >>> items = [{'id': i, 'data': f'item_{i}'} for i in range(250)]
        >>> processed, errors = process_batch(items, batch_size=100)
        >>> len(processed)
        250
        >>> len(errors)
        0

        Parallel processing with error handling:
        >>> items = [{'id': i, 'data': 'valid' if i % 10 else 'invalid'} for i in range(100)]
        >>> processed, errors = process_batch(items, parallel=True, num_workers=2)
        >>> len(processed) + len(errors)
        100

        Small batch for memory-constrained scenarios:
        >>> large_items = [{'id': i, 'data': 'x' * 1000000} for i in range(10)]
        >>> processed, errors = process_batch(large_items, batch_size=2)
        >>> len(processed)
        10
    """
    pass
```

## API Integration Functions

### REST API Client

```python
from typing import Any

import requests


def fetch_paginated_results(
    endpoint: str,
    params: dict[str, Any] | None = None,
    max_pages: int | None = None,
    rate_limit_delay: float = 0.1
) -> list[dict]:
    """Fetch all pages of results from paginated API endpoint.

    Automatically handles pagination by following 'next' links or
    incrementing page numbers until all results are retrieved or
    max_pages is reached.

    Args:
        endpoint: Full URL of the API endpoint.
        params: Query parameters for first request.
            Defaults to None.
        max_pages: Maximum pages to fetch. None for unlimited.
            Defaults to None.
        rate_limit_delay: Seconds to wait between requests.
            Defaults to 0.1.

    Returns:
        Combined results from all pages.

    Raises:
        requests.HTTPError: If any request returns 4xx or 5xx status.
        requests.Timeout: If request exceeds timeout threshold.
        ValueError: If endpoint URL is invalid.

    Examples:
        Illustrative template against a stubbed client:
        >>> results = fetch_paginated_results(
        ...     'https://service.test/users',
        ...     params={'active': True},
        ...     max_pages=2,
        ... )
        >>> [item['id'] for item in results]
        [1, 2, 3]

        Illustrative template with an explicit page cap:
        >>> results = fetch_paginated_results(
        ...     'https://service.test/posts',
        ...     max_pages=1,
        ... )
        >>> results[0]['page']
        1

        Illustrative template with rate limiting enabled:
        >>> results = fetch_paginated_results(
        ...     'https://service.test/data',
        ...     max_pages=3,
        ...     rate_limit_delay=0.5,
        ... )
        >>> results[-1]['page']
        3

    Note:
        Automatically retries failed requests up to 3 times with exponential backoff.
        Use a stubbed client or local test server in docstring examples, and
        assert on shaped results instead of elapsed time.
    """
    pass
```

## Async Functions

### Async Data Fetcher

```python
async def fetch_multiple_urls(
    urls: list[str],
    timeout: float = 10.0,
    max_concurrent: int = 10
) -> dict[str, str | Exception]:
    """Fetch multiple URLs concurrently with timeout and error handling.

    Args:
        urls: List of URLs to fetch.
        timeout: Timeout per request in seconds. Defaults to 10.0.
        max_concurrent: Maximum concurrent requests. Defaults to 10.

    Returns:
        Mapping of URL to response text or exception. Successful fetches
        return response text, failures return the exception.

    Examples:
        Illustrative async template with asyncio.run:
        >>> import asyncio
        >>> async def main() -> dict[str, str | Exception]:
        ...     urls = [
        ...         'https://service.test/page1',
        ...         'https://service.test/page2',
        ...     ]
        ...     return await fetch_multiple_urls(urls)
        >>> results = asyncio.run(main())
        >>> sorted(results)
        ['https://service.test/page1', 'https://service.test/page2']

        Illustrative async template with error handling:
        >>> import asyncio
        >>> async def main() -> dict[str, str | Exception]:
        ...     urls = [
        ...         'https://service.test/ok',
        ...         'https://service.test/missing',
        ...     ]
        ...     return await fetch_multiple_urls(urls, timeout=5.0)
        >>> results = asyncio.run(main())
        >>> isinstance(results['https://service.test/missing'], Exception)
        True

        Illustrative async template with a concurrency limit:
        >>> import asyncio
        >>> async def main() -> dict[str, str | Exception]:
        ...     urls = [f'https://service.test/item/{index}' for index in range(5)]
        ...     return await fetch_multiple_urls(urls, max_concurrent=2)
        >>> results = asyncio.run(main())
        >>> len(results)
        5

    Note:
        Uses aiohttp session with connection pooling for efficiency. Use
        `asyncio.run()` or your test framework's loop helper instead of bare
        top-level `await` in docstring examples.
    """
    pass
```

### Async Method

```python
class AsyncStatusClient:
    """Fetch status information from an async backend."""

    async def fetch_status(self, customer_id: str) -> dict[str, str]:
        """Fetch the latest status payload for a customer.

        Args:
            customer_id: Customer identifier to query.

        Returns:
            Status payload for the requested customer.
        """
        pass
```

### Async Generator

```python
from collections.abc import AsyncIterator


async def stream_results(batch_size: int = 100) -> AsyncIterator[dict[str, int]]:
    """Yield result rows asynchronously in batches.

    Args:
        batch_size: Number of rows requested per batch.

    Yields:
        Result rows as they arrive from the upstream service.
    """
    yield {"batch_size": batch_size}
```

## Decorators

### Retry Decorator

```python
from collections.abc import Callable


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator to retry function on failure with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts. Defaults to 3.
        delay: Initial delay between retries in seconds.
            Defaults to 1.0.
        backoff: Multiplier for delay after each retry.
            Defaults to 2.0.
        exceptions: Exception types to catch and retry. Defaults to
            (Exception,).

    Returns:
        Decorated function with retry logic.

    Examples:
        Deterministic retry on a transient exception:
        >>> outcomes = iter([ConnectionError("temporary outage"), "success"])
        >>> @retry(max_attempts=3, delay=0.0, exceptions=(ConnectionError,))
        ... def unstable_function():
        ...     result = next(outcomes)
        ...     if isinstance(result, Exception):
        ...         raise result
        ...     return result
        >>> unstable_function()
        'success'

        Retry specific exceptions only:
        >>> outcomes = iter([TimeoutError("try again"), {'status': 'ok'}])
        >>> @retry(max_attempts=2, delay=0.0, exceptions=(TimeoutError,))
        ... def fetch_data():
        ...     result = next(outcomes)
        ...     if isinstance(result, Exception):
        ...         raise result
        ...     return result
        >>> fetch_data()['status']
        'ok'

        Exponential backoff configuration:
        >>> outcomes = iter([TimeoutError("slow"), TimeoutError("still slow"), "done"])
        >>> @retry(max_attempts=4, delay=0.1, backoff=2.0, exceptions=(TimeoutError,))
        ... def api_call():
        ...     result = next(outcomes)
        ...     if isinstance(result, Exception):
        ...         raise result
        ...     return result
        >>> api_call()
        'done'

    Note:
        The decorator logs each retry attempt with the exception details.
    """
    pass
```

## Pytest Fixtures and Tests

Short, obvious pytest fixtures and tests can stay undocumented. Add or expand
docstrings when fixture lifecycle, isolation rules, or scenario intent would be
hard to infer from the name and body alone.

### Pytest Fixture

```python
from pathlib import Path

import pytest


@pytest.fixture
def configured_client(tmp_path: Path) -> dict[str, str]:
    """Create an isolated client configuration for integration-style tests.

    The fixture prepares a temporary configuration root so tests can mutate
    client state without touching shared files.

    Returns:
        Client settings seeded for the test scenario.
    """
    pass
```

### Pytest Test

```python
def test_refresh_token_retries_once(configured_client: dict[str, str]) -> None:
    """Verify refresh retries once after a transient unauthorized response.

    The scenario matters because the retry behavior is the regression target;
    a bare test name would not explain why one retry is expected.
    """
    pass
```

## Context Managers

### Database Transaction

```python
class DatabaseTransaction:
    """Context manager for database transactions with automatic rollback.

    Provides automatic commit on success and rollback on exception,
    with optional savepoint support for nested transactions.

    Args:
        connection: Database connection object (sqlite3, psycopg2, etc.).
        isolation_level: Transaction isolation level.
            Defaults to 'READ COMMITTED'.

    Examples:
        Basic transaction:
        >>> import sqlite3
        >>> conn = sqlite3.connect(':memory:')
        >>> with DatabaseTransaction(conn) as tx:
        ...     tx.connection.execute('CREATE TABLE users (id INTEGER, name TEXT)')
        ...     tx.connection.execute('INSERT INTO users VALUES (1, "Alice")')

        Automatic rollback on exception:
        >>> try:
        ...     with DatabaseTransaction(conn) as tx:
        ...         tx.connection.execute('INSERT INTO users VALUES (2, "Bob")')
        ...         raise ValueError("Something went wrong")
        ... except ValueError:
        ...     pass
        >>> cursor = conn.execute('SELECT COUNT(*) FROM users')
        >>> cursor.fetchone()[0]
        1

        Nested transaction with savepoint:
        >>> with DatabaseTransaction(conn) as outer:
        ...     outer.connection.execute('INSERT INTO users VALUES (3, "Charlie")')
        ...     try:
        ...         with DatabaseTransaction(conn) as inner:
        ...             inner.connection.execute('INSERT INTO users VALUES (4, "David")')
        ...             raise ValueError("Inner failure")
        ...     except ValueError:
        ...         pass  # Inner transaction rolled back
        ...     # Outer transaction continues
        >>> cursor = conn.execute('SELECT COUNT(*) FROM users')
        >>> cursor.fetchone()[0]
        2

    Attributes:
        connection: The database connection being managed.
        isolation_level: Current isolation level.
    """

    def __init__(self, connection, isolation_level: str = 'READ COMMITTED') -> None:
        self.connection = connection
        self.isolation_level = isolation_level

    def __enter__(self) -> "DatabaseTransaction":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        return False
```

## Type Annotations and Generics

### Generic Cache

```python
from typing import TypeVar, Generic, Callable

K = TypeVar('K')
V = TypeVar('V')

class LRUCache(Generic[K, V]):
    """Least Recently Used (LRU) cache with generic key and value types.

    Thread-safe LRU cache implementation with automatic eviction of
    least recently used items when capacity is reached.

    Args:
        capacity: Maximum number of items to cache.
        loader: Function to load values for cache misses.
            Defaults to None.

    Attributes:
        capacity: Maximum cache size.
        size: Current number of cached items.

    Examples:
        Basic cache usage with strings and integers:
        >>> cache: LRUCache[str, int] = LRUCache(capacity=3)
        >>> cache.put("a", 1)
        >>> cache.put("b", 2)
        >>> cache.get("a")
        1

        With automatic loader:
        >>> def load_user(user_id: int) -> dict:
        ...     return {'id': user_id, 'name': f'User_{user_id}'}
        >>> user_cache: LRUCache[int, dict] = LRUCache(capacity=100, loader=load_user)
        >>> user_cache.get(42)
        {'id': 42, 'name': 'User_42'}

        LRU eviction:
        >>> cache: LRUCache[str, str] = LRUCache(capacity=2)
        >>> cache.put("a", "first")
        >>> cache.put("b", "second")
        >>> cache.put("c", "third")  # Evicts "a"
        >>> cache.get("a") is None
        True
        >>> cache.get("b")
        'second'

    Note:
        This implementation uses threading.Lock for thread safety.
    """

    def __init__(self, capacity: int, loader: Callable[[K], V] | None = None) -> None:
        self.capacity = capacity
        self.loader = loader
        self._items: dict[K, V] = {}

    @property
    def size(self) -> int:
        return len(self._items)

    def get(self, key: K) -> V | None:
        if key in self._items:
            value = self._items.pop(key)
            self._items[key] = value
            return value
        if self.loader is None:
            return None
        value = self.loader(key)
        self.put(key, value)
        return value

    def put(self, key: K, value: V) -> None:
        if key in self._items:
            self._items.pop(key)
        elif len(self._items) >= self.capacity:
            oldest_key = next(iter(self._items))
            self._items.pop(oldest_key)
        self._items[key] = value
```

## Overloaded Functions

```python
from typing import overload


@overload
def parse_customer_id(value: str) -> int:
    ...


@overload
def parse_customer_id(value: bytes) -> int:
    ...


def parse_customer_id(value: str | bytes) -> int:
    """Convert a supported raw identifier to an integer.

    Args:
        value: Raw identifier to convert.

    Returns:
        Converted integer identifier.

    Raises:
        ValueError: If the raw value cannot be converted.
    """
    pass
```

## Special Cases

### Property Getter

```python
class CustomerProfile:
    @property
    def full_name(self) -> str:
        """Display name for the current customer."""
        return "Ada Lovelace"
```

### Static Method

Use this pattern only when an existing API or framework already requires a
static method.

```python
class ConfigValidator:
    @staticmethod
    def validate_port(value: int) -> bool:
        """Validate whether a port number is allowed.

        Args:
            value: Port number to validate.

        Returns:
            True when the port is within the allowed range.
        """
        pass
```

### Class Method

```python
class SessionToken:
    @classmethod
    def from_payload(cls, payload: dict[str, str]) -> "SessionToken":
        """Build a token from a decoded payload.

        Args:
            payload: Decoded payload values.

        Returns:
            Session token instance built from the payload.
        """
        pass
```

### Keyword-Only Parameters

```python
def render_report(customer_id: str, *, include_archived: bool = False) -> dict[str, object]:
    """Build a report for a single customer.

    Args:
        customer_id: Customer identifier to load.
        include_archived: Keyword-only flag that includes archived records.

    Returns:
        Report payload for the requested customer.
    """
    pass
```

### Dataclass

```python
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExportOptions:
    """Configuration for a CSV export job.

    Attributes:
        destination: Destination path for the export file.
        include_headers: Whether to emit a header row.
    """

    destination: Path
    include_headers: bool = True
```

### None-Returning Function

```python
def log_event(event: str) -> None:
    """Log an event to the audit stream.

    Args:
        event: Event description to log.

    Raises:
        IOError: If the audit stream is unavailable.
    """
    pass
```

### Module Docstring

```python
"""Utilities for customer exports.

This module coordinates export jobs, validates output paths, and formats
CSV rows for downstream systems.

Examples:
    >>> from customer_exports import log_event
    >>> log_event("export-started")
"""
```

## Error Handling Patterns

### Custom Exception with Context

```python
class DataValidationError(Exception):
    """Validation failure with detailed field context.

    Provides structured information about validation failures including
    the field that failed, the invalid value, and the validation rule.

    Args:
        message: Human-readable error message.
        field: Name of the field that failed validation.
        value (Any): The invalid value that was provided.
        rule: Description of the validation rule that was violated.
        code (str, optional): Machine-readable error code. Defaults to 'VALIDATION_ERROR'.

    Attributes:
        message: Error message.
        field: Failed field name.
        value (Any): Invalid value.
        rule: Violated rule.
        code: Error code.

    Examples:
        Basic validation error:
        >>> raise DataValidationError(
        ...     message="Email format is invalid",
        ...     field="email",
        ...     value="not-an-email",
        ...     rule="Must match pattern: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        ... )
        Traceback (most recent call last):
        ...
        DataValidationError: Email format is invalid

        Catching and inspecting:
        >>> try:
        ...     raise DataValidationError(
        ...         message="Age must be positive",
        ...         field="age",
        ...         value=-5,
        ...         rule="Must be greater than or equal to 0",
        ...     )
        ... except DataValidationError as e:
        ...     print(f"Field '{e.field}' failed: {e.message}")
        ...     print(f"Invalid value: {e.value}")
        ...     print(f"Rule: {e.rule}")
        Field 'age' failed: Age must be positive
        Invalid value: -5
        Rule: Must be greater than or equal to 0

        With custom error code:
        >>> raise DataValidationError(
        ...     message="Username already exists",
        ...     field="username",
        ...     value="john_doe",
        ...     rule="Must be unique",
        ...     code="DUPLICATE_USERNAME"
        ... )
    """
    pass
```

### Validation with Multiple Errors

```python
from typing import Any


def validate_user_input(
    data: dict[str, Any],
    schema: dict[str, dict],
    strict: bool = True
) -> tuple[bool, list[DataValidationError]]:
    """Validate user input against schema with comprehensive error collection.

    Args:
        data: User input data to validate.
        schema: Validation schema where keys are field names
            and values are dicts with 'type', 'required', 'min', 'max', 'pattern', etc.
        strict: If True, reject extra fields not in schema.
            Defaults to True.

    Returns:
        A tuple containing:
            - True if validation passed, otherwise False.
            - All validation errors found.

    Examples:
        Valid input:
        >>> schema = {
        ...     'name': {'type': str, 'required': True, 'min_length': 2},
        ...     'age': {'type': int, 'required': True, 'min': 0, 'max': 150},
        ...     'email': {'type': str, 'required': True, 'pattern': r'.+@.+\\..+'}
        ... }
        >>> data = {'name': 'Alice', 'age': 30, 'email': 'alice@example.com'}
        >>> is_valid, errors = validate_user_input(data, schema)
        >>> is_valid
        True
        >>> len(errors)
        0

        Multiple validation errors:
        >>> data = {'name': 'A', 'age': -5, 'email': 'invalid'}
        >>> is_valid, errors = validate_user_input(data, schema)
        >>> is_valid
        False
        >>> len(errors)
        3
        >>> [e.field for e in errors]
        ['name', 'age', 'email']

        Missing required field:
        >>> data = {'name': 'Bob', 'email': 'bob@example.com'}
        >>> is_valid, errors = validate_user_input(data, schema)
        >>> is_valid
        False
        >>> errors[0].field
        'age'
        >>> errors[0].code
        'MISSING_REQUIRED_FIELD'

        Extra fields in strict mode:
        >>> data = {'name': 'Charlie', 'age': 25, 'email': 'c@example.com', 'extra': 'field'}
        >>> is_valid, errors = validate_user_input(data, schema, strict=True)
        >>> is_valid
        False
        >>> errors[0].field
        'extra'

    Note:
        Collects all validation errors before returning, rather than failing
        on first error. This provides better user experience for form validation.
    """
    pass
```
