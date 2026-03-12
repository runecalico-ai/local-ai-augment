---
name: python-google-docstrings
description: Expert Python docstring writer using Google Style format with enhanced examples section. Use when writing or reviewing Python function, class, or module docstrings. Provides comprehensive templates for functions, classes, methods, modules, and special cases with proper formatting, type hints, and practical examples.
---

# Python Google Docstrings

Expert guidance for writing comprehensive Python docstrings following the Google Style Guide with enhanced example sections.

## When to Use This Skill

- Writing docstrings for Python functions, methods, classes, or modules
- Reviewing or refactoring existing docstrings for consistency
- Adding examples to existing docstrings
- Ensuring proper formatting and completeness of documentation
- Converting other docstring formats to Google Style

## Core Principles

### Google Style Format

Google Style docstrings use section headers followed by indented content. Each section is separated by a blank line.

### Standard Sections (in order)

1. **Summary Line** - One-line summary ending with period
2. **Extended Description** (optional) - Additional details, separated by blank line
3. **Args** - Function/method parameters
4. **Returns** - Return value description
5. **Yields** - For generators
6. **Raises** - Exceptions that may be raised
7. **Examples** - Practical usage examples (enhanced addition)
8. **Note** - Additional notes (optional)
9. **See Also** (optional) - Related functions/classes
10. **References** (optional) - External references

### Key Formatting Rules

- Use triple double-quotes `"""`
- First line is a brief summary (imperative mood)
- Args section uses `name (type): Description` format
- Indent section content by 4 spaces
- Examples section should include `>>>` for interactive examples
- Always include type information in Args and Returns

## Function Docstrings

### Basic Function Template

```python
def function_name(arg1: str, arg2: int, optional_arg: bool = False) -> dict:
    """Brief summary of what the function does.

    More detailed explanation of the function's purpose and behavior.
    This can span multiple lines and paragraphs if needed.

    Args:
        arg1 (str): Description of the first argument.
        arg2 (int): Description of the second argument.
        optional_arg (bool, optional): Description of optional argument.
            Defaults to False.

    Returns:
        dict: Description of the return value. Include structure if complex,
            e.g., {'key1': value1_description, 'key2': value2_description}.

    Raises:
        ValueError: When arg2 is negative.
        TypeError: When arg1 is not a string.

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
        user_id (int): Unique identifier for the user.

    Returns:
        dict[str, Any]: User data dictionary with the following structure:
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
        cache_size (int, optional): Maximum number of cached items.
            Defaults to 100.
        strict_mode (bool, optional): Enable strict validation.
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
            filepath (str): Path to the CSV file.
            delimiter (str, optional): Field delimiter character.
                Defaults to ','.

        Returns:
            pd.DataFrame: Loaded data with inferred column types.

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
        filepath (str): Path to file to read.
        chunk_size (int, optional): Number of bytes per chunk.
            Defaults to 1024.

    Yields:
        str: Next chunk of file content.

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
    pass
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

```python
@property
def full_name(self) -> str:
    """Get user's full name combining first and last names.

    Returns:
        str: Full name in "First Last" format.

    Examples:
        >>> user.first_name = "John"
        >>> user.last_name = "Doe"
        >>> user.full_name
        'John Doe'
    """
    return f"{self.first_name} {self.last_name}"
```

### Static Methods

```python
@staticmethod
def validate_config(config: dict) -> bool:
    """Validate configuration dictionary structure and values.

    Args:
        config (dict): Configuration dictionary to validate.

    Returns:
        bool: True if valid, False otherwise.

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
        json_str (str): JSON representation of object.

    Returns:
        MyClass: New instance populated from JSON data.

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

The Examples section is an enhanced addition to standard Google Style. It should:

1. **Use realistic scenarios** - Show actual use cases, not toy examples
2. **Include expected output** - Use `>>>` for interactive examples
3. **Cover common patterns** - Basic usage first, then advanced
4. **Show edge cases** when relevant
5. **Be executable** - Examples should work if copied

### Multiple Example Patterns

```python
def calculate_statistics(data: list[float], percentiles: list[int] = None) -> dict:
    """Calculate descriptive statistics for numerical data.

    Args:
        data (list[float]): Numerical data to analyze.
        percentiles (list[int], optional): Percentile values to compute.
            Defaults to [25, 50, 75].

    Returns:
        dict: Statistics including mean, median, std, and percentiles.

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

- [ ] Summary line (one line, imperative mood, ends with period)
- [ ] Extended description (if needed for clarity)
- [ ] Args section (all parameters with types)
- [ ] Returns section (type and structure)
- [ ] Raises section (all exceptions that may be raised)
- [ ] Examples section (at least one realistic example)
- [ ] Type hints in function signature match docstring
- [ ] Examples are executable and produce stated output

### Common Mistakes to Avoid

1. **Missing type information** - Always specify types in Args and Returns
2. **Vague descriptions** - Be specific about what parameters do and what's returned
3. **No examples** - Always include at least one practical example
4. **Imperative vs declarative** - Use imperative mood ("Calculate sum") not declarative ("Calculates sum")
5. **Incomplete raised exceptions** - Document all exceptions that may be raised
6. **Complex returns without structure** - For dicts/complex types, describe the structure
7. **Examples that don't work** - Test your examples before including them

## Resources

For more detailed examples and edge cases, see:

- [references/examples.md](references/examples.md) - Comprehensive collection of real-world docstring examples
