# Pydantic v2 vs Alternatives

## Decision Matrix

| Criterion | Pydantic v2 | `dataclass` | `TypedDict` | `attrs` | `msgspec` |
|-----------|-------------|-------------|-------------|---------|-----------|
| Runtime validation | ✅ Full | ⚠️ Manual only | ❌ None | ✅ Optional | ✅ Full |
| Type coercion | ✅ Automatic | ❌ None | ❌ None | ❌ None | ✅ Strict |
| JSON serialization | ✅ Built-in fast | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | ✅ Built-in fastest |
| JSON schema | ✅ OpenAPI-ready | ❌ None | ⚠️ Plugin needed | ⚠️ Plugin needed | ✅ Basic |
| FastAPI integration | ✅ Native | ⚠️ Basic | ❌ No instance | ✅ Via adapter | ⚠️ Non-standard |
| Settings from env | ✅ `pydantic-settings` | ❌ No | ❌ No | ❌ No | ❌ No |
| Stdlib dependency | ❌ External | ✅ stdlib | ✅ stdlib | ❌ External | ❌ External |
| Performance (parse) | ✅ Very fast (Rust) | N/A | N/A | Fast | ✅ Fastest |
| Inheritance | ✅ Full | ✅ Full | ✅ Functional | ✅ Full | Limited |
| Discriminated unions | ✅ Native | ❌ Manual | ❌ Manual | ❌ Manual | ✅ Basic |
| Computed fields | ✅ `@computed_field` | ✅ `@property` | ❌ | ✅ | ❌ |
| Immutability | ✅ `frozen=True` | ✅ `frozen=True` | N/A | ✅ | ✅ |
| IDE autocompletion | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Pydantic v2 vs Python `dataclass`

### When to pick `dataclass`

```python
# ✅ Correct: dataclass for internal data grouping, no external input
from dataclasses import dataclass, field

@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
```

Use `dataclass` when:
- All data is created internally by your code
- No external input to validate (no JSON, no user input, no env vars)
- Zero-dependency requirement (stdlib only)
- Frozen/immutable value objects with no coercion needed: `@dataclass(frozen=True)`

### When to pick Pydantic

```python
# ✅ Correct: Pydantic for external input
class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str
    age: int = Field(ge=0, le=150)
    role: Literal['admin', 'user', 'moderator'] = 'user'
```

Use Pydantic when:
- Data arrives from HTTP requests, files, databases, or environment variables
- You need coercion (e.g., string `"42"` → `int 42`)
- You need JSON schema for API docs or validation contracts
- You need `BaseSettings` for configuration management
- You want rich error messages with field paths

### Pydantic-decorated dataclasses (hybrid)

Pydantic can wrap standard dataclasses to add validation while keeping dataclass behavior:

```python
from pydantic.dataclasses import dataclass  # ← Pydantic's version

@dataclass
class Config:
    host: str
    port: int = 8080
    debug: bool = False

# Validates on construction, works as a dataclass
cfg = Config(host='localhost', port='8080')  # port coerced str→int
```

Useful for migrating existing dataclass code to Pydantic validation without changing the class structure.

---

## Pydantic v2 vs `TypedDict`

```python
from typing import TypedDict

# TypedDict — no runtime
class UserDict(TypedDict):
    name: str
    email: str
    age: int
```

`TypedDict` is purely a type-checker hint. There is **no runtime enforcement**:

```python
d: UserDict = {'name': 'Alice', 'email': 'invalid', 'age': 'not-a-number'}
# No error raised at runtime — mypy/pyright will warn in static analysis only
```

**Use `TypedDict` when:**
- You're describing the shape of an existing `dict` (e.g., from `json.load`, `**kwargs`)
- You need static analysis only; no instances are created
- Working with APIs that return raw dicts and you don't control them

**Never use `TypedDict` for:**
- Validating external input
- FastAPI request/response models
- Any scenario where corrupt data could cause downstream errors

---

## Pydantic v2 vs `attrs`

`attrs` is the closest library to Pydantic in design philosophy but without the Rust-backed performance.

```python
import attr

@attr.s(auto_attribs=True)
class Point:
    x: float = attr.ib(validator=attr.validators.instance_of(float))
    y: float = attr.ib(validator=attr.validators.instance_of(float))
```

**`attrs` advantages:**
- Very mature, stable API
- More control over `__init__` generation and slots
- Works well with classes that need complex `__init__` logic

**Pydantic v2 advantages over attrs:**
- Automatic JSON coercion and serialization
- Native JSON schema generation
- `pydantic-settings` integration
- Significantly better FastAPI/Starlette integration
- Type-narrowing in validator callbacks is more natural

---

## Pydantic v2 vs `msgspec`

`msgspec` is a high-performance serialization library with validation, written in C.

**Choose `msgspec` when:**
- Throughput is the absolute top priority (it's ~30-50% faster than Pydantic v2 on benchmarks)
- You need MessagePack support
- Strict parsing only (no coercion: `"42"` does NOT become `42`)

**Choose Pydantic v2 when:**
- Using FastAPI (native integration, no adapter needed)
- You need coercion / leniency in parsing
- You need `pydantic-settings`
- Discriminated unions, computed fields, or custom validators are required
- JSON schema quality matters (Pydantic produces richer OpenAPI schemas)

---

## Side-by-Side: Same Model in Each Tool

```python
# Pydantic v2
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)
    quantity: int = Field(ge=0, default=0)

# Python dataclass (no validation)
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    price: float
    quantity: int = 0
    def __post_init__(self):
        if len(self.name) < 1: raise ValueError(...)    # manual only
        if self.price <= 0: raise ValueError(...)

# TypedDict (no instances, no validation)
from typing import TypedDict

class Product(TypedDict):
    name: str
    price: float
    quantity: int

# attrs
import attr

@attr.s(auto_attribs=True)
class Product:
    name: str = attr.ib(validator=attr.validators.min_len(1))
    price: float = attr.ib(validator=attr.validators.gt(0))
    quantity: int = attr.ib(default=0, validator=attr.validators.ge(0))

# msgspec
import msgspec

class Product(msgspec.Struct):
    name: str
    price: float
    quantity: int = 0
    # No native constraint annotations; use @msgspec.json.decode with hooks
```

---

## Quick Decision Flowchart

```
External input? (HTTP, file, env, DB)  ─Yes─→  Need coercion? ─Yes─→  Pydantic v2
                                                              └─No──→  msgspec (max perf) or Pydantic v2
          │
         No
          │
          ↓
  Need type checking only?  ─Yes─→  TypedDict
          │
         No
          │
          ↓
  Need validation at runtime?  ─Yes─→  @dataclass + __post_init__ (if simple)
                                        or Pydantic dataclass
          │
         No
          │
          ↓
  Internal grouping only  ─→  @dataclass (stdlib, clean, fast)
```
