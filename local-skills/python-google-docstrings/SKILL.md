---
name: python-google-docstrings
description: Use when writing or reviewing Google-style Python docstrings for modules, public or non-obvious callables, pytest fixtures/tests, property, dataclass, overload, and override edge cases, and signature/docstring synchronization audits.
---

# Python Google Docstrings

Expert guidance for writing practical Python docstrings that align with the current Google Python Style Guide.

## When to Use This Skill

- Writing docstrings for Python functions, methods, classes, or modules
- Reviewing or refactoring existing docstrings for consistency
- Documenting pytest fixtures and tests when lifecycle or scenario intent is not obvious
- Running or interpreting signature/docstring synchronization audits
- Handling properties, overloads, and similar edge cases
- Adding examples where a concrete call improves clarity
- Ensuring proper formatting and completeness of documentation
- Converting other docstring formats to Google Style

## Core Principles

### Google Style Format

Google Style docstrings use section headers followed by indented content. Each section is separated by a blank line.

### Common Sections

1. **Summary Line** - One physical line, 80 characters or fewer, ending with `.` `?` or `!`
2. **Extended Description** (optional) - Additional details, separated by blank line
3. **Args** - Parameters that need explanation
4. **Returns** or **Yields** - Semantics the summary line and annotations do not already make clear; for in-scope non-None callables, use either an explicit section or a summary line that clearly starts with `Return` / `Returns` or `Yield` / `Yields`
5. **Raises** - Exceptions relevant to the interface
6. **Examples** (optional) - Add when a concrete call or output makes usage clearer
7. **Note** (optional) - Additional notes
8. **See Also** (optional) - Related functions/classes
9. **References** (optional) - External references

Use only the sections the reader needs. A one-line docstring is fine when the
callable is simple, returns `None`, or is otherwise out of scope for richer
sections under this skill.
The bundled audits are conservative about `Raises:`: they catch missing
documentation for explicit raise paths, but propagated or stale exception notes
still require manual review.

### Key Formatting Rules

- Use triple double-quotes `"""`
- First line is a brief summary; descriptive or imperative style is fine if it
    is consistent within a file
- Keep the summary line within 80 characters
- In `Args`, `Returns`, and `Yields`, include type text when annotations do not
    already communicate it
- When a keyword-only calling constraint matters to readers, mention it in the
    `Args` description
- Use consistent section indentation; 4 spaces is the bundle default
- If you include interactive examples, use `>>>`

The templates below show fuller patterns than every production docstring needs.
Omit sections that do not add value.

## Function Docstrings

### Basic Function Template

```python
def function_name(arg1: str, arg2: int, optional_arg: bool = False) -> dict:
    """Brief summary of what the function does.

    More detailed explanation of the function's purpose and behavior.
    This can span multiple lines and paragraphs if needed.

    Args:
        arg1: Description of the first argument.
        arg2: Description of the second argument.
        optional_arg: Description of optional argument.
            Defaults to False.

    Returns:
        Description of the return value. Include structure if complex, e.g.,
        {'key1': value1_description, 'key2': value2_description}.

    Raises:
        LookupError: If the requested record cannot be found.
        RuntimeError: If the backend rejects the update after validation.

    Examples:
        Basic usage:
        >>> result = function_name("hello", 42)
        >>> print(result['status'])
        'success'

        With optional argument:
        >>> result = function_name("world", 10, optional_arg=True)
        >>> result['count']
        10

    Note:
        Any additional information, caveats, or important details.
    """
    pass
```

### Complex Return Types

```python
def fetch_user_data(user_id: int) -> dict[str, Any]:
    """Retrieve comprehensive user information from database.

    Args:
        user_id: Unique identifier for the user.

    Returns:
        User data dictionary with the following structure:
            - 'id' (int): User identifier
            - 'name' (str): Full name
            - 'email' (str): Email address
            - 'created_at' (datetime): Account creation timestamp
            - 'metadata' (dict): Additional user metadata

    Raises:
        UserNotFoundError: If user_id does not exist.
        DatabaseConnectionError: If database is unreachable.

    Examples:
        >>> user = fetch_user_data(12345)
        >>> user['name']
        'John Doe'
        >>> user['metadata']['role']
        'admin'
    """
    pass
```

## Class Docstrings

### Class with Methods

