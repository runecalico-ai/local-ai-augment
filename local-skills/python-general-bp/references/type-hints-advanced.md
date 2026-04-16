# Advanced Type Hints

## Generic Types

### TypeVar for Generic Functions

```python
from typing import TypeVar

T = TypeVar('T')

def first(items: list[T]) -> T | None:
    """Get first item from list.

    Args:
        items: List of items of any type.

    Returns:
        First item or None if empty.

    Example:
        >>> first([1, 2, 3])
        1
        >>> first(['a', 'b'])
        'a'
    """
    return items[0] if items else None


# Constrained TypeVar
Number = TypeVar('Number', int, float)

def add(a: Number, b: Number) -> Number:
    """Add two numbers of the same type."""
    return a + b  # type: ignore


# Bound TypeVar
from abc import ABC

class Animal(ABC):
    """Base animal class."""
    pass

class Dog(Animal):
    """Dog class."""
    pass

A = TypeVar('A', bound=Animal)

def create_animal(animal_class: type[A]) -> A:
    """Create instance of any Animal subclass."""
    return animal_class()
```

### Generic Classes

```python
from typing import Generic, TypeVar

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Stack(Generic[T]):
    """Generic stack data structure."""

    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        """Push item onto stack."""
        self._items.append(item)

    def pop(self) -> T | None:
        """Pop item from stack."""
        return self._items.pop() if self._items else None

    def peek(self) -> T | None:
        """Peek at top item without removing."""
        return self._items[-1] if self._items else None

# Usage
int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)

str_stack: Stack[str] = Stack()
str_stack.push('hello')


class Cache(Generic[K, V]):
    """Generic cache with key-value pairs."""

    def __init__(self, max_size: int = 100) -> None:
        self._cache: dict[K, V] = {}
        self._max_size = max_size

    def get(self, key: K) -> V | None:
        """Get value by key."""
        return self._cache.get(key)

    def set(self, key: K, value: V) -> None:
        """Set key-value pair."""
        if len(self._cache) >= self._max_size:
            # Remove oldest item
            self._cache.pop(next(iter(self._cache)))
        self._cache[key] = value

# Usage
user_cache: Cache[int, User] = Cache()
user_cache.set(1, User(id=1, name='Alice'))
```

## Protocol Classes (Structural Subtyping)

### Basic Protocols

```python
from typing import Protocol

class Drawable(Protocol):
    """Protocol for drawable objects."""

    def draw(self) -> None:
        """Draw the object."""
        ...

class Circle:
    """Circle class (no explicit inheritance needed)."""

    def draw(self) -> None:
        print("Drawing circle")

class Rectangle:
    """Rectangle class."""

    def draw(self) -> None:
        print("Drawing rectangle")

def render(drawable: Drawable) -> None:
    """Render any drawable object."""
    drawable.draw()

# Both work without inheritance
render(Circle())
render(Rectangle())
```

### Runtime Checkable Protocols

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closeable(Protocol):
    """Protocol for closeable resources."""

    def close(self) -> None:
        """Close the resource."""
        ...

class File:
    """File class."""

    def close(self) -> None:
        print("File closed")

f = File()
print(isinstance(f, Closeable))  # True

def cleanup(resource: Closeable) -> None:
    """Clean up any closeable resource."""
    if isinstance(resource, Closeable):
        resource.close()
```

### Generic Protocols

```python
from typing import Protocol, TypeVar

T = TypeVar('T')

class Repository(Protocol[T]):
    """Generic repository protocol."""

    def get(self, id: int) -> T | None:
        """Get item by ID."""
        ...

    def save(self, item: T) -> T:
        """Save item."""
        ...

    def delete(self, id: int) -> bool:
        """Delete item by ID."""
        ...

class UserRepository:
    """User repository implementation."""

    def get(self, id: int) -> User | None:
        # Implementation
        pass

    def save(self, item: User) -> User:
        # Implementation
        pass

    def delete(self, id: int) -> bool:
        # Implementation
        pass

def process_repository(repo: Repository[User]) -> None:
    """Process any user repository."""
    user = repo.get(1)
    if user:
        print(user.name)
```

## Callable Types

### Function Types

```python
from collections.abc import Callable

