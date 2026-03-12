---
name: python-dataclasses
description: Use when designing, writing, or reviewing Python dataclasses — including decorator options, field defaults, __post_init__ validation, computed properties, inheritance, and deciding when dataclasses are the right tool versus Pydantic v2 or TypedDict.
---

# Python Dataclasses

Expert guidance for writing clean, idiomatic Python dataclasses using the stdlib `dataclasses` module (Python 3.10+).

## When to Use Dataclasses

**Use `@dataclass` when:**
- Grouping related data produced entirely by your own code (no external input)
- You need zero external dependencies (stdlib only)
- You need value objects, domain entities, DTOs, or config holders
- You want `__repr__`, `__eq__`, and optionally `__hash__`/ordering automatically

**Don't use `@dataclass` when:**
- Data arrives from JSON, HTTP, environment variables, or files → use **Pydantic v2**
- You need automatic type coercion or rich validation error messages → use **Pydantic v2**
- You only need a dict shape for static type checking, never instantiated → use **TypedDict**
- You need JSON schema / OpenAPI generation → use **Pydantic v2**

**Decision flowchart:**

```
External input? (HTTP, file, env, DB)
  └─ Yes → Need coercion or rich errors? → Pydantic v2
           └─ No (strict types only)    → Pydantic v2 (strict mode) or msgspec

  └─ No (internal data only)
       ├─ Type checking hint only, no instance? → TypedDict
       ├─ Need runtime validation at construction? → @dataclass + __post_init__
       └─ Just grouping fields, no validation?   → @dataclass (clean, fast, stdlib)
```

For a full comparison matrix see **python-pydantic-v2** skill → `references/pydantic-vs-alternatives.md`.

---

## Decorator Options

```python
@dataclass(
    init=True,        # generate __init__ (default True)
    repr=True,        # generate __repr__ (default True)
    eq=True,          # generate __eq__ based on fields (default True)
    order=False,      # generate __lt__, __le__, __gt__, __ge__ (default False)
    frozen=False,     # make immutable — raises FrozenInstanceError on assignment
    unsafe_hash=False,# generate __hash__ even when eq=True and not frozen
    slots=True,       # use __slots__ for memory/speed improvement (Python 3.10+)
    kw_only=False,    # all fields keyword-only in __init__ (Python 3.10+)
    match_args=True,  # generate __match_args__ for pattern matching (Python 3.10+)
)
```

**Common combinations:**

| Intent | Options |
|--------|---------|
| Simple mutable container | `@dataclass` (all defaults) |
| Immutable value object | `@dataclass(frozen=True)` |
| Sortable value object | `@dataclass(frozen=True, order=True)` |
| Memory-efficient (no `__dict__`) | `@dataclass(slots=True)` |
| Enforce keyword-only construction | `@dataclass(kw_only=True)` |
| Hashable mutable (use carefully) | `@dataclass(eq=True, unsafe_hash=True)` |

---

## Examples: Simple to Complex

### 1. Basic Container

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float

p = Point(1.0, 2.5)
print(p)         # Point(x=1.0, y=2.5)
p.x = 3.0        # mutable by default
```

### 2. With Defaults and `field()`

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class LogEntry:
    message: str
    level: str = "INFO"                            # simple scalar default
    tags: list[str] = field(default_factory=list)  # REQUIRED for mutable defaults
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str | None = None

entry = LogEntry(message="Service started", tags=["boot", "init"])
```

> **Rule:** Never use a mutable object (`[]`, `{}`, `set()`) as a bare default.
> Always use `field(default_factory=...)` instead.

### 3. Frozen (Immutable) Value Object

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

    def to_hex(self) -> str:
        return f'#{self.r:02X}{self.g:02X}{self.b:02X}'

RED = Color(255, 0, 0)
# RED.r = 128  → raises FrozenInstanceError

# Frozen dataclasses are hashable and usable as dict keys / set members
palette: set[Color] = {Color(255, 0, 0), Color(0, 255, 0)}
```

### 4. Validation with `__post_init__`

```python
from dataclasses import dataclass, field
from datetime import date

@dataclass
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError(
                f"end ({self.end}) must be after start ({self.start})"
            )

@dataclass
class Employee:
    name: str
    department: str
    salary: float
    years_experience: int = 0

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise ValueError("name must not be blank")
        if self.salary < 0:
            raise ValueError(f"salary must be non-negative, got {self.salary}")
        if self.years_experience < 0:
            raise ValueError("years_experience cannot be negative")
