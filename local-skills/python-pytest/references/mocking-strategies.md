# Mocking Strategies

Comprehensive patterns for mocking in pytest tests.

These examples are repo-dependent patterns, not drop-in defaults. Inspect the repo's existing seams, fixtures, helpers, and runner before copying a mocking strategy.

## Table of Contents

- Mock vs Monkeypatch
- Mocking External APIs
- Mocking File Operations
- Mocking Time and Randomness
- Database Mocking
- Class and Method Mocking
- Testing with Side Effects

## Mock vs Monkeypatch

Choose the right tool for the job.

Patch where the code under test looks up the symbol, not the library definition in isolation.

### When to Use Mock

Use `unittest.mock` for:
- Replacing functions/methods with specific return values
- Tracking calls and arguments
- Mocking external libraries (requests, boto3, etc.)

```python
from unittest.mock import Mock, patch
from myapp.api import fetch_data

@patch("myapp.api.requests.get")
def test_api_call(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"data": "value"}

    result = fetch_data("https://api.example.com")
    assert result == {"data": "value"}
    mock_get.assert_called_once()
```

### When to Use Monkeypatch

Use `monkeypatch` for:
- Environment variables
- Attributes on modules or classes
- Dictionary entries
- Simple function replacement

```python
def test_env_var(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")

    from myapp import get_api_key
    assert get_api_key() == "test-key"

def test_attribute_patch(monkeypatch):
    monkeypatch.setattr("myapp.config.DEBUG", True)

    from myapp.config import DEBUG
    assert DEBUG is True
```

## Mocking External APIs

### Basic HTTP Mocking

```python
from unittest.mock import patch, Mock

@patch("myapp.api.requests.get")
def test_fetch_user_success(mock_get):
    # Setup mock response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": 1,
        "name": "Alice"
    }
    mock_get.return_value = mock_response

    # Test
    from myapp.api import fetch_user
    user = fetch_user(1)

    assert user["name"] == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1")
```

### Mocking with Side Effects

```python
from unittest.mock import Mock, patch
from myapp.api import api_call_with_retry

@patch("myapp.api.requests.post")
def test_retry_on_failure(mock_post):
    # First call fails, second succeeds
    mock_post.side_effect = [
        Mock(status_code=500),
        Mock(status_code=200, json=lambda: {"success": True})
    ]

    result = api_call_with_retry()
    assert result["success"] is True
    assert mock_post.call_count == 2
```

### Mocking Exceptions

```python
import requests
from unittest.mock import patch

@patch("myapp.api.requests.get")
def test_network_error_handling(mock_get):
    mock_get.side_effect = requests.ConnectionError("Network unavailable")

    from myapp.api import fetch_data
    result = fetch_data("https://api.example.com")

    assert result is None  # Graceful failure
```

### Using responses Library

Use this only if the repo already depends on `responses`; otherwise prefer `patch` or `monkeypatch`.

```python
import responses
from myapp.api import fetch_user

@responses.activate
def test_api_with_responses():
    responses.add(
        responses.GET,
        "https://api.example.com/users/1",
        json={"id": 1, "name": "Alice"},
        status=200
    )

    result = fetch_user(1)
    assert result["name"] == "Alice"
```

## Mocking File Operations

### Mocking open()

```python
from unittest.mock import mock_open, patch
from myapp.config import read_config

def test_read_config():
    mock_data = "debug: true\nport: 8080"

    with patch("builtins.open", mock_open(read_data=mock_data)):
        config = read_config("config.yaml")
        assert config["debug"] is True
```

### Using tmp_path (Preferred)

```python
from myapp.config import read_config

def test_read_config_with_real_file(tmp_path):
    # Create real temporary file
    config_file = tmp_path / "config.yaml"
    config_file.write_text("debug: true\nport: 8080")

    config = read_config(config_file)
    assert config["debug"] is True
```

### Mocking pathlib

```python
from unittest.mock import patch
from myapp.files import load_file

@patch("myapp.files.Path.exists")
@patch("myapp.files.Path.read_text")
def test_file_content(mock_read, mock_exists):
    mock_exists.return_value = True
    mock_read.return_value = "test content"

    content = load_file("test.txt")
    assert content == "test content"
```

## Mocking Time and Randomness

### Using freezegun

Use this only if the repo already depends on `freezegun`; otherwise prefer patching the time boundary directly.

```python
from freezegun import freeze_time
from datetime import datetime
from myapp.reports import generate_report

@freeze_time("2024-01-15 10:30:00")
def test_timestamp():
    result = generate_report()
    assert result.timestamp == datetime(2024, 1, 15, 10, 30, 0)
```

### Mocking datetime

```python
from unittest.mock import patch
from datetime import datetime
from myapp.utils import get_current_timestamp

@patch("myapp.utils.datetime")
def test_current_time(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)

    result = get_current_timestamp()
    assert result == "2024-01-15 12:00:00"
```

### Controlling Randomness

```python
import random
from unittest.mock import patch
from myapp.game import roll_dice, shuffle_items

def test_random_selection():
    first = shuffle_items([1, 2, 3, 4, 5], rng=random.Random(42))
    second = shuffle_items([1, 2, 3, 4, 5], rng=random.Random(42))
    assert first == second

@patch("myapp.game.random.randint")
def test_random_number(mock_randint):
    mock_randint.return_value = 7

    result = roll_dice()
    assert result == 7
```

## Database Mocking

### Mocking a Repository Boundary

```python
from unittest.mock import patch
from myapp.models import User
from myapp.services.users import get_user_by_id

@patch("myapp.services.users.fetch_user")
def test_get_user(mock_fetch_user):
    mock_fetch_user.return_value = {"id": 1, "name": "Alice"}

    user = get_user_by_id(1)
    assert user["name"] == "Alice"
```

