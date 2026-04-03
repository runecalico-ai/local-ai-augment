# Dataclasses — stdlib Integration

## `dataclasses` Module Utilities

```python
import dataclasses

# Inspect all fields (returns tuple of Field objects)
dataclasses.fields(instance_or_class)

# Convert to dict (recursive — nested dataclasses, lists, tuples, and dicts are traversed; other leaf objects are copied with copy.deepcopy())
dataclasses.asdict(instance)

# Convert to tuple (recursive — field order matches declaration order; nested dataclasses, lists, tuples, and dicts are traversed; other leaf objects are copied with copy.deepcopy())
dataclasses.astuple(instance)

# Reconstruct via __init__ with field overrides
dataclasses.replace(instance, field_name=new_value, ...)

# Check if an object or class is a dataclass
dataclasses.is_dataclass(obj)   # True for dataclass instances AND classes

# Access a specific Field object
dataclasses.fields(MyClass)[0]
# Field(name='x', type=float, default=MISSING, ...)
```

---

## `asdict` and `astuple` — Deep Dive

```python
from dataclasses import dataclass, asdict, astuple

@dataclass
class Address:
    street: str
    city: str

@dataclass
class Person:
    name: str
    age: int
    address: Address

alice = Person("Alice", 30, Address("123 Main St", "Portland"))

# asdict: fully recursive
asdict(alice)
# {
#   'name': 'Alice',
#   'age': 30,
#   'address': {'street': '123 Main St', 'city': 'Portland'}
# }

# astuple: fully recursive, positional
astuple(alice)
# ('Alice', 30, ('123 Main St', 'Portland'))
```

**Caveats:**
- `asdict` and `astuple` recurse into nested dataclasses, lists, tuples, and dicts.
- Other leaf objects are copied with `copy.deepcopy()`, so object identity is not preserved in the result.
- That `deepcopy` step can also be slow or fail for non-copyable leaf objects.
- `asdict` and `astuple` are not cycle-safe; use them for tree-shaped value objects, not cyclic object graphs.
- If you need a shallow copy, use a `fields()`-based workaround instead.
- Does **not** call `to_dict()` methods — it inspects fields directly.
- Fields with `repr=False` or `compare=False` are still included in `asdict` output.
- There is no built-in exclude parameter for stdlib dataclass fields; filter manually:

```python
import dataclasses

# Shallow-copy workarounds that preserve existing object identity
shallow_dict = {f.name: getattr(instance, f.name) for f in dataclasses.fields(instance)}
shallow_tuple = tuple(getattr(instance, f.name) for f in dataclasses.fields(instance))
```

```python
import dataclasses
from dataclasses import dataclass, field

# Manually exclude sensitive fields
def safe_dict(instance) -> dict:
    return {
        f.name: getattr(instance, f.name)
        for f in dataclasses.fields(instance)
        if f.metadata.get('public', True)
    }

# Mark fields with metadata
@dataclass
class User:
    name: str
    email: str
    password_hash: str = field(metadata={'public': False})
```

---

## JSON Serialization

The patterns below assume trusted or already-validated data. For untrusted JSON, HTTP, file, or environment-variable input, do not rely on plain dataclasses as the only validation or coercion layer; validate first or prefer Pydantic v2.

Dataclasses have no built-in JSON support. Use one of these patterns:

### Pattern 1: `asdict` + `json.dumps` (simple, no custom types)

```python
import json
from dataclasses import dataclass, asdict

@dataclass
class Config:
    host: str
    port: int
    debug: bool = False

cfg = Config(host="localhost", port=8080)
json.dumps(asdict(cfg))
# '{"host": "localhost", "port": 8080, "debug": false}'
```

### Pattern 2: Custom `JSONEncoder` (handles `datetime`, enums, custom types)

```python
import json
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
import dataclasses

class DataclassEncoder(json.JSONEncoder):
    def default(self, obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

@dataclass
class Event:
    name: str
    date: datetime
    capacity: int

event = Event(name="PyCon", date=datetime(2026, 5, 1, 9, 0), capacity=500)
json.dumps(event, cls=DataclassEncoder)
# '{"name": "PyCon", "date": "2026-05-01T09:00:00", "capacity": 500}'
```

### Pattern 3: `to_dict` / `from_dict` methods on the class (explicit, useful for small stable models)

```python
from dataclasses import dataclass, field
import json
from datetime import datetime, timezone

@dataclass
class Product:
    id: int
    name: str
    price: float
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        return cls(
            id=data['id'],
            name=data['name'],
            price=data['price'],
            created_at=datetime.fromisoformat(data['created_at']),
        )

p = Product(1, "Widget", 9.99)
serialized = json.dumps(p.to_dict())
restored = Product.from_dict(json.loads(serialized))
```

For complex or boundary-facing models, prefer a dedicated validation or serialization layer instead of hand-rolling every conversion path.

### Pattern 4: Use `dataclasses-json` library (third-party, low boilerplate)