```

> `__post_init__` runs **after** `__init__` finishes, so all fields are already set. Use it for cross-field checks and normalization. For complex validation with rich error messages, prefer Pydantic v2.

### 5. Computed Properties

```python
from dataclasses import dataclass
import math

@dataclass
class Circle:
    radius: float

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError(f"radius must be positive, got {self.radius}")

    @property
    def area(self) -> float:
        return math.pi * self.radius ** 2

    @property
    def circumference(self) -> float:
        return 2 * math.pi * self.radius

    @property
    def diameter(self) -> float:
        return self.radius * 2

c = Circle(5.0)
print(c.area)          # 78.539...
print(c)               # Circle(radius=5.0)  ← properties NOT in __repr__ by default
```

### 6. `field()` with `repr`, `compare`, `hash` Control

```python
from dataclasses import dataclass, field
import secrets

@dataclass
class ApiKey:
    name: str
    _secret: str = field(default_factory=lambda: secrets.token_urlsafe(32),
                         repr=False,    # excluded from __repr__ (security)
                         compare=False) # excluded from __eq__ / __hash__

key = ApiKey(name="prod-key")
print(key)  # ApiKey(name='prod-key')  ← secret not exposed
```

### 7. Using `slots=True` for Performance

```python
from dataclasses import dataclass