```python
class DataProcessor:
    """Process and transform data from various sources.

    This class provides methods for loading, cleaning, and transforming
    data from CSV, JSON, and database sources. It maintains internal
    state for caching and optimization.

    Args:
        cache_size: Maximum number of cached items.
            Defaults to 100.
        strict_mode: Enable strict validation.
            Defaults to True.

    Attributes:
        cache_size (int): Current cache size limit.
        strict_mode (bool): Whether strict mode is enabled.
        processed_count (int): Number of items processed.

    Examples:
        Basic initialization and usage:
        >>> processor = DataProcessor(cache_size=50)
        >>> processor.load_csv('data.csv')
        >>> processor.processed_count
        150

        With strict mode disabled:
        >>> processor = DataProcessor(strict_mode=False)
        >>> processor.transform(data, allow_nulls=True)

    Note:
        Cache is cleared automatically when size limit is reached.
    """

    def __init__(self, cache_size: int = 100, strict_mode: bool = True):
        self.cache_size = cache_size
        self.strict_mode = strict_mode
        self.processed_count = 0

    def load_csv(self, filepath: str, delimiter: str = ',') -> pd.DataFrame:
        """Load data from CSV file into DataFrame.

        Args:
            filepath: Path to the CSV file.
            delimiter: Field delimiter character.
                Defaults to ','.

        Returns:
            Loaded data with inferred column types.

        Raises:
            FileNotFoundError: If filepath does not exist.
            ValueError: If CSV format is invalid.

        Examples:
            Load standard CSV:
            >>> df = processor.load_csv('data.csv')
            >>> len(df)
            1000

            Load with custom delimiter:
            >>> df = processor.load_csv('data.tsv', delimiter='\\t')
        """
        pass
```

## Generator Functions

```python
def read_large_file(filepath: str, chunk_size: int = 1024) -> Generator[str, None, None]:
    """Read large file in chunks to avoid memory issues.

    Args:
        filepath: Path to file to read.
        chunk_size: Number of bytes per chunk.
            Defaults to 1024.

    Yields:
        Next chunk of file content.

    Raises:
        FileNotFoundError: If filepath does not exist.
        PermissionError: If file cannot be read.

    Examples:
        Process file in chunks:
        >>> for chunk in read_large_file('huge_file.txt'):
        ...     process_chunk(chunk)

        With custom chunk size:
        >>> chunks = list(read_large_file('data.bin', chunk_size=4096))
        >>> len(chunks)
        250
    """
    yield ""
```

## Module Docstrings

Place at the top of the file:

```python
"""Utilities for data validation and transformation.

This module provides functions and classes for validating user input,
transforming data formats, and applying business rules. It is designed
to work with pandas DataFrames and native Python data structures.

The module includes:
    - Input validators (validate_email, validate_phone, etc.)
    - Data transformers (normalize_text, convert_units, etc.)
    - Custom validation rules framework

Examples:
    Import and use validators:
    >>> from validation_utils import validate_email
    >>> validate_email('user@example.com')
    True

    Use data transformers:
    >>> from validation_utils import normalize_text
    >>> normalize_text('  Hello World  ')
    'hello world'

Note:
    This module requires pandas >= 1.5.0 for DataFrame operations.
"""
```

## Special Cases

### Property Docstrings

Document `@property` and `@cached_property` docstrings like attributes, not
zero-argument methods.
Use a short descriptive summary of what the property represents. Omit `Args:`
and do not add `Returns:` by default. If a specific codebase has an
established local convention for richer property docstrings, treat that as an
optional exception rather than the default. This default guidance applies to
getter-like property APIs. The bundled helpers always treat property setters
and deleters as out of scope. If a local codebase documents them as part of
the public contract, review them manually rather than relying on helper output.
The helpers also do not treat an existing `Returns:` block on a property as
drift by itself, because some codebases intentionally keep richer
property-style docs.

```python
@property
def full_name(self) -> str:
    """User's full name in "First Last" format."""
    return f"{self.first_name} {self.last_name}"
```

### Overloaded Functions

Skip docstrings on `@overload` stubs. Document only the concrete
implementation that carries the real body.

```python
from typing import overload


@overload
def coerce_id(value: str) -> int:
    ...


@overload
def coerce_id(value: bytes) -> int:
    ...


def coerce_id(value: str | bytes) -> int:
    """Convert a supported raw value to an integer identifier.

    Args:
        value: Raw identifier value to convert.

    Returns:
        Converted integer identifier.
    """
    return len(value)
```

### Dataclasses

Document dataclass fields in the class docstring rather than inventing
docstrings for generated methods. Prefer `Attributes:` for stored state and use
`Args:` only when constructor-specific semantics need explanation.

```python
from dataclasses import dataclass


@dataclass
class SyncRequest:
    """Request payload for a sync operation.

    Attributes:
        customer_id: Customer identifier to synchronize.
        enabled: Whether the sync should run.
    """

    customer_id: str
    enabled: bool = True
```

### Overridden Methods

`@override` methods may omit a local docstring when the inherited contract is
still sufficient. The bundled helpers treat docstring-less overrides as manual
exceptions, but they do not verify that the inherited documentation is correct
or complete. If an override changes behavior, side effects, outputs, or
exceptions, write or expand a local docstring.

### Static Methods

Avoid introducing new `@staticmethod` members unless an existing public API,
framework hook, or external interface already requires one. When you do have
to document a static method, treat it like any other callable.

```python
@staticmethod
def validate_config(config: dict) -> bool:
    """Validate configuration dictionary structure and values.

    Args:
        config: Configuration dictionary to validate.

    Returns:
        True if valid, False otherwise.

    Examples:
        >>> valid_config = {'host': 'localhost', 'port': 8080}
        >>> MyClass.validate_config(valid_config)
        True

        >>> invalid_config = {'host': 'localhost'}
        >>> MyClass.validate_config(invalid_config)
        False
    """
    pass
```