### Using the Repo's Database Test Strategy

Prefer the repo's existing database fixture or container strategy. The SQLite example below is only a fallback when the repo already uses it or the code path is genuinely dialect-agnostic.

SQLite in-memory databases are connection-scoped. If the repo needs shared state across connections or threads, use the repo's existing harness or a tmp_path-backed database instead of assuming one shared in-memory database.

```python
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from myapp.models import Base, User

@pytest.fixture
def db_session():
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

def test_create_user(db_session):
    user = User(name="Alice", email="alice@example.com")
    db_session.add(user)
    db_session.flush()

    found = db_session.execute(
        select(User).filter_by(name="Alice")
    ).scalar_one()
    assert found.email == "alice@example.com"
```

### Patching a Repository Seam

```python
from unittest.mock import patch
from myapp.services.users import get_user_count

@patch("myapp.services.users.count_users")
def test_user_count(mock_count_users):
    mock_count_users.return_value = 42

    count = get_user_count()
    assert count == 42
```

## Class and Method Mocking

### Mocking Class Instances

```python
from unittest.mock import Mock, patch
from myapp.services import send_welcome_email

@patch("myapp.services.EmailService")
def test_send_notification(MockEmailService):
    # Mock the class constructor
    mock_service = Mock()
    MockEmailService.return_value = mock_service

    # Test
    send_welcome_email("alice@example.com")

    # Verify
    mock_service.send.assert_called_once_with(
        to="alice@example.com",
        subject="Welcome"
    )
```

### Mocking Instance Methods

```python
from myapp.services.user_service import UserService

def test_user_service(monkeypatch):
    class MockDatabase:
        def get_user(self, user_id):
            return {"id": user_id, "name": "Test User"}

    monkeypatch.setattr("myapp.services.user_service.Database", MockDatabase)

    service = UserService()
    user = service.fetch_user(1)
    assert user["name"] == "Test User"
```

### Partial Mocking

```python
from unittest.mock import patch
from myapp.math import Calculator

class TestCalculator:
    def test_complex_operation(self):
        calc = Calculator()

        # Mock only one method
        with patch.object(calc, "expensive_operation", return_value=42):
            result = calc.complex_calculation(10)
            assert result == 52  # 10 + 42
```

### Mocking Properties

```python
from unittest.mock import PropertyMock, patch
from myapp.models import User

@patch("myapp.models.User.is_active", new_callable=PropertyMock)
def test_active_user(mock_is_active):
    mock_is_active.return_value = True

    user = User(name="Alice")
    assert user.is_active is True
```

## Testing with Side Effects

### Tracking Calls

```python
from unittest.mock import Mock
from myapp.processor import process_items

def test_callback_called():
    callback = Mock()

    process_items([1, 2, 3], on_complete=callback)

    callback.assert_called_once()
    assert callback.call_args[0][0] == 3  # Called with count
```

### Multiple Side Effects

```python
from unittest.mock import patch
from myapp.api import fetch_all_pages

@patch("myapp.api.fetch_data")
def test_pagination(mock_fetch):
    # Different responses for each call
    mock_fetch.side_effect = [
        {"items": [1, 2], "next": "page2"},
        {"items": [3, 4], "next": "page3"},
        {"items": [5], "next": None}
    ]

    all_items = fetch_all_pages()
    assert all_items == [1, 2, 3, 4, 5]
    assert mock_fetch.call_count == 3
```

### Callable Side Effects

```python
from unittest.mock import Mock, patch
from myapp.api import fetch

@patch("myapp.api.requests.get")
def test_dynamic_responses(mock_get):
    def dynamic_response(url):
        if "users" in url:
            return Mock(json=lambda: {"type": "user"})
        else:
            return Mock(json=lambda: {"type": "other"})

    mock_get.side_effect = dynamic_response

    user_response = fetch("https://api.example.com/users/1")
    assert user_response["type"] == "user"
```

### Verifying Call Arguments

```python
from unittest.mock import call, patch
from myapp.worker import process_with_logging

@patch("myapp.worker.logger.log")
def test_logging_calls(mock_log):
    process_with_logging([1, 2, 3])

    # Verify specific calls
    mock_log.assert_any_call("Processing: 1")
    mock_log.assert_any_call("Processing: 2")

    # Verify all calls in order
    expected_calls = [
        call("Start"),
        call("Processing: 1"),
        call("Processing: 2"),
        call("Processing: 3"),
        call("Done")
    ]
    mock_log.assert_has_calls(expected_calls)
```

## Context Managers

### Mocking Context Managers

```python
from unittest.mock import patch, MagicMock
from myapp.db_client import run_query

@patch("myapp.db_client.get_connection")
def test_database_context(mock_get_connection):
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_get_connection.return_value = mock_conn

    run_query("SELECT 1")

    mock_conn.execute.assert_called_once_with("SELECT 1")
    mock_conn.__exit__.assert_called_once()
```

## Best Practices

### Do's

✅ Mock at the boundary (external APIs, filesystem, network)
✅ Use real objects for your own code when possible
✅ Keep mocks simple and focused
✅ Verify important interactions with `assert_called_*`
✅ Use `tmp_path` instead of mocking file operations
✅ Prefer dependency injection over deep mocking

### Don'ts

❌ Don't mock what you don't own (unless necessary)
❌ Don't over-specify mock expectations
❌ Don't mock internal implementation details
❌ Don't create complex mock hierarchies
❌ Don't forget to verify mock calls when behavior matters
