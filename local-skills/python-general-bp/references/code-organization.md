# Code Organization and Project Structure

## Project Layout

### Standard Python Package Structure

```
myproject/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── models.py
│       │   └── services.py
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── validators.py
│       │   └── helpers.py
│       └── config.py
├── tests/
│   ├── __init__.py
│   ├── test_core/
│   │   ├── test_models.py
│   │   └── test_services.py
│   └── test_utils/
│       └── test_validators.py
├── docs/
│   └── index.md
├── scripts/
│   └── setup_dev.py
├── pyproject.toml
├── README.md
└── .gitignore
```

### Package __init__.py Patterns

```python
# src/mypackage/__init__.py
"""MyPackage - A brief description of the package.

Detailed explanation of what the package does and how to use it.
"""

from __future__ import annotations

# Version info
__version__ = '1.0.0'
__author__ = 'Your Name'

# Import key classes/functions for easy access
from mypackage.core.models import User, Product
from mypackage.core.services import UserService, ProductService

# Define public API
__all__ = [
    'User',
    'Product',
    'UserService',
    'ProductService',
]
```

## Module Design

### Single Responsibility Modules

```python
# models.py - Data models only
from dataclasses import dataclass

@dataclass
class User:
    """User data model."""
    id: int
    name: str
    email: str


# services.py - Business logic
class UserService:
    """Service for user operations."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def create_user(self, name: str, email: str) -> User:
        """Create a new user."""
        # Validation and business logic
        user = User(id=0, name=name, email=email)
        return self._repository.save(user)


# repositories.py - Data access
class UserRepository:
    """Repository for user data access."""

    def save(self, user: User) -> User:
        """Save user to database."""
        # Database interaction
        pass

    def find_by_id(self, user_id: int) -> User | None:
        """Find user by ID."""
        pass
```

### Circular Import Prevention

```python
# Option 1: Move shared code to separate module
# shared.py
from typing import Protocol

class Repository(Protocol):
    """Repository interface."""
    pass


# models.py
from mypackage.shared import Repository


# services.py
from mypackage.shared import Repository


# Option 2: Use TYPE_CHECKING for type hints only
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypackage.repositories import UserRepository

class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository


# Option 3: Late imports inside functions
def create_service():
    from mypackage.repositories import UserRepository
    return UserService(UserRepository())
```

## Layered Architecture

### Three-Layer Pattern

```python
# Layer 1: Presentation/API
# api/routes.py
from fastapi import APIRouter, Depends

from mypackage.services import UserService
from mypackage.dependencies import get_user_service

router = APIRouter()

@router.post('/users')
async def create_user(
    name: str,
    email: str,
    service: UserService = Depends(get_user_service),
):
    """API endpoint for creating users."""
    user = service.create_user(name, email)
    return {'id': user.id, 'name': user.name}


# Layer 2: Business Logic
# services.py
class UserService:
    """Business logic for users."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    def create_user(self, name: str, email: str) -> User:
        """Create user with validation."""
        # Business rules and validation
        if not self._is_valid_email(email):
            raise ValueError(f"Invalid email: {email}")

        user = User(id=0, name=name, email=email)
        return self._repository.save(user)

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format."""
        return '@' in email


# Layer 3: Data Access
# repositories.py
import sqlite3

class UserRepository:
    """Data access for users."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def save(self, user: User) -> User:
        """Save user to database."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                'INSERT INTO users (name, email) VALUES (?, ?)',
                (user.name, user.email)
            )
            user.id = cursor.lastrowid
            return user
```

## Configuration Management

### Separate Configuration from Code

```python
# config/settings.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int
    name: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> DatabaseConfig:
        """Load from environment variables."""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            name=os.getenv('DB_NAME', 'mydb'),
            user=os.getenv('DB_USER', 'user'),
            password=os.getenv('DB_PASSWORD', ''),
        )

@dataclass
class AppConfig:
    """Application configuration."""
    debug: bool
    log_level: str
    database: DatabaseConfig

    @classmethod
    def from_env(cls) -> AppConfig:
        """Load configuration from environment."""
        return cls(
            debug=os.getenv('DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            database=DatabaseConfig.from_env(),
        )

# Global config instance
config = AppConfig.from_env()


# Usage in other modules
from mypackage.config import config

def connect_database():
    """Connect to database using config."""
    return connect(
        host=config.database.host,
        port=config.database.port,
    )
```

## Dependency Management

### pyproject.toml (Modern Standard)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mypackage"
version = "1.0.0"
description = "A brief description"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "you@example.com"}
]
keywords = ["keyword1", "keyword2"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
]
dependencies = [
    "requests>=2.28.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]
docs = [
    "sphinx>=5.0.0",
    "sphinx-rtd-theme>=1.0.0",
]

[project.urls]
Homepage = "https://github.com/username/mypackage"
Documentation = "https://mypackage.readthedocs.io"
Repository = "https://github.com/username/mypackage"
Issues = "https://github.com/username/mypackage/issues"

[project.scripts]
mycommand = "mypackage.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
addopts = "-v --strict-markers"

[tool.black]
line-length = 100
target-version = ["py310", "py311"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "F", "I", "N", "W", "B", "C4", "UP"]
ignore = []

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]
```

## Logging Setup

### Centralized Logging Configuration

```python
# logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(
    log_level: str = 'INFO',
    log_file: Path | None = None,
) -> None:
    """Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file. If None, logs to console only.
    """
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


# Usage in main module
from mypackage.logging_config import setup_logging

def main():
    setup_logging(log_level='DEBUG', log_file=Path('logs/app.log'))
    logger = logging.getLogger(__name__)
    logger.info('Application started')
```

## Package Distribution

### README.md Template

```markdown
# MyPackage

Brief description of what the package does.

## Installation

```bash
pip install mypackage
```

## Quick Start

```python
from mypackage import UserService

service = UserService()
user = service.create_user(name="Alice", email="alice@example.com")
```

## Features

- Feature 1
- Feature 2
- Feature 3

## Documentation

Full documentation available at: https://mypackage.readthedocs.io

## Development

```bash
# Clone repository
git clone https://github.com/username/mypackage.git
cd mypackage

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black .
ruff check .
mypy src/
```

## License

MIT License - see LICENSE file for details.
```

## Best Practices Summary

1. **Use src layout**: Keeps package code separate from tests and scripts
2. **Single responsibility**: Each module has one clear purpose
3. **Layer separation**: Presentation, business logic, data access in separate layers
4. **Configuration management**: Environment variables, separate config files
5. **Type hints everywhere**: Enable static analysis and better IDE support
6. **Comprehensive logging**: Structured logging with appropriate levels
7. **Modern tools**: pyproject.toml, ruff, black, mypy
8. **Clear package API**: Expose only necessary items in `__init__.py`
9. **Documentation**: README, docstrings, type hints
10. **Testing**: Mirror source structure in tests/
