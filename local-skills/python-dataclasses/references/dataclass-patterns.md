# Advanced Dataclass Patterns

## Generic Dataclasses

Python dataclasses support `Generic` for typed containers.

```python
from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

@dataclass
class Box(Generic[T]):
    value: T
    label: str = ""

    def map(self, func) -> 'Box':
        return Box(value=func(self.value), label=self.label)

box: Box[int] = Box(value=42, label="answer")
str_box = box.map(str)   # Box(value='42', label='answer')


@dataclass
class Pair(Generic[K, V]):
    key: K
    value: V

    def swap(self) -> 'Pair[V, K]':
        return Pair(key=self.value, value=self.key)

p: Pair[str, int] = Pair(key="age", value=30)
p.swap()   # Pair(key=30, value='age')


@dataclass
class Stack(Generic[T]):
    _items: list[T] = field(default_factory=list, repr=False, init=False)

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)
```

---

## Abstract / Base Dataclasses

Combine `@dataclass` with `ABC` to enforce interface contracts in subclasses.

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class Shape(ABC):
    color: str = "black"

    @property
    @abstractmethod
    def area(self) -> float: ...

    @property
    @abstractmethod
    def perimeter(self) -> float: ...

    def describe(self) -> str:
        return f"{self.__class__.__name__}(color={self.color}, area={self.area:.2f})"

@dataclass
class Rectangle(Shape):
    width: float = 0.0
    height: float = 0.0

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

@dataclass
class Circle(Shape):
    radius: float = 0.0

    @property
    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2

    @property
    def perimeter(self) -> float:
        import math
        return 2 * math.pi * self.radius
```

---

## Protocol Compliance

Dataclasses can satisfy `Protocol` interfaces without explicit inheritance.

```python
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict: ...

    @classmethod
    def from_dict(cls, data: dict) -> 'Serializable': ...

@dataclass
class UserDTO:
    id: int
    name: str
    email: str

    def to_dict(self) -> dict:
        return {'id': self.id, 'name': self.name, 'email': self.email}

    @classmethod
    def from_dict(cls, data: dict) -> 'UserDTO':
        return cls(id=data['id'], name=data['name'], email=data['email'])

assert isinstance(UserDTO(1, "a", "b"), Serializable)  # True at runtime
```

---

## Pattern Matching Support (`match_args`)

Python 3.10+ dataclasses generate `__match_args__` automatically, enabling structural pattern matching.

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

@dataclass
class Circle:
    center: Point
    radius: float

@dataclass
class Rectangle:
    top_left: Point
    bottom_right: Point

def describe_shape(shape) -> str:
    match shape:
        case Circle(center=Point(x=0, y=0), radius=r):
            return f"Circle centered at origin, r={r}"
        case Circle(center=c, radius=r):
            return f"Circle at ({c.x}, {c.y}), r={r}"
        case Rectangle(top_left=Point(x=x1, y=y1), bottom_right=Point(x=x2, y=y2)):
            return f"Rectangle ({x1},{y1}) → ({x2},{y2})"
        case _:
            return "Unknown shape"
```

---

## Factory Patterns

### Class Factory Methods (prefer over complex `__post_init__`)

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class Event:
    name: str
    start: datetime
    end: datetime
    attendees: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def all_day(cls, name: str, date: datetime, attendees=None) -> 'Event':
        """Factory for an all-day event."""
        return cls(
            name=name,
            start=date.replace(hour=0, minute=0, second=0),
            end=date.replace(hour=23, minute=59, second=59),
            attendees=attendees or [],
        )

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        return cls(
            name=data['name'],
            start=datetime.fromisoformat(data['start']),
            end=datetime.fromisoformat(data['end']),
            attendees=data.get('attendees', []),
        )
```

---

## `__init_subclass__` for Automatic Registration

```python
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Command:
    _registry: ClassVar[dict[str, type]] = {}
    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'name'):
            Command._registry[cls.name] = cls

    @classmethod
    def dispatch(cls, command_name: str, **kwargs) -> 'Command':
        if command_name not in cls._registry:
            raise KeyError(f"Unknown command: {command_name!r}")
        return cls._registry[command_name](**kwargs)

@dataclass
class StartCommand(Command):
    name: ClassVar[str] = 'start'
    service: str

@dataclass
class StopCommand(Command):
    name: ClassVar[str] = 'stop'
    service: str
    force: bool = False

# Auto-registered
cmd = Command.dispatch('start', service='api')
assert isinstance(cmd, StartCommand)
```

---

## Computed Fields Excluded from `__init__`

```python
from dataclasses import dataclass, field

@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    # Derived — not settable, not in __init__
    area: float = field(init=False, repr=False)
    aspect_ratio: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        object.__setattr__(self, 'area', self.width * self.height)
        object.__setattr__(self, 'aspect_ratio', self.width / self.height)

# For frozen dataclasses, use object.__setattr__ inside __post_init__
@dataclass(frozen=True)
class ImmutableBox:
    x: float
    y: float
    width: float
    height: float
    area: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # Must use object.__setattr__ because frozen=True blocks normal assignment
        object.__setattr__(self, 'area', self.width * self.height)
```

---

## Keyword-Only Inheritance (Python 3.10+)

The cleanest solution for the "fields-with-defaults before fields-without-defaults" inheritance problem:

```python
from dataclasses import dataclass, field, KW_ONLY

@dataclass
class Node:
    value: int
    _: KW_ONLY                   # everything after this marker is keyword-only
    parent: 'Node | None' = None # default, but keyword-only — safe for subclassing

@dataclass
class LeafNode(Node):
    label: str                   # required, no default — works because parent's
                                 # default field is keyword-only

leaf = LeafNode(value=5, label="leaf-A")
leaf = LeafNode(value=5, label="leaf-A", parent=Node(value=0))
```

---

## Dataclass with `__slots__` and Properties (Manual Pattern, Pre-3.10)

Before Python 3.10's `slots=True`, slots and properties together required extra care:

```python
from dataclasses import dataclass

# Python 3.10+: use slots=True directly
@dataclass(slots=True)
class Point3D:
    x: float
    y: float
    z: float = 0.0

    @property
    def magnitude(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

# Python 3.9 and below: manual approach needed (avoid this if possible)
```

---

## Testing Dataclasses

```python
import pytest
from dataclasses import replace

# Test construction and defaults
def test_log_entry_defaults():
    entry = LogEntry(message="hello")
    assert entry.level == "INFO"
    assert entry.tags == []
    assert entry.tags is not LogEntry(message="other").tags  # separate instances

# Test immutability
def test_frozen_dataclass_is_immutable():
    c = Color(255, 0, 0)
    with pytest.raises(FrozenInstanceError):
        c.r = 128

# Test replace (immutable update)
def test_replace():
    original = Config(host="prod.example.com", port=443)
    dev = replace(original, host="localhost", port=8080)
    assert dev.host == "localhost"
    assert dev.port == 8080
    assert original.host == "prod.example.com"   # unchanged

# Test post_init validation
def test_date_range_rejects_inverted_range():
    with pytest.raises(ValueError, match="end.*must be after"):
        DateRange(start=date(2025, 6, 1), end=date(2025, 5, 1))

# Test ordering
def test_version_ordering():
    assert Version(1, 0) < Version(2, 0)
    assert Version(2, 0, 1) > Version(2, 0, 0)
    assert sorted([Version(2,1), Version(1,0)]) == [Version(1,0), Version(2,1)]
```
