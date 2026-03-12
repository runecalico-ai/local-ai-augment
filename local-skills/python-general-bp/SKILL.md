---
name: python-general-bp
description: Expert Python development with modern best practices. Use when writing, reviewing, or refactoring Python code (not specific to testing or documentation). Covers code structure, type hints, error handling, naming conventions, idioms, performance patterns, and Python 3.10+ features. Apply to any .py files except test files.
---

# Python General Best Practices

Expert guidance for writing clean, maintainable, idiomatic Python code using modern Python 3.10+ features and industry best practices.

## When to Use This Skill

- Writing new Python modules, classes, or functions
- Reviewing or refactoring existing Python code
- Implementing type hints and modern Python features
- Optimizing code for readability and performance
- Ensuring code follows PEP 8 and Python idioms
- Converting legacy Python code to modern patterns
- Questions about Python best practices and idioms

## Core Principles

### Modern Python Philosophy

- **Explicit is better than implicit**: Clear, readable code over clever tricks
- **Simple is better than complex**: Straightforward solutions preferred
- **Readability counts**: Code is read more often than written
- **Type hints everywhere**: Improve clarity and catch errors early
- **Fail fast**: Validate early, use specific exceptions, avoid silent failures
- **Pythonic idioms**: Use language features as intended (list comprehensions, context managers, etc.)

### Code Quality Standards

- **PEP 8 compliance**: Follow standard style guide
- **Type hints required**: Use `from __future__ import annotations` for Python 3.10+
- **DRY principle**: Don't repeat yourself
- **SOLID principles**: Single responsibility, dependency injection, etc.
- **Error handling**: Specific exceptions, proper context, useful messages

## Quick Reference

### Type Hints

```python
from __future__ import annotations

from typing import Any, TypeVar
from collections.abc import Callable, Iterable, Sequence

# Basic types
def greet(name: str, age: int) -> str:
    return f"Hello {name}, you are {age}"

# Collections (use collections.abc for Python 3.10+)
def process_items(items: Sequence[str]) -> list[str]:
    return [item.upper() for item in items]

# Optional and Union (use | for Python 3.10+)
def find_user(user_id: int) -> dict[str, Any] | None:
    return {"id": user_id, "name": "John"} if user_id else None

# Callable
def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

# TypeVar for generics
T = TypeVar('T')

def first_item(items: Sequence[T]) -> T | None:
    return items[0] if items else None

# Type aliases for complex types
UserId = int
UserData = dict[str, Any]

def get_user(user_id: UserId) -> UserData | None:
    pass
```

### Error Handling

```python
# Use specific exceptions
def divide(a: float, b: float) -> float:
    """Divide two numbers with validation."""
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise TypeError(f"Expected numeric types, got {type(a)} and {type(b)}")
    if b == 0:
        raise ValueError("Division by zero is not allowed")
    return a / b

# Custom exceptions with context
class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

class DataValidationError(Exception):
    """Raised when data validation fails."""

    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for '{field}': {reason} (got: {value})")

# Exception chaining (preserve context)
def load_config(path: str) -> dict[str, Any]:
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise ConfigurationError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in config: {path}") from e
```

### Context Managers

```python
from contextlib import contextmanager
from pathlib import Path

# Using built-in context managers
def read_file(path: Path) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()

# Multiple context managers
def copy_file(src: Path, dst: Path) -> None:
    with open(src, 'rb') as src_file, open(dst, 'wb') as dst_file:
        dst_file.write(src_file.read())

# Custom context manager
@contextmanager
def temporary_env_var(key: str, value: str):
    """Temporarily set environment variable."""
    import os
    old_value = os.environ.get(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if old_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = old_value

# Usage
with temporary_env_var('DEBUG', 'true'):
    # Code using DEBUG=true
    pass
```

### Pythonic Patterns

```python
# List comprehensions (prefer over map/filter)
squares = [x**2 for x in range(10) if x % 2 == 0]

# Dict comprehensions
word_lengths = {word: len(word) for word in ['hello', 'world']}

# Unpacking
first, *middle, last = [1, 2, 3, 4, 5]

# Walrus operator (Python 3.8+)
if (match := pattern.search(text)) is not None:
    print(match.group(1))

# Match statement (Python 3.10+)
def process_command(command: str, args: list[str]) -> str:
    match command:
        case 'start':
            return "Starting process..."
        case 'stop':
            return "Stopping process..."
        case 'status':
            return f"Status: {args[0]}" if args else "Status: unknown"
        case _:
            return f"Unknown command: {command}"

# Dataclasses (prefer over plain classes for data)
from dataclasses import dataclass, field

@dataclass
class User:
    """User data model."""
    id: int
    name: str
    email: str
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate after initialization."""
        if '@' not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
```

