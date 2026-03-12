# Comprehensive Docstring Examples

This file contains additional real-world examples for various Python docstring scenarios.

## Table of Contents

1. [Data Processing Functions](#data-processing-functions)
2. [API Integration Functions](#api-integration-functions)
3. [Async Functions](#async-functions)
4. [Decorators](#decorators)
5. [Context Managers](#context-managers)
6. [Type Annotations and Generics](#type-annotations-and-generics)
7. [Error Handling Patterns](#error-handling-patterns)

## Data Processing Functions

### DataFrame Transformation

```python
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
        transactions (pd.DataFrame): Transaction records with columns:
            customer_id, amount, date, product_id.
        customers (pd.DataFrame): Customer records with columns:
            customer_id, name, email, tier.
        on (str, optional): Column name to join on. Defaults to 'customer_id'.
        how (str, optional): Type of join ('left', 'right', 'inner', 'outer').
            Defaults to 'left'.

    Returns:
        pd.DataFrame: Merged dataframe with all transaction columns plus
            customer name, email, and tier. Missing customer data is filled
            with 'Unknown' for tier and empty string for name/email.

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
        items (list[dict]): Items to process, each containing 'id' and 'data'.
        batch_size (int, optional): Number of items per batch. Defaults to 100.
        parallel (bool, optional): Enable parallel processing. Defaults to False.
        num_workers (int, optional): Worker count for parallel mode. Defaults to 4.

    Returns:
        tuple[list[dict], list[Exception]]: A tuple containing:
            - list[dict]: Successfully processed items with added 'status' field
            - list[Exception]: Exceptions encountered during processing

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
def fetch_paginated_results(
    endpoint: str,
    params: dict[str, Any] = None,
    max_pages: int = None,
    rate_limit_delay: float = 0.1
) -> list[dict]:
    """Fetch all pages of results from paginated API endpoint.

    Automatically handles pagination by following 'next' links or
    incrementing page numbers until all results are retrieved or
    max_pages is reached.

    Args:
        endpoint (str): Full URL of the API endpoint.
        params (dict[str, Any], optional): Query parameters for first request.
            Defaults to None.
        max_pages (int, optional): Maximum pages to fetch. None for unlimited.
            Defaults to None.
        rate_limit_delay (float, optional): Seconds to wait between requests.
            Defaults to 0.1.

    Returns:
        list[dict]: Combined results from all pages.

    Raises:
        requests.HTTPError: If any request returns 4xx or 5xx status.
        requests.Timeout: If request exceeds timeout threshold.
        ValueError: If endpoint URL is invalid.

    Examples:
        Fetch all results:
        >>> results = fetch_paginated_results(
        ...     'https://api.example.com/users',
        ...     params={'active': True}
        ... )
        >>> len(results)
        523

        Limit to first 3 pages:
        >>> results = fetch_paginated_results(
        ...     'https://api.example.com/posts',
        ...     max_pages=3
        ... )
        >>> len(results)
        150  # 50 per page * 3 pages

        With rate limiting:
        >>> import time
        >>> start = time.time()
        >>> results = fetch_paginated_results(
        ...     'https://api.example.com/data',
        ...     max_pages=5,
        ...     rate_limit_delay=0.5
        ... )
        >>> elapsed = time.time() - start
        >>> elapsed >= 2.0  # 4 delays between 5 requests
        True

    Note:
        Automatically retries failed requests up to 3 times with exponential backoff.
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
        urls (list[str]): List of URLs to fetch.
        timeout (float, optional): Timeout per request in seconds. Defaults to 10.0.
        max_concurrent (int, optional): Maximum concurrent requests. Defaults to 10.

    Returns:
        dict[str, str | Exception]: Mapping of URL to response text or exception.
            Successful fetches return response text, failures return the exception.

    Examples:
        Basic concurrent fetch:
        >>> urls = [
        ...     'https://example.com/page1',
        ...     'https://example.com/page2',
        ...     'https://example.com/page3'
        ... ]
        >>> results = await fetch_multiple_urls(urls)
        >>> len(results)
        3
        >>> isinstance(results[urls[0]], str)
        True

        With timeout and error handling:
        >>> urls = ['https://example.com', 'https://invalid-url-that-will-fail.xyz']
        >>> results = await fetch_multiple_urls(urls, timeout=5.0)
        >>> isinstance(results[urls[1]], Exception)
        True

        Large batch with concurrency limit:
        >>> urls = [f'https://api.example.com/item/{i}' for i in range(100)]
        >>> results = await fetch_multiple_urls(urls, max_concurrent=5)
        >>> len(results)
        100

    Note:
        Uses aiohttp session with connection pooling for efficiency.
    """
    pass
```

## Decorators

### Retry Decorator

```python
def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator to retry function on failure with exponential backoff.

    Args:
        max_attempts (int, optional): Maximum retry attempts. Defaults to 3.
        delay (float, optional): Initial delay between retries in seconds.
            Defaults to 1.0.
        backoff (float, optional): Multiplier for delay after each retry.
            Defaults to 2.0.
        exceptions (tuple[type[Exception], ...], optional): Exception types
            to catch and retry. Defaults to (Exception,).

    Returns:
        Callable: Decorated function with retry logic.

    Examples:
        Basic retry on any exception:
        >>> @retry(max_attempts=3, delay=0.1)
        ... def unstable_function():
        ...     if random.random() < 0.5:
        ...         raise ValueError("Random failure")
        ...     return "success"
        >>> result = unstable_function()  # Will retry up to 3 times
        >>> result
        'success'

        Retry specific exceptions only:
        >>> @retry(max_attempts=5, delay=0.5, exceptions=(ConnectionError, TimeoutError))
        ... def fetch_data():
        ...     response = requests.get('https://api.example.com/data', timeout=2)
        ...     return response.json()

        With exponential backoff:
        >>> @retry(max_attempts=4, delay=1.0, backoff=2.0)
        ... def api_call():
        ...     # Delays: 1s, 2s, 4s between attempts
        ...     return call_rate_limited_api()

    Note:
        The decorator logs each retry attempt with the exception details.
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
        isolation_level (str, optional): Transaction isolation level.
            Defaults to 'READ COMMITTED'.

    Examples:
        Basic transaction:
        >>> import sqlite3
        >>> conn = sqlite3.connect(':memory:')
        >>> with DatabaseTransaction(conn) as tx:
        ...     tx.connection.execute('CREATE TABLE users (id INTEGER, name TEXT)')
        ...     tx.connection.execute('INSERT INTO users VALUES (1, "Alice")')
        # Transaction auto-commits here

        Automatic rollback on exception:
        >>> try:
        ...     with DatabaseTransaction(conn) as tx:
        ...         tx.connection.execute('INSERT INTO users VALUES (2, "Bob")')
        ...         raise ValueError("Something went wrong")
        ... except ValueError:
        ...     pass
        >>> cursor = conn.execute('SELECT COUNT(*) FROM users')
        >>> cursor.fetchone()[0]
        1  # Bob was not inserted due to rollback

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
        2  # Charlie was inserted, David was not

    Attributes:
        connection: The database connection being managed.
        isolation_level (str): Current isolation level.
    """
    pass
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
        capacity (int): Maximum number of items to cache.
        loader (Callable[[K], V], optional): Function to load values for cache misses.
            Defaults to None.

    Attributes:
        capacity (int): Maximum cache size.
        size (int): Current number of cached items.

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
    pass
```

## Error Handling Patterns

### Custom Exception with Context

```python
class DataValidationError(Exception):
    """Exception raised for data validation failures with detailed context.

    Provides structured information about validation failures including
    the field that failed, the invalid value, and the validation rule.

    Args:
        message (str): Human-readable error message.
        field (str): Name of the field that failed validation.
        value (Any): The invalid value that was provided.
        rule (str): Description of the validation rule that was violated.
        code (str, optional): Machine-readable error code. Defaults to 'VALIDATION_ERROR'.

    Attributes:
        message (str): Error message.
        field (str): Failed field name.
        value (Any): Invalid value.
        rule (str): Violated rule.
        code (str): Error code.

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
        ...     validate_age(-5)
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
def validate_user_input(
    data: dict[str, Any],
    schema: dict[str, dict],
    strict: bool = True
) -> tuple[bool, list[DataValidationError]]:
    """Validate user input against schema with comprehensive error collection.

    Args:
        data (dict[str, Any]): User input data to validate.
        schema (dict[str, dict]): Validation schema where keys are field names
            and values are dicts with 'type', 'required', 'min', 'max', 'pattern', etc.
        strict (bool, optional): If True, reject extra fields not in schema.
            Defaults to True.

    Returns:
        tuple[bool, list[DataValidationError]]: A tuple containing:
            - bool: True if validation passed, False otherwise
            - list[DataValidationError]: List of all validation errors found

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
