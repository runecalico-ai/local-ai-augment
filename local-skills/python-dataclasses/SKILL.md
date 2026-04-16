---
name: python-dataclasses
description: Use when choosing between dataclasses, Pydantic v2, TypedDict, or msgspec, or when dataclass code needs help with mutable defaults, default_factory, __post_init__, InitVar or ClassVar, frozen, slots, inheritance, replace or asdict behavior, or pattern matching.
---

# Python Dataclasses

Expert guidance for writing clean, idiomatic Python dataclasses using the stdlib `dataclasses` module (Python 3.10+).

## When to Use Dataclasses

**Use `@dataclass` when:**
- Grouping related internal data with known Python types
- The values are created by your code, or already validated and normalized before they reach this class
- You need zero external dependencies (stdlib only)
- You need value objects, DTOs, config holders, or simple internal records
- You want `__repr__`, `__eq__`, and optionally `__hash__`/ordering automatically

**Don't use `@dataclass` when:**
- You are validating untrusted or loosely typed boundary data from JSON, HTTP, environment variables, files, or similar sources, and a plain dataclass would be the only validation or coercion layer → prefer **Pydantic v2** or validate and coerce before constructing the dataclass
- You need automatic type coercion or rich validation error messages → use **Pydantic v2**
- You need plain dict-shaped data with a known structure for static type checking → use **TypedDict**
- You need JSON schema / OpenAPI generation → use **Pydantic v2**

**Decision flowchart:**

```
Is this untrusted or loosely typed boundary data?
  (HTTP/JSON/env/file input before validation)
  └─ Yes
      ├─ Need coercion, rich errors, settings, or schema generation? → Pydantic v2
      └─ Need very fast structured decoding or encoding with strict schemas? → consider `msgspec`

  └─ No
      (already validated or normalized, or purely internal data)
       ├─ Need plain dict-shaped data with a known structure for static type checking? → TypedDict
       ├─ Need simple invariant checks on already-validated internal data? → @dataclass + __post_init__
       └─ Just grouping fields, no validation?   → @dataclass (clean, fast, stdlib)
```

For a fuller comparison, see the **python-pydantic-v2** skill.

---

## Decorator Options

```python
@dataclass(
    init=True,        # generate __init__ (default True)
    repr=True,        # generate __repr__ (default True)
    eq=True,          # generate __eq__ based on fields (default True)
    order=False,      # generate __lt__, __le__, __gt__, __ge__ (default False)
    frozen=False,     # block attribute rebinding — raises FrozenInstanceError on assignment
    unsafe_hash=False,# generate __hash__ even when eq=True and not frozen; only use when hashed fields are hashable and treated as effectively immutable after creation
    slots=False,      # generate __slots__ for lower overhead when enabled (default False, Python 3.10+)
    kw_only=False,    # all fields keyword-only in __init__ (Python 3.10+)
    match_args=True,  # generate __match_args__ from non-keyword-only init fields (Python 3.10+)
)
```

**Common combinations:**

| Intent | Options |
|--------|---------|
| Simple mutable container | `@dataclass` (all defaults) |
| Read-only value object | `@dataclass(frozen=True)` |
| Sortable value object | `@dataclass(frozen=True, order=True)` |
| Often memory-efficient (when no base class provides `__dict__`) | `@dataclass(slots=True)` |
| Weakref-able slotted instances | `@dataclass(slots=True, weakref_slot=True)` (Python 3.11+) |
| Enforce keyword-only construction | `@dataclass(kw_only=True)` |
| Mutable class with generated `__hash__` (only when hashed fields are hashable and effectively immutable after creation) | `@dataclass(eq=True, unsafe_hash=True)` |

`order=True` requires `eq=True`, and generated equality and ordering compare only instances of the identical dataclass type.

---

## Canonical Patterns

### Mutable Defaults

```python
from dataclasses import dataclass, field

@dataclass
class LogEntry:
    message: str
    tags: list[str] = field(default_factory=list)
```

Use `field(default_factory=...)` for any per-instance mutable state.

### Validation And Normalization

```python
from dataclasses import dataclass
from datetime import date

@dataclass
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end <= self.start:
            raise ValueError("end must be after start")
```

