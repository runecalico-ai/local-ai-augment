# Fixture Patterns

Advanced pytest fixture patterns for complex testing scenarios.

## Table of Contents

- Factory Fixtures
- Fixture Composition
- Parametrized Fixtures
- Request Context
- Autouse Fixtures
- Fixture Finalization

## Factory Fixtures

Factory fixtures return a callable that creates test objects with custom parameters.

### Basic Factory

```python
import pytest

@pytest.fixture
def user_factory():
    """Factory for creating test users with custom attributes."""
    def create_user(name="test_user", email=None, is_active=True):
        return User(
            name=name,
            email=email or f"{name}@example.com",
            is_active=is_active
        )
    return create_user

def test_user_creation(user_factory):
    # Create multiple users with different attributes
    admin = user_factory(name="admin", is_active=True)
    guest = user_factory(name="guest", is_active=False)

    assert admin.is_active
    assert not guest.is_active
```

### Factory with State Tracking

```python
@pytest.fixture
def user_factory(db_session):
    """Factory that tracks created users for cleanup."""
    created_users = []

    def create_user(**kwargs):
        user = User(**kwargs)
        db_session.add(user)
        db_session.commit()
        created_users.append(user)
        return user

    yield create_user

    # Cleanup all created users
    for user in created_users:
        db_session.delete(user)
    db_session.commit()
```

## Fixture Composition

Combine multiple fixtures to build complex test scenarios.

### Layered Fixtures

```python
@pytest.fixture
def database():
    """Provides database connection."""
    db = Database("test.db")
    db.connect()
    yield db
    db.disconnect()

@pytest.fixture
def db_schema(database):
    """Creates schema on top of database fixture."""
    database.create_tables()
    yield database
    database.drop_tables()

@pytest.fixture
def db_with_data(db_schema):
    """Populates database with test data."""
    db_schema.insert("users", {"id": 1, "name": "Alice"})
    db_schema.insert("users", {"id": 2, "name": "Bob"})
    yield db_schema
    db_schema.clear_all()

def test_query_users(db_with_data):
    users = db_with_data.query("SELECT * FROM users")
    assert len(users) == 2
```

### Fixture Dependencies

```python
@pytest.fixture
def app_config(tmp_path):
    """Creates application configuration."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("debug: true\nport: 8080")
    return config_file

@pytest.fixture
def app(app_config):
    """Creates application instance with config."""
    application = Application(config_path=app_config)
    yield application
    application.shutdown()

@pytest.fixture
def authenticated_app(app):
    """Application with authentication enabled."""
    app.login("test_user", "password")
    yield app
    app.logout()
```

## Parametrized Fixtures

Create multiple variations of a fixture.

### Basic Parametrization

```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def database(request):
    """Provides different database backends."""
    db_type = request.param
    db = create_database(db_type)
    db.connect()
    yield db
    db.disconnect()

def test_insert_user(database):
    # This test runs 3 times, once for each database type
    database.insert("users", {"name": "Alice"})
    assert database.count("users") == 1
```

### Parametrized with IDs

```python
@pytest.fixture(
    params=[
        ("admin", True),
        ("user", False),
        ("guest", False),
    ],
    ids=["admin-active", "user-inactive", "guest-inactive"]
)
def user(request):
    """Provides different user types."""
    name, is_active = request.param
    return User(name=name, is_active=is_active)

def test_user_permissions(user):
    # Test runs with clear IDs in output
    if user.name == "admin":
        assert user.has_permission("delete")
```

### Conditional Parametrization

```python
import sys

database_backends = ["sqlite"]
if sys.platform != "win32":
    database_backends.extend(["postgres", "mysql"])

@pytest.fixture(params=database_backends)
def database(request):
    return create_database(request.param)
```

## Request Context

Access test context and metadata within fixtures.

### Using request.param

```python
@pytest.fixture
def sample_data(request):
    """Provides different data samples based on parameter."""
    data_map = {
        "small": list(range(10)),
        "medium": list(range(100)),
        "large": list(range(1000)),
    }
    return data_map[request.param]

@pytest.mark.parametrize("sample_data", ["small", "medium"], indirect=True)
def test_processing(sample_data):
    result = process(sample_data)
    assert len(result) == len(sample_data)
```

