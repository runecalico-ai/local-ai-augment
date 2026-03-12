# Mocking Strategies

Comprehensive patterns for mocking in pytest tests.

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

### When to Use Mock

Use `unittest.mock` for:
- Replacing functions/methods with specific return values
- Tracking calls and arguments
- Mocking external libraries (requests, boto3, etc.)

```python
from unittest.mock import Mock, patch

@patch("requests.get")
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

@patch("requests.get")
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
@patch("requests.post")
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
@patch("requests.get")
def test_network_error_handling(mock_get):
    mock_get.side_effect = requests.ConnectionError("Network unavailable")

    from myapp.api import fetch_data
    result = fetch_data("https://api.example.com")

    assert result is None  # Graceful failure
```

### Using responses Library

```python
import responses

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

def test_read_config():
    mock_data = "debug: true\nport: 8080"

    with patch("builtins.open", mock_open(read_data=mock_data)):
        config = read_config("config.yaml")
        assert config["debug"] is True
```

### Using tmp_path (Preferred)

```python
def test_read_config_with_real_file(tmp_path):
    # Create real temporary file
    config_file = tmp_path / "config.yaml"
    config_file.write_text("debug: true\nport: 8080")

    config = read_config(config_file)
    assert config["debug"] is True
```

### Mocking pathlib

```python
@patch("pathlib.Path.exists")
@patch("pathlib.Path.read_text")
def test_file_content(mock_read, mock_exists):
    mock_exists.return_value = True
    mock_read.return_value = "test content"

    content = load_file("test.txt")
    assert content == "test content"
```

## Mocking Time and Randomness

### Using freezegun

```python
from freezegun import freeze_time
from datetime import datetime

@freeze_time("2024-01-15 10:30:00")
def test_timestamp():
    result = generate_report()
    assert result.timestamp == datetime(2024, 1, 15, 10, 30, 0)
```

### Mocking datetime

```python
from unittest.mock import patch
from datetime import datetime

@patch("myapp.utils.datetime")
def test_current_time(mock_datetime):
    mock_datetime.now.return_value = datetime(2024, 1, 15, 12, 0, 0)

    result = get_current_timestamp()
    assert result == "2024-01-15 12:00:00"
```

### Controlling Randomness

```python
import random

def test_random_selection():
    random.seed(42)  # Deterministic randomness

    result = shuffle_items([1, 2, 3, 4, 5])
    assert result == [2, 5, 4, 1, 3]  # Always same order

@patch("random.randint")
def test_random_number(mock_randint):
    mock_randint.return_value = 7

    result = roll_dice()
    assert result == 7
```

## Database Mocking

### Mocking Database Queries

```python
from unittest.mock import Mock, patch

@patch("myapp.db.session.query")
def test_get_user(mock_query):
    # Setup mock
    mock_user = Mock()
    mock_user.id = 1
    mock_user.name = "Alice"
    mock_query.return_value.filter.return_value.first.return_value = mock_user

    # Test
    user = get_user_by_id(1)
    assert user.name == "Alice"
```

### Using In-Memory Database (Preferred)

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    db_session.commit()

    found = db_session.query(User).filter_by(name="Alice").first()
    assert found.email == "alice@example.com"
```

### Mocking Query Results

```python
@patch("myapp.models.User.query")
def test_user_count(mock_query):
    mock_query.count.return_value = 42

    count = get_user_count()
    assert count == 42
```

## Class and Method Mocking

### Mocking Class Instances

```python
from unittest.mock import Mock, patch

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
def test_user_service(monkeypatch):
    class MockDatabase:
        def get_user(self, user_id):
            return {"id": user_id, "name": "Test User"}

    monkeypatch.setattr("myapp.database.Database", MockDatabase)

    service = UserService()
    user = service.fetch_user(1)
    assert user["name"] == "Test User"
```

### Partial Mocking

```python
from unittest.mock import patch

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

def test_callback_called():
    callback = Mock()

    process_items([1, 2, 3], on_complete=callback)

    callback.assert_called_once()
    assert callback.call_args[0][0] == 3  # Called with count
```

### Multiple Side Effects

```python
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
@patch("requests.get")
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
from unittest.mock import call

@patch("myapp.logger.log")
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
from unittest.mock import Mock, patch, MagicMock

@patch("myapp.db.get_connection")
def test_database_context(mock_get_connection):
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_get_connection.return_value = mock_conn

    with get_connection() as conn:
        conn.execute("SELECT 1")

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
