---
name: python-pytest
description: Expert Python testing with pytest. Use when writing, reviewing, or refactoring Python test files. Provides best practices for test structure, fixtures, parametrization, mocking, async tests, and comprehensive testing patterns following pytest idioms and Python 3.10+ standards.
---

# Python Pytest

Expert guidance for writing comprehensive, maintainable Python tests using pytest with modern best practices.

## When to Use This Skill

- Writing new pytest test files
- Reviewing or refactoring existing tests
- Setting up test fixtures and parametrization
- Implementing mocking and async tests
- Organizing test suites and test coverage
- Debugging flaky or failing tests
- Converting tests from unittest to pytest

## Core Principles

### Token-Efficient Test Generation

- **Be concise**: Remove redundant explanations; favor compact examples
- **Structure clearly**: Use Markdown headings, lists, fenced code blocks
- **Semantic precision**: Use correct pytest terminology (fixture, parametrize, assert)
- **Minimal examples**: Tests should be focused, readable, and minimal
- **Idiomatic pytest**: Follow pytest and Python 3.10+ idioms with type hints

### Testing Philosophy

- **One test, one behavior**: Each test function validates a single aspect
- **Arrange-Act-Assert**: Clear three-phase structure with comments
- **Fast by default**: Unit tests complete in milliseconds; mark slow tests
- **Deterministic**: No timing dependencies, randomness without seeds, or flaky behavior
- **Isolated**: Use fixtures, mocks, and `tmp_path` to avoid side effects

## Quick Start

### Basic Test Structure

```python
# tests/test_math_utils.py
def test_clamp_within_bounds_returns_value():
    # arrange
    from your_package.math_utils import clamp
    lo, hi, value = 1, 10, 5

    # act
    got = clamp(value, lo, hi)

    # assert
    assert got == 5, "Value within bounds should be returned unchanged"
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize(
    "text, expected",
    [
        ("true", True),
        ("TRUE", True),
        ("False", False),
        ("0", False),
        ("1", True),
    ],
)
def test_parse_bool_accepts_common_truthy_falsy(text, expected):
    from your_package.parse import parse_bool
    assert parse_bool(text) is expected
```

### Exception Testing

```python
import pytest

def test_load_config_raises_on_missing_file(tmp_path):
    from your_package.config import load_config
    missing = tmp_path / "absent.yaml"
    with pytest.raises(FileNotFoundError):
        load_config(missing)
```

## Test Organization

### Directory Structure

```
project/
├── src/
│   └── your_package/
│       ├── math_utils.py
│       └── config.py
└── tests/
    ├── conftest.py          # Shared fixtures
    ├── test_math_utils.py   # Mirror source structure
    └── test_config.py
```

### Naming Conventions

- **Files**: `test_<module>.py`
- **Functions**: `test_<unit>_<behavior>_<condition>()`
- **Fixtures**: Nouns describing what they provide (`db_session`, `tmp_conf`)

### Test Markers

Configure in `pytest.ini`:

```ini
[pytest]
addopts = -q
testpaths = tests
markers =
    integration: hits real services or multiple layers
    slow: long-running tests
    snapshot: snapshot-based tests
```

Use markers in tests:

```python
@pytest.mark.integration
def test_full_api_flow():
    # Integration test that hits real services
    pass

@pytest.mark.slow
def test_large_dataset_processing():
    # Test that takes >1 second
    pass
```

## Fixtures

### Basic Fixtures

```python
# tests/conftest.py
import json
import pytest

@pytest.fixture
def config_file(tmp_path):
    """Creates a temporary JSON config file."""
    cfg = {"host": "localhost", "port": 8080}
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return p

@pytest.fixture
def db_session():
    """Provides a clean database session."""
    session = create_test_session()
    yield session
    session.rollback()
    session.close()
```

### Fixture Scopes

```python
@pytest.fixture(scope="session")
def database_engine():
    """Created once per test session."""
    engine = create_engine("sqlite:///:memory:")
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")  # Default
def clean_state():
    """Created for each test function."""
    return {}
```

## Mocking

### Using unittest.mock

```python
from unittest.mock import patch, Mock

@patch("your_package.api.requests.get")
def test_fetch_user_handles_404(mock_get):
    mock_get.return_value.status_code = 404
    from your_package.api import fetch_user
    assert fetch_user("abc") is None
```

### Using monkeypatch

```python
def test_env_is_read(monkeypatch):
    monkeypatch.setenv("APP_MODE", "test")
    from your_package.settings import get_mode
    assert get_mode() == "test"
```

### Mocking Best Practices

- Prefer dependency injection over mocking when possible
- Mock at the boundary (external APIs, filesystem, network)
- Don't mock your own code—test behavior directly
- Use `AsyncMock` for async functions

## Async Testing

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_fetch_all_concurrent():
    from your_package.asyncio_utils import fetch_all
    urls = ["http://example.com/a", "http://example.com/b"]
    results = await fetch_all(urls)
    assert len(results) == 2