# Simple callable
Validator = Callable[[str], bool]

def validate_email(email: str) -> bool:
    """Validate email format."""
    return '@' in email

def apply_validation(value: str, validator: Validator) -> bool:
    """Apply validation function."""
    return validator(value)

apply_validation('test@example.com', validate_email)


# Multiple parameters
Processor = Callable[[str, int], str]

def process(text: str, count: int) -> str:
    """Process text."""
    return text * count

def apply_processor(data: str, n: int, proc: Processor) -> str:
    """Apply processor function."""
    return proc(data, n)


# With keyword arguments (use ...)
ComplexFunc = Callable[..., int]

def complex_func(a: int, b: str, c: bool = True) -> int:
    """Complex function with various parameters."""
    return a

def call_complex(func: ComplexFunc) -> int:
    """Call complex function."""
    return func(1, 'test', c=False)
```

### Method Types

```python
from typing import Callable

class Calculator:
    """Calculator with method types."""

    def __init__(self) -> None:
        # Store method references
        self._operations: dict[str, Callable[[int, int], int]] = {
            'add': self._add,
            'subtract': self._subtract,
            'multiply': self._multiply,
        }

    def _add(self, a: int, b: int) -> int:
        return a + b

    def _subtract(self, a: int, b: int) -> int:
        return a - b

    def _multiply(self, a: int, b: int) -> int:
        return a * b

    def execute(self, operation: str, a: int, b: int) -> int:
        """Execute operation by name."""
        op_func = self._operations.get(operation)
        if op_func is None:
            raise ValueError(f"Unknown operation: {operation}")
        return op_func(a, b)
```

## Literal Types

### Literal Values

```python
from typing import Literal

# Restrict to specific values
Mode = Literal['read', 'write', 'append']

def open_file(path: str, mode: Mode) -> None:
    """Open file with restricted mode values."""
    print(f"Opening {path} in {mode} mode")

open_file('data.txt', 'read')  # OK
# open_file('data.txt', 'invalid')  # Type error


# Multiple literals
Status = Literal['pending', 'running', 'completed', 'failed']

