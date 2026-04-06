# Pydantic v2 vs Alternatives

## Decision Matrix

| Criterion | Pydantic v2 | `dataclass` | `TypedDict` | `attrs` | `msgspec` |
|-----------|-------------|-------------|-------------|---------|-----------|
| Runtime validation | ✅ Full | ⚠️ Manual only | ❌ None (plain `TypedDict`) | ✅ Optional | ⚠️ On decode/convert paths |
| Type coercion | ✅ Automatic by default | ❌ None | ❌ None | ⚠️ Via converters or validators, not automatic | ⚠️ Strict by default, optional lax mode |
| JSON serialization | ✅ Built-in fast | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | ✅ Built-in, very fast |
| JSON schema | ✅ OpenAPI-ready | ❌ None | ⚠️ Plugin needed | ⚠️ Plugin needed | ✅ Basic |
| FastAPI integration | ✅ Native | ⚠️ Basic | ❌ No instance | ⚠️ Custom adapter only / not native | ⚠️ Non-standard |
| Settings from env | ✅ `pydantic-settings` | ❌ No | ❌ No | ❌ No | ❌ No |
| Stdlib dependency | ❌ External | ✅ stdlib | ✅ stdlib | ❌ External | ❌ External |
| Performance (parse) | ✅ Very fast (Rust) | N/A | N/A | Fast | ✅ Often fastest in benchmarks |
| Inheritance | ✅ Full | ✅ Full | ✅ Functional | ✅ Full | ⚠️ Supported, but less flexible |
| Discriminated unions | ✅ Native | ❌ Manual | ❌ Manual | ❌ Manual | ✅ Basic |
| Computed fields | ✅ `@computed_field` | ⚠️ Manual `@property` | ❌ | ⚠️ Manual property | ❌ |
| Immutability | ⚠️ Faux-immutable via `frozen=True` | ✅ `frozen=True` | N/A | ✅ | ✅ |
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
from typing import Literal

from pydantic import BaseModel, Field

class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1)
    email: str
    age: int = Field(ge=0, le=150)
    role: Literal['admin', 'user', 'moderator'] = 'user'
```

This keeps the example dependency-free. Plain `str` does not validate email or URL shape; use `EmailStr`, URL types, or explicit validators when boundary semantics require that.

Use Pydantic when:
- Data arrives from HTTP requests, files, databases, or environment variables
- You need coercion (e.g., string `"42"` → `int 42`)
- You need JSON schema for API docs or validation contracts
- You need `BaseSettings` via `pydantic-settings` for configuration management
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

When you need `model_dump()`, `model_json_schema()`, or other `BaseModel` methods directly on the type, prefer `BaseModel` instead of a Pydantic dataclass.

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
from typing import TypedDict

class UserDict(TypedDict):
    name: str
    email: str
    age: int

d: UserDict = {'name': 'Alice', 'email': 'invalid', 'age': 'not-a-number'}
# No error raised at runtime — mypy/pyright will warn in static analysis only
```

**Use `TypedDict` when:**
- You're describing the shape of an existing `dict` (e.g., from `json.load`, `**kwargs`)
- You need static analysis only; no instances are created
- Working with APIs that return raw dicts and you don't control them, when you only need static typing; add `TypeAdapter` if runtime validation is required

If you want to keep dict-shaped data but add runtime checks, validate the `TypedDict` with `TypeAdapter`:

```python
from typing_extensions import TypedDict

from pydantic import TypeAdapter

class UserDict(TypedDict):
    name: str
    email: str
    age: int

adapter = TypeAdapter(UserDict)
user = adapter.validate_python({'name': 'Alice', 'email': 'a@example.com', 'age': '42'})
```

For `TypeAdapter(TypedDict)` on Python 3.10 and 3.11, prefer `typing_extensions.TypedDict`; `typing.TypedDict` becomes safe for this use on Python 3.12+.

**Avoid `TypedDict` for:**
- Validating external input without `TypeAdapter` or another runtime-validation layer
- FastAPI request/response models
- Any scenario where corrupt data could cause downstream errors

---

## Pydantic v2 vs `attrs`

`attrs` is the closest library to Pydantic in design philosophy, but validation and coercion are more manual and schema tooling is less integrated.

```python
import attr

@attr.s(auto_attribs=True)
class Point:
    x: float = attr.ib(validator=attr.validators.instance_of(float))
    y: float = attr.ib(validator=attr.validators.instance_of(float))
```

`instance_of(float)` rejects `int` values. Use converters such as `converter=float` if you want attrs to normalize broader numeric input.