Use `__post_init__` for simple invariants on already-typed internal data.

### Constructor-Only Inputs

```python
from dataclasses import InitVar, dataclass, field

@dataclass
class UserRecord:
    username: str
    email: str = field(init=False)
    raw_email: InitVar[str]

    def __post_init__(self, raw_email: str) -> None:
        normalized_email = raw_email.strip().lower()
        if "@" not in normalized_email:
            raise ValueError("email must contain '@'")
        self.email = normalized_email
```

Declare derived stored fields up front. For frozen classes, assign them with `object.__setattr__`.

### Slots

```python
from dataclasses import dataclass

@dataclass(slots=True)
class Vector3:
    x: float
    y: float
    z: float
```

Use `slots=True` as an opt-in performance choice, not the default baseline. On Python 3.11+, add `weakref_slot=True` if instances must support weak references.

`functools.cached_property` requires an instance `__dict__`, so it will not work on a slotted dataclass unless a base class provides one. On Python 3.10+, zero-argument `super()` can also fail in `slots=True` classes because the decorator returns a new class object.

See the reference files for more worked examples covering frozen value objects, `ClassVar`, ordering, generics, serialization, `replace()`, and pattern matching.

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
1. Parent fields are added before child fields, but keyword-only parameters are moved after all non-keyword-only parameters in the generated `__init__`.
2. **Fields with defaults must not precede fields without defaults** — this is a common ordering trap.
3. Frozen ↔ non-frozen inheritance is not allowed (`TypeError`).
4. Use `field(default=..., kw_only=True)` on parents to avoid ordering problems (Python 3.10+).
5. `__post_init__` is not chained automatically; if a base dataclass defines it, a subclass override should call `super().__post_init__()` when base validation or normalization still needs to run.
6. A generated dataclass `__init__` does not call a non-dataclass base `__init__`; call it explicitly from `__post_init__` or a custom `__init__` when that base initialization must run.

```python
from dataclasses import dataclass, field

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
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Config:
    host: str
    port: int
    debug: bool = False

prod = Config(host="api.example.com", port=443)
dev  = replace(prod, host="localhost", port=8080, debug=True)
# Config(host='localhost', port=8080, debug=True)
```

`replace()` reconstructs a new dataclass instance by calling the class `__init__` again with the current `init=True` field values plus any overrides you pass. `__post_init__` reruns when the generated dataclass `__init__` is used, or when a custom `__init__` calls it. Treat this as reconstruction, not cloning: nested mutable objects remain shared unless you copy them explicitly, derived `init=False` fields are recomputed in `__post_init__` if that code sets them, required `InitVar` values must also be supplied again because they are not stored on the original instance and cannot be recovered from it, and `init=False` fields cannot be passed in `changes`.

If the instance carries derived `init=False` state or nested mutables, copy or rebuild those values explicitly instead of assuming `replace()` preserves full object state.

---

## Common Mistakes

- Bare mutable defaults such as `[]`, `{}`, or shared state objects: use `field(default_factory=...)`.
- Treating type hints as runtime validation: stdlib dataclasses do not coerce or validate automatically.
- Putting network, filesystem, or service lookups in `__post_init__`: keep it for pure validation and normalization.
- Assuming `replace()` is a deep clone: it reconstructs and can still share nested mutables.
- Using `unsafe_hash=True` on mutable or unhashable state: only do this when hashed fields are effectively immutable and hashable.

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
| Convert to dict | `dataclasses.asdict(instance)` (recursive; see caveats) |
| Convert to tuple | `dataclasses.astuple(instance)` |
| Inspect fields | `dataclasses.fields(instance)` |
| Check if dataclass | `dataclasses.is_dataclass(obj)` |

## Reference Files

- [dataclass-patterns.md](references/dataclass-patterns.md) — Generic dataclasses, abstract dataclasses, `__init_subclass__`, factory patterns, protocol compliance, pattern matching
- [stdlib-integration.md](references/stdlib-integration.md) — `asdict`, `astuple`, `replace`, JSON serialization, `copy`/`pickle`, `functools`, `__slots__` interactions