class Task:
    """Task with status."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._status: Status = 'pending'

    def set_status(self, status: Status) -> None:
        """Set task status."""
        self._status = status

    @property
    def status(self) -> Status:
        """Get current status."""
        return self._status


# Literal with numbers and booleans
LogLevel = Literal[0, 1, 2, 3]
Flag = Literal[True, False]  # Same as bool, but more explicit
```

## TypedDict

### Basic TypedDict

```python
from typing import TypedDict

class UserDict(TypedDict):
    """Type definition for user dictionary."""
    id: int
    name: str
    email: str
    is_active: bool

def create_user(user_data: UserDict) -> None:
    """Create user from dictionary."""
    print(f"Creating user: {user_data['name']}")

# Usage
user: UserDict = {
    'id': 1,
    'name': 'Alice',
    'email': 'alice@example.com',
    'is_active': True,
}
create_user(user)
```

### Optional Keys

```python
from typing import TypedDict, NotRequired

# Python 3.11+
class ConfigDict(TypedDict):
    """Configuration dictionary with optional keys."""
    host: str
    port: int
    debug: NotRequired[bool]  # Optional key
    timeout: NotRequired[int]  # Optional key

config: ConfigDict = {
    'host': 'localhost',
    'port': 8080,
    # debug and timeout are optional
}


# Alternative for Python 3.10
class ConfigDictLegacy(TypedDict, total=False):
    """Config with all optional keys."""
    debug: bool
    timeout: int

class RequiredConfig(TypedDict):
    """Required config keys."""
    host: str
    port: int

class FullConfig(RequiredConfig, ConfigDictLegacy):
    """Combined config."""
    pass
```

## Union Types and Optional

### Modern Union Syntax

```python
# Python 3.10+ uses | operator
def process_data(data: int | str | None) -> str:
    """Process data of multiple types."""
    if data is None:
        return 'No data'
    elif isinstance(data, int):
        return f'Number: {data}'
    else:
        return f'Text: {data}'


# Optional is same as T | None
from typing import Optional

def find_user(user_id: int) -> User | None:  # Preferred in Python 3.10+
    """Find user by ID."""
    pass

def find_user_legacy(user_id: int) -> Optional[User]:  # Legacy style
    """Find user by ID."""
    pass
```

### Type Guards

```python
from typing import TypeGuard

def is_str_list(val: list[int | str]) -> TypeGuard[list[str]]:
    """Check if all items are strings."""
    return all(isinstance(item, str) for item in val)

def process_items(items: list[int | str]) -> None:
    """Process items with type narrowing."""
    if is_str_list(items):
        # Type checker knows items is list[str] here
        for item in items:
            print(item.upper())  # OK, item is str
    else:
        # items could be list[int | str]
        print(len(items))
```

## ParamSpec and Concatenate

### ParamSpec for Decorators

```python
from typing import Callable, ParamSpec, TypeVar
from functools import wraps
import time

P = ParamSpec('P')
R = TypeVar('R')

def timer(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that times function execution."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

@timer
def slow_function(n: int, message: str = 'default') -> str:
    """Example function with timer."""
    time.sleep(0.1)
    return f"{message} {n}"

# Type checker understands parameters are preserved
result = slow_function(42, message='test')
```

### Concatenate for Adding Parameters

```python
from typing import Callable, Concatenate, ParamSpec, TypeVar

P = ParamSpec('P')
R = TypeVar('R')

class Logger:
    """Logger class."""

    def log(self, message: str) -> None:
        print(f"LOG: {message}")

def with_logging(
    func: Callable[Concatenate[Logger, P], R]
) -> Callable[P, R]:
    """Decorator that adds logger as first argument."""
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        logger = Logger()
        return func(logger, *args, **kwargs)
    return wrapper

@with_logging
def process(logger: Logger, data: str, count: int) -> str:
    """Process with logging."""
    logger.log(f"Processing {data}")
    return data * count

# Call without logger argument (decorator adds it)
result = process('test', 3)
```

## Annotating Complex Structures

### Nested Structures

```python
from typing import Any

# Complex nested type
ApiResponse = dict[str, int | str | list[dict[str, Any]]]

def parse_response(response: ApiResponse) -> list[User]:
    """Parse API response to user list."""
    users = []
    if 'data' in response and isinstance(response['data'], list):
        for item in response['data']:
            if isinstance(item, dict):
                users.append(User(**item))
    return users


# Better: Use TypedDict for clarity
class UserData(TypedDict):
    """User data from API."""
    id: int
    name: str
    email: str

class ApiResponseTyped(TypedDict):
    """Typed API response."""
    status: int
    message: str
    data: list[UserData]

def parse_response_typed(response: ApiResponseTyped) -> list[User]:
    """Parse typed API response."""
    return [User(**user_data) for user_data in response['data']]
```

### Type Aliases

```python
from typing import TypeAlias

# Simple alias
UserId: TypeAlias = int
Email: TypeAlias = str

# Complex alias
JsonDict: TypeAlias = dict[str, Any]
JsonList: TypeAlias = list[Any]
Json: TypeAlias = JsonDict | JsonList | str | int | float | bool | None

# Generic alias
Matrix: TypeAlias = list[list[float]]

def multiply_matrices(a: Matrix, b: Matrix) -> Matrix:
    """Multiply two matrices."""
    # Implementation
    return [[0.0]]
```

## Best Practices

1. **Use built-in generics**: Prefer `list[int]` over `List[int]` (Python 3.9+)
2. **Use `|` for unions**: Prefer `int | str` over `Union[int, str]` (Python 3.10+)
3. **Protocol over ABC**: Use Protocol for structural typing when appropriate
4. **TypedDict for dicts**: Use TypedDict instead of `dict[str, Any]` when structure is known
5. **Literal for constants**: Use Literal to restrict to specific values
6. **ParamSpec for decorators**: Preserve parameter types in decorators
7. **TypeGuard for narrowing**: Use TypeGuard for runtime type narrowing
8. **Type aliases for clarity**: Create aliases for complex types
9. **Generic classes**: Make classes generic when they work with multiple types
10. **Avoid Any**: Use specific types; Any defeats the purpose of type hints