```python
# pip install dataclasses-json
from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class User:
    id: int
    name: str
    email: str

u = User(1, "Alice", "alice@example.com")
u.to_json()              # '{"id": 1, "name": "Alice", "email": "alice@example.com"}'
User.from_json('...')    # round-trip
```

Use this style for trusted internal serialization round-trips, not as a replacement for validation at untrusted boundaries.

---

## `copy` and `deepcopy`

```python
import copy
from dataclasses import dataclass, field, replace

@dataclass
class Node:
    value: int
    children: list['Node'] = field(default_factory=list)

root = Node(1, [Node(2), Node(3)])

# Shallow copy — children list is SHARED
shallow = copy.copy(root)
shallow.children.append(Node(4))
print(len(root.children))   # 3 → ⚠️ root was mutated!

# Deep copy — fully independent
deep = copy.deepcopy(root)
deep.children.append(Node(5))
print(len(root.children))   # 3 → ✅ root unchanged

# replace() reconstructs through __init__; __post_init__ reruns when the generated dataclass __init__ is used, or when a custom __init__ calls it; nested mutables remain shared unless copied
updated = replace(root, value=99)
assert updated.children is root.children   # same list object
```

**Rule:** Treat `replace()` as reconstruction, not cloning. It calls the class `__init__` again, so `__post_init__` reruns when the generated dataclass `__init__` is used, or when a custom `__init__` calls it; nested mutable fields remain shared unless you copy them explicitly, derived `init=False` fields are recomputed there if that code sets them, `init=False` fields cannot be passed in `changes`, and required `InitVar` values must still be supplied because they are not stored on the original instance and cannot be recovered from it.

Use `replace()` for value-like dataclasses with immutable field values. Use `copy.deepcopy()` when mutability at any depth is a concern.

---

## `pickle` Compatibility

Dataclass instances usually work with pickle without extra code when the class is importable and all field values are themselves pickleable:

```python
import pickle
from dataclasses import dataclass

@dataclass
class ModelWeights:
    layer_name: str
    weights: list[float]

w = ModelWeights("dense_1", [0.1, 0.2, 0.3])
serialized = pickle.dumps(w)
restored = pickle.loads(serialized)
assert restored == w
```

`slots=True` dataclasses follow the same rule on Python 3.10+; slots support does not change the normal pickle requirements.

Local or nested dataclasses, or instances that contain unpickleable values, can still fail to pickle or unpickle.

---

## `functools.total_ordering` (Alternative When You Need Custom Ordering)

Prefer `order=True` when tuple-like field ordering matches your semantics. Use `total_ordering` when you need custom `__lt__` logic and want the remaining comparison methods derived for you.

```python
from dataclasses import dataclass
from functools import total_ordering

@total_ordering
@dataclass
class SemVer:
    major: int
    minor: int
    patch: int
    pre: str = ""   # e.g. "alpha", "beta" — affects ordering

    def __lt__(self, other: 'SemVer') -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        self_key = (self.major, self.minor, self.patch, self.pre == '', self.pre)
        other_key = (other.major, other.minor, other.patch, other.pre == '', other.pre)
        return self_key < other_key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.pre) == \
               (other.major, other.minor, other.patch, other.pre)
```

---

## `typing.get_type_hints` — Runtime Field Type Inspection

```python
import typing
import dataclasses
from dataclasses import dataclass

@dataclass
class Config:
    host: str
    port: int
    debug: bool = False

# Get all field types (resolves string annotations)
hints = typing.get_type_hints(Config)
# {'host': <class 'str'>, 'port': <class 'int'>, 'debug': <class 'bool'>}

# Iterate fields with types
for f in dataclasses.fields(Config):
    print(f.name, hints[f.name], f.default)
# host <class 'str'> MISSING
# port <class 'int'> MISSING
# debug <class 'bool'> False
```

---

## Dataclass Field Metadata — Custom Tagging

`field(metadata=...)` accepts a mapping, such as a dict, and exposes it on `Field.metadata` as a read-only mappingproxy. Use it to attach schema hints, serialization rules, or documentation.

```python
from dataclasses import dataclass, field
import dataclasses

@dataclass
class CSVRow:
    first_name: str = field(metadata={'csv_header': 'First Name', 'required': True})
    last_name: str  = field(metadata={'csv_header': 'Last Name',  'required': True})
    age: int        = field(metadata={'csv_header': 'Age',        'required': False})

def get_csv_headers(cls) -> list[str]:
    return [f.metadata['csv_header'] for f in dataclasses.fields(cls)]

get_csv_headers(CSVRow)  # ['First Name', 'Last Name', 'Age']
```

---

## Combining Dataclasses with `__str__` and `__format__`

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Money:
    amount: int   # stored in cents
    currency: str = "USD"

    def __str__(self) -> str:
        return f"{self.currency} {self.amount / 100:.2f}"

    def __format__(self, spec: str) -> str:
        if spec == 'short':
            return f"{self.amount / 100:.0f}"
        return str(self)

    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

price = Money(1999)
print(price)          # USD 19.99
print(f"{price:short}")  # 20
total = price + Money(500)
print(total)          # USD 24.99
```
