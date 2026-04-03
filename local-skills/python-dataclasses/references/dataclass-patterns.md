# Advanced Dataclass Patterns

## Generic Dataclasses

Python dataclasses support `Generic` for typed containers.

```python
from dataclasses import dataclass, field
from typing import Callable, Generic, TypeVar

T = TypeVar('T')
U = TypeVar('U')
K = TypeVar('K')
V = TypeVar('V')

@dataclass
class Box(Generic[T]):
    value: T
    label: str = ""

    def map(self, func: Callable[[T], U]) -> 'Box[U]':
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

Dataclasses can satisfy `Protocol` interfaces without explicit inheritance, but any `from_dict` example here assumes trusted or already-validated mappings, not raw boundary data.

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

`@runtime_checkable` only performs a shallow runtime attribute check. Real protocol conformance still depends on static type checking.

---

## Pattern Matching Support (`match_args`)

Python 3.10+ dataclasses generate `__match_args__` automatically from non-keyword-only fields, enabling structural pattern matching. Keyword-only fields are excluded, so `@dataclass(kw_only=True)` disables positional matching unless you define `__match_args__` manually.

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
        case Point(0, y):
            return f"Point on y-axis at y={y}"
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

Keep `from_dict` factories for trusted or already-validated mappings. For untrusted JSON, HTTP, file, or environment-variable input, do not rely on a plain dataclass factory as the only validation or coercion layer; validate first or prefer Pydantic v2.

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
    def all_day(
        cls,
        name: str,
        date: datetime,
        attendees: list[str] | None = None,
    ) -> 'Event':
        """Factory for an all-day event."""
        return cls(
            name=name,
            start=date.replace(hour=0, minute=0, second=0),
            end=date.replace(hour=23, minute=59, second=59),
            attendees=[] if attendees is None else attendees.copy(),
        )

    @classmethod
    def from_dict(cls, data: dict) -> 'Event':
        return cls(
            name=data['name'],
            start=datetime.fromisoformat(data['start']),
            end=datetime.fromisoformat(data['end']),
            attendees=data.get('attendees', []).copy(),
        )
```

Use `None` as the sentinel for “not provided”, and copy caller-supplied mutables so the new instance does not share list state with the caller.

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
        if 'name' in cls.__dict__:
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

With `slots=True` on Python 3.10+, avoid parameterized base `__init_subclass__` hooks unless every parameter has a default; otherwise subclass creation raises `TypeError`. For this registration pattern, prefer post-decoration registration or avoid `slots=True`, because `__init_subclass__` runs before the replacement slotted class exists.

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
        self.area = self.width * self.height
        self.aspect_ratio = self.width / self.height

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

## Testing Dataclasses

For broader pytest guidance, use the **python-pytest** skill. The example below is self-contained and runnable.

```python
import pytest
from dataclasses import FrozenInstanceError, dataclass, field, replace
from datetime import date

@dataclass
class LogEntry:
    message: str
    tags: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

@dataclass
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("end must be after start")

def test_log_entry_uses_distinct_default_lists():
    first = LogEntry("hello")
    second = LogEntry("world")
    assert first.tags == []
    assert first.tags is not second.tags

def test_frozen_dataclass_blocks_rebinding():
    c = Color(255, 0, 0)
    with pytest.raises(FrozenInstanceError):
        c.r = 128

def test_post_init_validation_rejects_inverted_range():
    with pytest.raises(ValueError, match="end must be after"):
        DateRange(date(2025, 6, 1), date(2025, 5, 1))

def test_replace_rebuilds_value_fields():
    updated = replace(Color(1, 2, 3), g=9)
    assert updated == Color(1, 9, 3)
```