### Class Methods

```python
@classmethod
def from_json(cls, json_str: str) -> 'MyClass':
    """Create instance from JSON string.

    Args:
        json_str: JSON representation of object.

    Returns:
        New instance populated from JSON data.

    Raises:
        JSONDecodeError: If json_str is invalid JSON.

    Examples:
        >>> json_data = '{"name": "test", "value": 42}'
        >>> obj = MyClass.from_json(json_data)
        >>> obj.name
        'test'
    """
    pass
```

## Examples Section Guidelines

Examples are helpful but optional. Add an `Examples:` section when a concrete
call, expected output, edge case, or return shape is easier to understand from
an example than from prose alone.

If you include examples:

1. **Use realistic scenarios** - Show actual use cases, not toy examples
2. **Prefer interactive style when appropriate** - Use `>>>` for REPL-style examples
3. **Lead with the common path** - Show the main usage before edge cases
4. **Add edge cases when they materially help** - Do not pad the docstring
5. **Keep them executable and accurate** - Examples should work if copied

### Multiple Example Patterns

```python
def calculate_statistics(data: list[float], percentiles: list[int] = None) -> dict:
    """Calculate descriptive statistics for numerical data.

    Args:
        data: Numerical data to analyze.
        percentiles: Percentile values to compute.
            Defaults to [25, 50, 75].

    Returns:
        Statistics including mean, median, std, and percentiles.

    Examples:
        Basic usage with default percentiles:
        >>> data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> stats = calculate_statistics(data)
        >>> stats['mean']
        5.5
        >>> stats['percentiles'][50]
        5.5

        Custom percentiles:
        >>> stats = calculate_statistics(data, percentiles=[10, 90])
        >>> stats['percentiles'][90]
        9.1

        Empty data handling:
        >>> calculate_statistics([])
        {'mean': None, 'median': None, 'std': None, 'percentiles': {}}

        Large dataset:
        >>> import random
        >>> large_data = [random.random() for _ in range(10000)]
        >>> stats = calculate_statistics(large_data)
        >>> 0 <= stats['mean'] <= 1
        True
    """
    pass
```

## Quick Reference

### Checklist for Complete Docstrings

- [ ] Summary line (one physical line, <= 80 chars, consistent style,
        ends with `.`, `?`, or `!`)
- [ ] Extended description (if needed for clarity)
- [ ] Args section explains parameters; include type text only when needed
- [ ] Returns or Yields section adds semantics or type detail not already clear
- [ ] Raises section covers interface-relevant exceptions
- [ ] Examples section only when it materially helps the caller
- [ ] Type hints in function signature match docstring
- [ ] Examples are executable and produce stated output, if included

### Common Mistakes to Avoid

1. **Redundant or missing type information** - Do not repeat obvious types from
    annotations, but do add type detail when the signature does not make it clear
2. **Vague descriptions** - Be specific about what parameters do and what's returned
3. **Forcing examples everywhere** - Add examples when they clarify usage, not by default
4. **Mixed summary style** - Use descriptive or imperative summaries consistently within a file
5. **Incomplete raised exceptions** - Document interface-relevant exceptions, not API misuse cases
6. **Complex returns without structure** - For dicts/complex types, describe the structure
7. **Examples that don't work** - Test your examples before including them

The bundled index and audit scripts are intentionally conservative helpers.
Use the prompt's scope rules to filter out trivial or out-of-scope callables
before treating raw helper output as the final pass/fail signal. They are not
a standalone completeness oracle for required module, class, or dataclass
documentation. Decorator detection is tuned for canonical spellings such as
`@property`, `@cached_property`, `@overload`, and `typing.overload`; if a
project aliases those decorators to different local names, review them
manually.

## Resources

For more detailed examples and edge cases, see these bundled resources:

Bundled scripts are authoritative for this skill. Use similarly named
workspace tools only as a fallback when the bundled copy is unavailable in the
current checkout.

- [references/examples.md](references/examples.md) - Comprehensive collection of real-world docstring examples
- [references/python-docstrings-google.prompt.md](references/python-docstrings-google.prompt.md) - Copilot prompt for Google-style docstrings, pytest fixtures/tests, property and overload handling, and sync-audit workflows
- [scripts/python-docstring-indexer.py](scripts/python-docstring-indexer.py) - Authoritative callable inventory for modules, classes, functions, fixtures, tests, and nested definitions
- [scripts/python-docstring-mismatch-finder.py](scripts/python-docstring-mismatch-finder.py) - Authoritative raw mismatch checker for Args and Returns/Yields drift in Google-style docstrings; apply prompt-scope filtering before treating results as final
- [scripts/python-docstring-sync-audit.py](scripts/python-docstring-sync-audit.py) - Authoritative raw structured sync audit for functions, methods, fixtures, tests, and nested callables; apply prompt-scope filtering before treating results as final