@pytest.mark.asyncio
async def test_async_api_call(monkeypatch):
    mock_response = AsyncMock(return_value={"status": "ok"})
    monkeypatch.setattr("your_package.client.fetch", mock_response)
    from your_package.client import get_data
    result = await get_data()
    assert result["status"] == "ok"
```

## Assertions

### Clear Assertion Messages

```python
# Good: specific message
assert result.count == expected_count, f"Expected {expected_count} items, got {result.count}"

# Good: context-rich message
assert user.is_active, f"User {user.id} should be active after registration"

# Avoid: no message
assert result == expected
```

### Exception Assertions

```python
# Basic exception check
with pytest.raises(ValueError):
    parse_number("invalid")

# Check exception message
with pytest.raises(ValueError, match=r"Invalid format.*"):
    parse_number("abc")

# Capture exception for detailed inspection
with pytest.raises(ValidationError) as exc_info:
    validate_user({"name": ""})
assert "name" in str(exc_info.value)
```

## Common Patterns

### Testing Logging

```python
def test_process_logs_warning(caplog):
    from your_package.processor import process_data
    process_data([])
    assert "Empty dataset" in caplog.text
    assert caplog.records[0].levelname == "WARNING"
```

### Temporary Files

```python
def test_save_report(tmp_path):
    from your_package.reports import save_report
    output = tmp_path / "report.pdf"
    save_report(data, output)
    assert output.exists()
    assert output.stat().st_size > 0
```

### Deterministic Randomness

```python
import random

def test_random_selection_is_deterministic():
    random.seed(42)
    from your_package.sampling import select_random
    result = select_random(range(100), k=5)
    assert result == [81, 14, 3, 94, 35]  # Deterministic with seed
```

## Advanced Topics

For detailed guidance on specific testing scenarios, see:

- **[Fixture Patterns](references/fixture-patterns.md)** - Advanced fixture usage, factories, and composition
- **[Mocking Strategies](references/mocking-strategies.md)** - Comprehensive mocking patterns and edge cases
- **[Async Testing](references/async-testing.md)** - Detailed async/await testing patterns
- **[Test Templates](references/test-templates.md)** - Complete templates for common testing scenarios

## Coverage & Quality

### Coverage Targets

- Aim for **90%+ line coverage**, but prioritize meaningful assertions
- Ensure branch coverage on critical paths and error handling
- Use coverage to find untested code, not as a quality metric

### Running with Coverage

```bash
pytest --cov=your_package --cov-report=html tests/
```

### Definition of Done

- ✅ Meaningful coverage of success, edge, and error paths
- ✅ No network/filesystem side effects (unless marked `@pytest.mark.integration`)
- ✅ Deterministic: fixed seeds, frozen time, no sleeps/races
- ✅ Clear names, minimal duplication, helpful failure messages
- ✅ Type hints and linting clean (ruff, mypy, pylint)
- ✅ Fast: unit suite completes in seconds

## Common Pitfalls to Avoid

❌ **Don't test implementation details** - Focus on behavior, not private methods
❌ **Don't create flaky tests** - Eliminate timing, network, or order dependencies
❌ **Don't mock your own code** - Use dependency injection instead
❌ **Don't use real external services** - Mock or mark as integration tests
❌ **Don't skip assertion messages** - Help future debuggers understand failures
❌ **Don't create large opaque fixtures** - Keep fixtures simple and focused

## Refactoring Guidance

When updating existing tests:

1. **Preserve semantics**: Only change assertions when behavior meaningfully changed
2. **Strengthen weak assertions**: Check fields, types, and side effects
3. **Remove dead code**: Eliminate unused fixtures and helpers
4. **Consolidate duplicates**: Use parametrization, but maintain readability
5. **Document changes**: If test behavior changes, explain why in commit message

## Bug Fix Workflow

1. **Reproduce the bug**: Write a failing test that demonstrates the issue (RED)
2. **Fix the bug**: Modify code to make the test pass (GREEN)
3. **Refactor**: Clean up code and tests while keeping tests passing (REFACTOR)

## Legacy Code Testing

When adding tests to untested code:

1. **Write characterization tests**: Document current behavior
2. **Lock down inputs/outputs**: Establish baseline with snapshots or assertions
3. **Introduce refactors carefully**: Guard behavior with tests before changing structure
4. **Test small units**: Break large functions into testable pieces

## Quick Reference

### Essential pytest Commands

```bash
# Run all tests
pytest

# Run specific file or test
pytest tests/test_math.py
pytest tests/test_math.py::test_add

# Run with markers
pytest -m integration
pytest -m "not slow"

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run in parallel
pytest -n auto

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

### Common Fixtures

- `tmp_path`: Temporary directory unique to the test
- `tmp_path_factory`: Temporary directory with custom scope
- `monkeypatch`: Modify environment, attributes, dictionaries
- `caplog`: Capture log messages
- `capsys`: Capture stdout/stderr
- `capfd`: Capture file descriptors

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)
