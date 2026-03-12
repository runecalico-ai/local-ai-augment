# Test Templates

Complete, ready-to-use templates for common testing scenarios.

## Table of Contents

- REST API Testing
- Database Testing
- File Processing
- CLI Application Testing
- Configuration Testing
- Authentication Testing
- Data Validation

## REST API Testing

### Basic API Test Suite

```python
# tests/test_api.py
import pytest
from unittest.mock import patch, Mock

class TestUserAPI:
    """Tests for User API endpoints."""

    @patch("requests.get")
    def test_get_user_success(self, mock_get):
        """Test successful user retrieval."""
        # arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com"
        }
        mock_get.return_value = mock_response

        # act
        from myapp.api import get_user
        user = get_user(1)

        # assert
        assert user["name"] == "Alice"
        assert user["email"] == "alice@example.com"
        mock_get.assert_called_once_with(
            "https://api.example.com/users/1",
            timeout=30
        )

    @patch("requests.get")
    def test_get_user_not_found(self, mock_get):
        """Test user not found returns None."""
        # arrange
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # act
        from myapp.api import get_user
        user = get_user(999)

        # assert
        assert user is None

    @patch("requests.post")
    def test_create_user(self, mock_post):
        """Test creating a new user."""
        # arrange
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 2,
            "name": "Bob",
            "email": "bob@example.com"
        }
        mock_post.return_value = mock_response

        # act
        from myapp.api import create_user
        user = create_user(name="Bob", email="bob@example.com")

        # assert
        assert user["id"] == 2
        assert user["name"] == "Bob"
```

### Parametrized API Tests

```python
import pytest

@pytest.mark.parametrize(
    "status_code,expected_result",
    [
        (200, "success"),
        (201, "created"),
        (400, "bad_request"),
        (401, "unauthorized"),
        (404, "not_found"),
        (500, "server_error"),
    ],
    ids=["ok", "created", "bad-request", "unauthorized", "not-found", "server-error"]
)
@patch("requests.get")
def test_api_status_codes(mock_get, status_code, expected_result):
    """Test API handles various status codes correctly."""
    mock_get.return_value.status_code = status_code

    from myapp.api import fetch_with_error_handling
    result = fetch_with_error_handling("https://api.example.com/data")

    assert result.status == expected_result
```

## Database Testing

### Complete Database Test Suite

```python
# tests/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from myapp.models import Base, User, Post

@pytest.fixture(scope="function")
def db_engine():
    """Create in-memory SQLite database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture
def db_session(db_engine):
    """Provide database session with rollback."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(name="Alice", email="alice@example.com")
    db_session.add(user)
    db_session.commit()
    return user

class TestUserModel:
    """Tests for User model."""

    def test_create_user(self, db_session):
        """Test creating a new user."""
        # arrange & act
        user = User(name="Bob", email="bob@example.com")
        db_session.add(user)
        db_session.commit()

        # assert
        assert user.id is not None
        assert user.name == "Bob"
        assert user.email == "bob@example.com"

    def test_query_user_by_email(self, db_session, sample_user):
        """Test querying user by email."""
        # act
        found = db_session.query(User).filter_by(
            email="alice@example.com"
        ).first()

        # assert
        assert found is not None
        assert found.id == sample_user.id
        assert found.name == "Alice"

    def test_update_user(self, db_session, sample_user):
        """Test updating user information."""
        # act
        sample_user.name = "Alice Smith"
        db_session.commit()

        # assert
        updated = db_session.query(User).get(sample_user.id)
        assert updated.name == "Alice Smith"

    def test_delete_user(self, db_session, sample_user):
        """Test deleting a user."""
        # arrange
        user_id = sample_user.id

        # act
        db_session.delete(sample_user)
        db_session.commit()

        # assert
        deleted = db_session.query(User).get(user_id)
        assert deleted is None

    def test_user_posts_relationship(self, db_session, sample_user):
        """Test user-posts relationship."""
        # arrange
        post1 = Post(title="First Post", user_id=sample_user.id)
        post2 = Post(title="Second Post", user_id=sample_user.id)
        db_session.add_all([post1, post2])
        db_session.commit()

        # act
        user_with_posts = db_session.query(User).get(sample_user.id)

        # assert
        assert len(user_with_posts.posts) == 2
        assert user_with_posts.posts[0].title == "First Post"
```

## File Processing

### File Operations Test Suite