## Code Structure

### Module Organization

```python
"""Module docstring describing purpose and usage.

This module provides utilities for data processing including
validation, transformation, and export functionality.

Example:
    >>> from mypackage import data_utils
    >>> result = data_utils.process_data(raw_data)
"""

# Standard library imports (grouped and sorted)
import json
import sys
from pathlib import Path
from typing import Any

# Third-party imports (grouped and sorted)
import numpy as np
import pandas as pd

# Local application imports
from mypackage.config import settings
from mypackage.models import User

# Module-level constants (UPPER_CASE)
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Module-level type aliases
ConfigDict = dict[str, Any]
```

### Function Design

```python
def process_user_data(
    user_id: int,
    *,  # Force keyword-only arguments after this
    validate: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Process user data with validation and timeout.

    Args:
        user_id: Unique identifier for the user.
        validate: Whether to validate data before processing. Defaults to True.
        timeout: Maximum time in seconds for processing. Defaults to DEFAULT_TIMEOUT.

    Returns:
        Processed user data dictionary containing:
            - 'id': User identifier
            - 'processed_at': Processing timestamp
            - 'status': Processing status

    Raises:
        ValueError: If user_id is negative.
        TimeoutError: If processing exceeds timeout.
        DataValidationError: If validation fails and validate=True.

    Example:
        >>> result = process_user_data(123, validate=True, timeout=60)
        >>> result['status']
        'success'
    """
    if user_id < 0:
        raise ValueError(f"user_id must be positive, got {user_id}")

    # Implementation
    return {"id": user_id, "status": "success"}
```

### Class Design

```python
from abc import ABC, abstractmethod

class DataProcessor(ABC):
    """Abstract base class for data processors.

    Defines interface for processing data from various sources.
    Subclasses must implement process() method.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize processor with configuration.

        Args:
            config: Configuration dictionary with processor settings.
        """
        self._config = config
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration (private method)."""
        required_keys = {'source', 'destination'}
        if not required_keys.issubset(self._config.keys()):
            missing = required_keys - self._config.keys()
            raise ConfigurationError(f"Missing required config keys: {missing}")

    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data (must be implemented by subclasses).

        Args:
            data: Input data to process.

        Returns:
            Processed data.
        """
        pass

    def __repr__(self) -> str:
        """Return string representation."""
        return f"{self.__class__.__name__}(config={self._config})"


class CSVProcessor(DataProcessor):
    """Processor for CSV data."""

    def process(self, data: str) -> list[dict[str, Any]]:
        """Process CSV data into list of dictionaries."""
        # Implementation
        return []
```

## Naming Conventions

### Standards

- **Modules/packages**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase`
- **Functions/methods**: `lowercase_with_underscores()`
- **Constants**: `UPPER_CASE_WITH_UNDERSCORES`
- **Private attributes**: `_single_leading_underscore`
- **Name mangling**: `__double_leading_underscore` (rare)
- **Variables**: `lowercase_with_underscores`

### Good Names

```python
# Clear, descriptive names
def calculate_monthly_revenue(transactions: list[Transaction]) -> Decimal:
    pass

# Avoid abbreviations unless very common
user_count = 10  # Good
usr_cnt = 10     # Bad

# Use verbs for functions
def validate_email(email: str) -> bool:
    pass

# Use nouns for classes
class UserRepository:
    pass

# Boolean variables with is/has/can prefix
is_valid = True
has_permission = False
can_edit = True
```

## Performance and Optimization

### Common Patterns

```python
# Use generators for large datasets
def read_large_file(path: Path) -> Iterable[str]:
    """Read file line by line (memory efficient)."""
    with open(path) as f:
        for line in f:
            yield line.strip()

# Lazy evaluation
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(n: int) -> int:
    """Cache results of expensive calculation."""
    return sum(range(n))

# Use slots for memory efficiency in classes with many instances
class Point:
    """Memory-efficient point class."""
    __slots__ = ('x', 'y')

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

# Avoid premature optimization
# 1. Write clear, correct code first
# 2. Profile to find bottlenecks
# 3. Optimize only where needed
```

### String Operations

```python
# Use f-strings (Python 3.6+)
name, age = "Alice", 30
message = f"{name} is {age} years old"  # Good
message = name + " is " + str(age) + " years old"  # Bad

# Join for building strings from sequences
words = ['hello', 'world', 'python']
sentence = ' '.join(words)  # Good
sentence = ''
for word in words:
    sentence += word + ' '  # Bad (slow for large lists)