@dataclass(slots=True)
class Vector3:
    x: float
    y: float
    z: float

    def magnitude(self) -> float:
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def dot(self, other: 'Vector3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z
```

`slots=True` generates `__slots__` automatically (Python 3.10+). Benefits:
- ~30% less memory per instance
- Faster attribute access
- Prevents accidental creation of arbitrary attributes

### 8. `InitVar` — Constructor-Only Parameters

```python
from dataclasses import dataclass, field, InitVar

@dataclass
class HashedPassword:
    username: str
    hashed: str = field(init=False, repr=False)
    raw_password: InitVar[str]       # passed to __init__ but NOT stored as a field

    def __post_init__(self, raw_password: str) -> None:
        import hashlib
        if len(raw_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        self.hashed = hashlib.sha256(raw_password.encode()).hexdigest()

u = HashedPassword(username="alice", raw_password="s3cr3t!!")
# HashedPassword(username='alice')   ← raw_password and hashed hidden
```

### 9. `ClassVar` — Class-Level Constants

```python
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Config:
    VERSION: ClassVar[str] = "2.1.0"   # NOT included in __init__ or __repr__
    MAX_RETRIES: ClassVar[int] = 3

    host: str
    port: int = 8080
    debug: bool = False

# ClassVar fields are shared across all instances and excluded from __init__
cfg = Config(host="localhost")
print(Config.VERSION)   # "2.1.0"
```

### 10. Ordered and Sorted Value Objects

```python
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Version:
    major: int
    minor: int
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

versions = [Version(2, 1), Version(1, 0), Version(2, 0, 1)]
print(sorted(versions))
# [Version(major=1, minor=0, patch=0), Version(major=2, minor=0, patch=1), ...]
```

> `order=True` compares fields **in declaration order**. Put the most significant field first.

---

## Inheritance

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class BaseEntity:
    id: int
    created_at: datetime

@dataclass
class User(BaseEntity):
    name: str
    email: str

@dataclass
class AdminUser(User):
    permissions: list[str] = field(default_factory=list)
```

**Rules for dataclass inheritance:**
1. Parent fields always come before child fields in `__init__`.
2. **Fields with defaults must not precede fields without defaults** — this is a common ordering trap.
3. Frozen ↔ non-frozen inheritance is not allowed (`TypeError`).
4. Use `field(default=..., kw_only=True)` on parents to avoid ordering problems (Python 3.10+).

```python
# ❌ Breaks: parent has a default, child adds a required field
@dataclass
class Base:
    x: int = 0

@dataclass
class Child(Base):
    y: int       # TypeError: non-default follows default

# ✅ Fix with kw_only on the parent default field
@dataclass
class Base:
    x: int = field(default=0, kw_only=True)

@dataclass
class Child(Base):
    y: int       # Works — x is keyword-only, ordering no longer conflicts
```

---

## `replace()` — Immutable Updates

```python
from dataclasses import replace

@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug: bool = False

prod = Config(host="api.example.com", port=443)
dev  = replace(prod, host="localhost", port=8080, debug=True)
# Config(host='localhost', port=8080, debug=True)
```

`replace()` is the dataclass equivalent of Pydantic's `model_copy(update={...})`. Only the specified fields change; the rest are copied from the original.

---

## Anti-Patterns

### ❌ Mutable default values

```python
# BAD: all instances share the SAME list object
@dataclass
class Cart:
    items: list[str] = []   # raises ValueError at definition time

# GOOD
@dataclass
class Cart:
    items: list[str] = field(default_factory=list)
```

### ❌ Using `@dataclass` for external input without validation

```python
# BAD: no coercion — "42" stays a string, validator not called
@dataclass
class APIBody:
    user_id: int      # will silently accept str "42"
    amount: float

body = APIBody(user_id="42", amount="not-a-number")  # no error raised

# GOOD: use Pydantic v2 for external input
```

### ❌ Heavy business logic in `__post_init__`

```python
# BAD: dataclass constructor is reaching out to network/DB
@dataclass
class Order:
    product_id: int

    def __post_init__(self):
        self.product = db.get_product(self.product_id)  # ← side effect in constructor

# GOOD: keep __post_init__ for pure validation/normalization; load externally
@dataclass
class Order:
    product_id: int
    product: Product | None = field(default=None, init=False)

def load_order(product_id: int) -> Order:
    order = Order(product_id=product_id)
    order.product = db.get_product(product_id)
    return order
```

### ❌ Forgetting `frozen=True` breaks `order=True` intent

```python
# BAD: mutable but ordered — sorting is unstable if fields change after insertion
@dataclass(order=True)
class Priority:
    level: int    # if you mutate level, sorted collections become corrupted

# GOOD: combine order with frozen for safe use in sorted structures
@dataclass(frozen=True, order=True)
class Priority:
    level: int
```

### ❌ Overriding `__init__` entirely

```python
# BAD: defeats the purpose of @dataclass — you now own all initialization
@dataclass
class Bad:
    x: int
    y: int

    def __init__(self, x, y, extra):  # ← breaks @dataclass generated __init__
        self.x = x
        self.y = y

# GOOD: use InitVar for extra constructor params, keep generated __init__
@dataclass
class Good:
    x: int
    y: int
    extra: InitVar[str]

    def __post_init__(self, extra: str) -> None:
        self._extra = extra
```

### ❌ Deep nesting of mutable dataclasses without copy semantics

```python
# BAD: shallow copy shares inner lists
from dataclasses import replace

@dataclass
class Profile:
    tags: list[str] = field(default_factory=list)

p1 = Profile(tags=["python"])
p2 = replace(p1)           # p2.tags IS p1.tags — same object!
p2.tags.append("dataclass")
print(p1.tags)              # ['python', 'dataclass'] ← corrupted

# GOOD: deep copy mutable fields explicitly
import copy
p2 = replace(p1, tags=list(p1.tags))   # or copy.deepcopy(p1)
```

---

## Quick Reference

| Task | Code |
|------|------|
| Basic dataclass | `@dataclass` |
| Immutable | `@dataclass(frozen=True)` |
| Sortable immutable | `@dataclass(frozen=True, order=True)` |
| Memory efficient | `@dataclass(slots=True)` |
| Keyword-only init | `@dataclass(kw_only=True)` |
| Mutable default | `field(default_factory=list)` |
| Hide from repr | `field(repr=False)` |
| Exclude from comparison | `field(compare=False)` |
| Constructor-only param | `InitVar[type]` + `__post_init__` |
| Class-level constant | `ClassVar[type]` |
| Computed value | `@property` |
| Validate fields | `__post_init__(self) → None` |
| Immutable update | `replace(instance, field=value)` |
| Convert to dict | `dataclasses.asdict(instance)` |
| Convert to tuple | `dataclasses.astuple(instance)` |
| Inspect fields | `dataclasses.fields(instance)` |
| Check if dataclass | `dataclasses.is_dataclass(obj)` |

## Reference Files

- [dataclass-patterns.md](references/dataclass-patterns.md) — Generic dataclasses, abstract dataclasses, `__init_subclass__`, factory patterns, protocol compliance, pattern matching
- [stdlib-integration.md](references/stdlib-integration.md) — `asdict`, `astuple`, `replace`, JSON serialization, `copy`/`pickle`, `functools`, `__slots__` interactions