```python
# tests/test_file_processor.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_csv(tmp_path):
    """Create sample CSV file."""
    csv_file = tmp_path / "data.csv"
    csv_file.write_text(
        "name,age,city\n"
        "Alice,30,NYC\n"
        "Bob,25,LA\n"
    )
    return csv_file

@pytest.fixture
def sample_json(tmp_path):
    """Create sample JSON file."""
    import json
    json_file = tmp_path / "data.json"
    data = {
        "users": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
    }
    json_file.write_text(json.dumps(data, indent=2))
    return json_file

class TestCSVProcessor:
    """Tests for CSV file processing."""

    def test_read_csv(self, sample_csv):
        """Test reading CSV file."""
        from myapp.processor import read_csv

        data = read_csv(sample_csv)

        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["age"] == "25"

    def test_write_csv(self, tmp_path):
        """Test writing CSV file."""
        from myapp.processor import write_csv

        output_file = tmp_path / "output.csv"
        data = [
            {"name": "Charlie", "age": 35},
            {"name": "Diana", "age": 28}
        ]

        write_csv(data, output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "Charlie" in content
        assert "Diana" in content

    def test_filter_csv_by_age(self, sample_csv, tmp_path):
        """Test filtering CSV data."""
        from myapp.processor import filter_csv

        output_file = tmp_path / "filtered.csv"
        filter_csv(sample_csv, output_file, min_age=28)

        content = output_file.read_text()
        assert "Alice" in content
        assert "Bob" not in content

class TestJSONProcessor:
    """Tests for JSON file processing."""

    def test_read_json(self, sample_json):
        """Test reading JSON file."""
        from myapp.processor import read_json

        data = read_json(sample_json)

        assert "users" in data
        assert len(data["users"]) == 2
        assert data["users"][0]["name"] == "Alice"

    def test_write_json(self, tmp_path):
        """Test writing JSON file."""
        from myapp.processor import write_json

        output_file = tmp_path / "output.json"
        data = {"status": "ok", "count": 42}

        write_json(data, output_file)

        assert output_file.exists()
        import json
        loaded = json.loads(output_file.read_text())
        assert loaded["status"] == "ok"

    def test_merge_json_files(self, tmp_path):
        """Test merging multiple JSON files."""
        from myapp.processor import merge_json

        file1 = tmp_path / "data1.json"
        file2 = tmp_path / "data2.json"
        file1.write_text('{"a": 1}')
        file2.write_text('{"b": 2}')

        output = tmp_path / "merged.json"
        merge_json([file1, file2], output)

        import json
        result = json.loads(output.read_text())
        assert result == {"a": 1, "b": 2}
```

## CLI Application Testing

### Command Line Interface Tests

```python
# tests/test_cli.py
import pytest
from click.testing import CliRunner
from myapp.cli import cli, init, process

@pytest.fixture
def runner():
    """Provides Click CLI test runner."""
    return CliRunner()

class TestCLI:
    """Tests for CLI commands."""

    def test_cli_help(self, runner):
        """Test CLI shows help message."""
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.output

    def test_init_command(self, runner, tmp_path):
        """Test init command creates config."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(init, ["--name", "myproject"])

            assert result.exit_code == 0
            assert Path("config.yaml").exists()
            assert "Initialized" in result.output

    def test_process_command_success(self, runner, tmp_path):
        """Test process command with valid input."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("test data")

        result = runner.invoke(process, [str(input_file)])

        assert result.exit_code == 0
        assert "Processed" in result.output

    def test_process_command_missing_file(self, runner):
        """Test process command with missing file."""
        result = runner.invoke(process, ["nonexistent.txt"])

        assert result.exit_code != 0
        assert "Error" in result.output

    @pytest.mark.parametrize(
        "verbosity,expected_level",
        [
            ([], "INFO"),
            (["-v"], "DEBUG"),
            (["-q"], "WARNING"),
        ],
    )
    def test_verbosity_levels(self, runner, verbosity, expected_level):
        """Test different verbosity levels."""
        result = runner.invoke(cli, [*verbosity, "status"])

        assert expected_level in result.output or result.exit_code == 0
```

## Configuration Testing

### Configuration Management Tests

```python
# tests/test_config.py
import pytest
import os
from myapp.config import Config, load_config, validate_config

@pytest.fixture
def config_file(tmp_path):
    """Create sample configuration file."""
    config = tmp_path / "config.yaml"
    config.write_text("""
database:
  host: localhost
  port: 5432
  name: testdb

api:
  url: https://api.example.com
  timeout: 30

logging:
  level: DEBUG
""")
    return config

class TestConfig:
    """Tests for configuration management."""

    def test_load_config_from_file(self, config_file):
        """Test loading configuration from file."""
        config = load_config(config_file)

        assert config.database.host == "localhost"
        assert config.database.port == 5432
        assert config.api.timeout == 30

    def test_config_missing_file(self):
        """Test loading nonexistent config file."""
        with pytest.raises(FileNotFoundError):
            load_config("missing.yaml")

    def test_config_from_env_vars(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("DB_HOST", "remote-host")
        monkeypatch.setenv("DB_PORT", "3306")

        config = Config.from_env()

        assert config.database.host == "remote-host"
        assert config.database.port == 3306

    def test_config_validation_success(self, config_file):
        """Test configuration validation passes."""
        config = load_config(config_file)

        is_valid, errors = validate_config(config)

        assert is_valid
        assert len(errors) == 0

    def test_config_validation_failure(self, tmp_path):
        """Test configuration validation fails."""
        invalid_config = tmp_path / "invalid.yaml"
        invalid_config.write_text("database:\n  host: localhost\n")

        config = load_config(invalid_config)
        is_valid, errors = validate_config(config)

        assert not is_valid
        assert "port" in str(errors)

    def test_config_override(self, config_file):
        """Test configuration override."""
        config = load_config(config_file)
        config.override(database_host="newhost", api_timeout=60)

        assert config.database.host == "newhost"
        assert config.api.timeout == 60
```