# Use raw strings for regex
import re
pattern = r'\d{3}-\d{3}-\d{4}'  # Good
pattern = '\\d{3}-\\d{3}-\\d{4}'  # Bad (harder to read)
```

## Testing and Validation

### Input Validation

```python
def process_age(age: int) -> str:
    """Process age with validation.

    Args:
        age: Person's age in years.

    Returns:
        Age category string.

    Raises:
        TypeError: If age is not an integer.
        ValueError: If age is negative or unrealistic.
    """
    if not isinstance(age, int):
        raise TypeError(f"Age must be integer, got {type(age).__name__}")
    if age < 0:
        raise ValueError(f"Age cannot be negative, got {age}")
    if age > 150:
        raise ValueError(f"Age unrealistic, got {age}")

    if age < 18:
        return "minor"
    elif age < 65:
        return "adult"
    else:
        return "senior"
```

### Assertions for Debugging

```python
def calculate_average(numbers: list[float]) -> float:
    """Calculate average of numbers.

    Args:
        numbers: List of numbers to average.

    Returns:
        Average value.

    Raises:
        ValueError: If numbers list is empty.
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")

    result = sum(numbers) / len(numbers)

    # Assertions for debugging (removed in optimized mode with -O flag)
    assert isinstance(result, float), "Result should be float"
    assert not (numbers and result > max(numbers)), "Average shouldn't exceed max"

    return result
```

## Advanced Patterns

### Dependency Injection

```python
from typing import Protocol

# Define interface using Protocol
class Logger(Protocol):
    """Logger protocol for dependency injection."""

    def log(self, message: str) -> None:
        """Log a message."""
        ...

# Accept interface, not concrete implementation
class UserService:
    """User service with injected logger."""

    def __init__(self, logger: Logger) -> None:
        self._logger = logger

    def create_user(self, name: str) -> User:
        """Create user with logging."""
        self._logger.log(f"Creating user: {name}")
        # Create user logic
        return User(id=1, name=name, email=f"{name}@example.com")
```

### Factory Pattern

```python
from typing import Literal

ProcessorType = Literal['csv', 'json', 'xml']

def create_processor(processor_type: ProcessorType) -> DataProcessor:
    """Factory function to create processors.

    Args:
        processor_type: Type of processor to create.

    Returns:
        Appropriate processor instance.

    Raises:
        ValueError: If processor_type is unknown.
    """
    processors = {
        'csv': CSVProcessor,
        'json': JSONProcessor,
        'xml': XMLProcessor,
    }

    processor_class = processors.get(processor_type)
    if processor_class is None:
        raise ValueError(f"Unknown processor type: {processor_type}")

    return processor_class(config={})
```

## Common Pitfalls

### Mutable Default Arguments

```python
# DON'T: Mutable default arguments
def add_item(item: str, items: list[str] = []) -> list[str]:  # Bad!
    items.append(item)
    return items

# DO: Use None and create new list
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items

# OR: Use dataclass with field
from dataclasses import dataclass, field

@dataclass
class Container:
    items: list[str] = field(default_factory=list)
```

### Exception Handling

```python
# DON'T: Bare except
try:
    risky_operation()
except:  # Bad! Catches everything including KeyboardInterrupt
    pass

# DO: Catch specific exceptions
try:
    risky_operation()
except (ValueError, KeyError) as e:
    logger.error(f"Operation failed: {e}")
    raise

# DON'T: Silent failures
try:
    result = risky_operation()
except Exception:
    pass  # Bad! Error is hidden

# DO: Log and re-raise or handle properly
try:
    result = risky_operation()
except Exception as e:
    logger.exception("Risky operation failed")
    raise
```

### Resource Management

```python
# DON'T: Manual resource management
file = open('data.txt')
try:
    data = file.read()
finally:
    file.close()

# DO: Use context managers
with open('data.txt') as file:
    data = file.read()
```

## Code Review Checklist

When reviewing Python code, check for:

1. **Type hints**: All functions have complete type annotations
2. **Docstrings**: All public functions, classes, modules documented
3. **Error handling**: Specific exceptions, proper error messages
4. **Naming**: Follows PEP 8 conventions
5. **Imports**: Organized (stdlib, third-party, local) and sorted
6. **Context managers**: Used for resources (files, locks, connections)
7. **Pythonic idioms**: List comprehensions, unpacking, etc.
8. **No mutable defaults**: Check function signatures
9. **DRY principle**: No code duplication
10. **Single responsibility**: Functions and classes do one thing well

## References

For detailed examples and advanced patterns, see:

- [code-organization.md](references/code-organization.md) - Project structure and module design
- [type-hints-advanced.md](references/type-hints-advanced.md) - Complex type annotations and generics
- [performance-optimization.md](references/performance-optimization.md) - Profiling and optimization techniques
- [async-patterns.md](references/async-patterns.md) - Asyncio and concurrent programming