**`attrs` advantages:**
- Very mature, stable API
- More control over `__init__` generation and slots
- Works well with classes that need complex `__init__` logic
- Converters and validators can provide targeted runtime normalization when you want it

**Pydantic v2 advantages over attrs:**
- Automatic JSON coercion and serialization
- Native JSON schema generation
- `pydantic-settings` integration
- Significantly better FastAPI/Starlette integration
- Type-narrowing in validator callbacks is more natural

---

## Pydantic v2 vs `msgspec`

`msgspec` is a high-performance serialization library written in C with validation on decode/convert paths.

Direct `msgspec.Struct(...)` construction does not validate or coerce fields the way `msgspec.json.decode(...)`, `msgspec.convert(...)`, or Pydantic model construction does.

**Choose `msgspec` when:**
- Throughput is the absolute top priority and you are willing to benchmark on your workload
- You need MessagePack support
- Strict-by-default decode/convert behavior is desirable, with optional lax conversion via `strict=False`
- `Annotated[..., msgspec.Meta(...)]` constraints are enough for your schema

For strict request or config validation, remember that unknown fields are ignored unless you opt in:

```python
import msgspec

class StrictPayload(msgspec.Struct, forbid_unknown_fields=True):
    name: str
```

**Choose Pydantic v2 when:**
- Using FastAPI (native integration, no adapter needed)
- You need coercion / leniency in parsing
- You need `pydantic-settings`
- Discriminated unions, computed fields, or custom validators are required
- JSON schema quality matters (Pydantic produces richer OpenAPI schemas)

---

## Side-by-Side: Same Model in Each Tool

Comparison only. These are separate examples, not one runnable script.

```python
# Pydantic v2
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1)
    weight: float = Field(gt=0)
    quantity: int = Field(ge=0, default=0)

# Python dataclass (manual validation in __post_init__)
from dataclasses import dataclass

@dataclass
class Product:
    name: str
    weight: float
    quantity: int = 0

    def __post_init__(self):
        if len(self.name) < 1:
            raise ValueError('name must not be empty')
        if self.weight <= 0:
            raise ValueError('weight must be positive')

# TypedDict (no instances, no validation)
from typing import TypedDict

class Product(TypedDict):
    name: str
    weight: float
    quantity: int

# attrs
import attr

@attr.s(auto_attribs=True)
class Product:
    name: str = attr.ib(validator=attr.validators.min_len(1))
    weight: float = attr.ib(validator=attr.validators.gt(0))
    quantity: int = attr.ib(default=0, validator=attr.validators.ge(0))

# msgspec
from typing import Annotated

import msgspec

class Product(msgspec.Struct):
    name: Annotated[str, msgspec.Meta(min_length=1)]
    weight: Annotated[float, msgspec.Meta(gt=0)]
    quantity: Annotated[int, msgspec.Meta(ge=0)] = 0

# Validation happens on decode/convert paths, not plain Struct(...) construction.
```

---

## Quick Decision Flowchart

Common-case shortcut, not an exhaustive decision tree.

```
External input? (HTTP, file, env, DB)  ─Yes─→  Need named model/schema/settings/validators? ─Yes─→  Pydantic v2
                                               │
                                              No
                                               │
                                               ↓
                   Need bare list/dict/union validation only? ─Yes─→  TypeAdapter
                                               │
                                              No
                                               │
                                               ↓
                         Need benchmark-driven, feature-light decode? ─Yes─→  msgspec (decode/convert paths)
                                               │
                                              No
                                               │
                                               ↓
                                              Pydantic v2
          │
         No
          │
          ↓
    Need type checking only for dict-shaped data?  ─Yes─→  TypedDict
          │
         No
          │
          ↓
    Need validation at runtime?  ─Yes─→  Need model features/schema/nested parsing? ─Yes─→  BaseModel
                                                                                                                     │
                                                                                                                    No
                                                                                                                     │
                                                                                                                     ↓
                                          Need validated dict/list/union only? ─Yes─→  TypeAdapter
                                                                                                                     │
                                                                                                                    No
                                                                                                                     │
                                                                                                                     ↓
                                                            Want Pydantic validation/coercion without full BaseModel? ─Yes─→  pydantic.dataclasses.dataclass
                                                                                                                     │
                                                                                                                    No
                                                                                                                     │
                                                                                                                     ↓
                                                                                                @dataclass + __post_init__ for internal, already-typed data (if simple)
          │
         No
          │
          ↓
  Internal grouping only  ─→  @dataclass (stdlib, clean, fast)
```