## Authentication Testing

### Authentication and Authorization Tests

```python
# tests/test_auth.py
import pytest
from datetime import datetime, timedelta
from myapp.auth import authenticate, create_token, verify_token
from myapp.models import User

@pytest.fixture
def test_user():
    """Create test user."""
    return User(
        id=1,
        username="testuser",
        password_hash="hashed_password",
        role="user"
    )

@pytest.fixture
def admin_user():
    """Create admin user."""
    return User(
        id=2,
        username="admin",
        password_hash="hashed_password",
        role="admin"
    )

class TestAuthentication:
    """Tests for authentication."""

    @patch("myapp.auth.verify_password")
    @patch("myapp.auth.get_user_by_username")
    def test_authenticate_success(
        self, mock_get_user, mock_verify, test_user
    ):
        """Test successful authentication."""
        mock_get_user.return_value = test_user
        mock_verify.return_value = True

        user = authenticate("testuser", "password123")

        assert user is not None
        assert user.username == "testuser"

    @patch("myapp.auth.get_user_by_username")
    def test_authenticate_user_not_found(self, mock_get_user):
        """Test authentication with unknown user."""
        mock_get_user.return_value = None

        user = authenticate("unknown", "password")

        assert user is None

    @patch("myapp.auth.verify_password")
    @patch("myapp.auth.get_user_by_username")
    def test_authenticate_wrong_password(
        self, mock_get_user, mock_verify, test_user
    ):
        """Test authentication with wrong password."""
        mock_get_user.return_value = test_user
        mock_verify.return_value = False

        user = authenticate("testuser", "wrongpassword")

        assert user is None

class TestJWTTokens:
    """Tests for JWT token management."""

    def test_create_token(self, test_user):
        """Test creating JWT token."""
        token = create_token(test_user)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_valid_token(self, test_user):
        """Test verifying valid token."""
        token = create_token(test_user)

        payload = verify_token(token)

        assert payload is not None
        assert payload["user_id"] == test_user.id
        assert payload["username"] == test_user.username

    def test_verify_expired_token(self, test_user, monkeypatch):
        """Test verifying expired token."""
        # Create token that expires immediately
        with patch("myapp.auth.TOKEN_EXPIRY", timedelta(seconds=-1)):
            token = create_token(test_user)

        payload = verify_token(token)

        assert payload is None

    def test_verify_invalid_token(self):
        """Test verifying invalid token."""
        payload = verify_token("invalid.token.here")

        assert payload is None

class TestAuthorization:
    """Tests for authorization."""

    def test_user_has_permission(self, admin_user):
        """Test admin has all permissions."""
        from myapp.auth import has_permission

        assert has_permission(admin_user, "read")
        assert has_permission(admin_user, "write")
        assert has_permission(admin_user, "delete")

    def test_user_lacks_permission(self, test_user):
        """Test regular user lacks admin permissions."""
        from myapp.auth import has_permission

        assert has_permission(test_user, "read")
        assert not has_permission(test_user, "delete")
```

## Data Validation

### Data Validation Test Suite

```python
# tests/test_validation.py
import pytest
from myapp.validation import (
    validate_email,
    validate_phone,
    validate_date,
    validate_schema
)

class TestEmailValidation:
    """Tests for email validation."""

    @pytest.mark.parametrize(
        "email",
        [
            "user@example.com",
            "test.user@example.co.uk",
            "user+tag@example.com",
            "user_name@example-domain.com",
        ],
    )
    def test_valid_emails(self, email):
        """Test valid email formats."""
        assert validate_email(email) is True

    @pytest.mark.parametrize(
        "email",
        [
            "invalid",
            "@example.com",
            "user@",
            "user @example.com",
            "user@example",
        ],
    )
    def test_invalid_emails(self, email):
        """Test invalid email formats."""
        assert validate_email(email) is False

class TestSchemaValidation:
    """Tests for schema validation."""

    def test_validate_user_schema_success(self):
        """Test valid user data."""
        data = {
            "name": "Alice",
            "email": "alice@example.com",
            "age": 30
        }
        schema = {
            "name": str,
            "email": str,
            "age": int
        }

        is_valid, errors = validate_schema(data, schema)

        assert is_valid
        assert len(errors) == 0

    def test_validate_schema_missing_field(self):
        """Test schema validation with missing field."""
        data = {"name": "Alice"}
        schema = {"name": str, "email": str}

        is_valid, errors = validate_schema(data, schema)

        assert not is_valid
        assert "email" in errors

    def test_validate_schema_wrong_type(self):
        """Test schema validation with wrong type."""
        data = {"name": "Alice", "age": "thirty"}
        schema = {"name": str, "age": int}

        is_valid, errors = validate_schema(data, schema)

        assert not is_valid
        assert "age" in errors
```