### Using request.node

```python
@pytest.fixture
def log_file(request, tmp_path):
    """Creates a log file named after the test."""
    test_name = request.node.name
    log_path = tmp_path / f"{test_name}.log"

    logging.basicConfig(filename=log_path, level=logging.DEBUG)
    yield log_path

    # Read log for debugging if test failed
    if request.node.rep_call.failed:
        print(f"\n--- Log from {test_name} ---")
        print(log_path.read_text())
```

### Dynamic Configuration

```python
@pytest.fixture
def server_port(request):
    """Provides custom port from marker or uses default."""
    marker = request.node.get_closest_marker("port")
    if marker:
        return marker.args[0]
    return 8080

@pytest.mark.port(9000)
def test_custom_port_server(server_port):
    assert server_port == 9000

def test_default_port_server(server_port):
    assert server_port == 8080
```

## Autouse Fixtures

Fixtures that run automatically for all tests.

### Test Isolation

```python
@pytest.fixture(autouse=True)
def reset_global_state():
    """Resets global state before each test."""
    global_cache.clear()
    global_config.reset()
    yield
    # Cleanup runs after each test
    global_cache.clear()
```

### Logging Setup

```python
@pytest.fixture(autouse=True, scope="session")
def configure_logging():
    """Configure logging for entire test session."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
```

### Environment Cleanup

```python
@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Ensures clean environment for each test."""
    # Remove problematic environment variables
    env_vars_to_remove = ["AWS_PROFILE", "DATABASE_URL"]
    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)
```

## Fixture Finalization

Proper cleanup and teardown patterns.

### Using Yield

```python
@pytest.fixture
def database_connection():
    """Provides database connection with guaranteed cleanup."""
    conn = create_connection()
    conn.begin_transaction()

    yield conn

    # Teardown always runs
    conn.rollback()
    conn.close()
```

### Using request.addfinalizer

```python
@pytest.fixture
def temp_resources(request, tmp_path):
    """Creates multiple temporary resources."""
    resources = []

    def create_resource(name):
        path = tmp_path / name
        path.touch()
        resources.append(path)
        return path

    def cleanup():
        for resource in resources:
            if resource.exists():
                resource.unlink()

    request.addfinalizer(cleanup)
    return create_resource
```

### Error Handling in Teardown

```python
@pytest.fixture
def server(request):
    """Starts server with error-safe shutdown."""
    server = Server()
    server.start()

    def shutdown():
        try:
            server.stop(timeout=5)
        except TimeoutError:
            print("Server shutdown timed out, forcing kill")
            server.kill()
        except Exception as e:
            print(f"Error during shutdown: {e}")

    request.addfinalizer(shutdown)
    yield server
```

## Advanced Patterns

### Caching Expensive Operations

```python
@pytest.fixture(scope="session")
def trained_model(tmp_path_factory):
    """Trains ML model once per session."""
    cache_dir = tmp_path_factory.mktemp("models")
    model_path = cache_dir / "model.pkl"

    if not model_path.exists():
        model = train_model()  # Expensive operation
        save_model(model, model_path)

    return load_model(model_path)
```

### Context Manager Fixtures

```python
from contextlib import contextmanager

@pytest.fixture
def transaction(database):
    """Provides database transaction context."""
    @contextmanager
    def _transaction():
        tx = database.begin()
        try:
            yield tx
            tx.commit()
        except Exception:
            tx.rollback()
            raise

    return _transaction

def test_with_transaction(transaction):
    with transaction():
        # Operations within transaction
        pass
```

### Fixture Markers

```python
@pytest.fixture
def api_client(request):
    """Creates API client with optional authentication."""
    use_auth = request.node.get_closest_marker("authenticated")

    if use_auth:
        client = APIClient(auth=("user", "pass"))
    else:
        client = APIClient()

    yield client
    client.close()

@pytest.mark.authenticated
def test_protected_endpoint(api_client):
    response = api_client.get("/protected")
    assert response.status == 200

def test_public_endpoint(api_client):
    response = api_client.get("/public")
    assert response.status == 200
```
