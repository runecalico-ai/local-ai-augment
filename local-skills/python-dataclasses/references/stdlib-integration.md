# Dataclasses — stdlib Integration

## `dataclasses` Module Utilities

```python
import dataclasses

# Inspect all fields (returns tuple of Field objects)
dataclasses.fields(instance_or_class)

# Convert to dict (recursive — nested dataclasses also converted)
dataclasses.asdict(instance)

# Convert to tuple (recursive — field order matches declaration order)
dataclasses.astuple(instance)

# Shallow copy with field overrides
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
- `asdict` recursively converts **all** nested dataclasses, lists, tuples, and dicts.
- Does **not** call `to_dict()` methods — it inspects fields directly.
- Fields with `repr=False` or `compare=False` are still included in `asdict` output.
- Fields with `field(exclude=...)` — there is no built-in exclude; filter manually:

```python
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

Dataclasses have no built-in JSON support. Use one of these patterns:

### Pattern 1: `asdict` + `json.dumps` (simple, no custom types)

```python
import json
from dataclasses import asdict

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

### Pattern 3: `to_dict` / `from_dict` methods on the class (explicit, recommended for complex models)

```python
from dataclasses import dataclass, field
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

### Pattern 4: Use `dataclasses-json` library (third-party, zero boilerplate)

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

# replace() is always shallow — only top-level fields differ
updated = replace(root, value=99)
assert updated.children is root.children   # same list object
```

**Rule:** Use `replace()` for value-like dataclasses with immutable field values. Use `copy.deepcopy()` when mutability at any depth is a concern.

---

## `pickle` Compatibility

Dataclasses are pickle-compatible by default:

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

`slots=True` dataclasses are also pickle-compatible (Python 3.10+ handles `__slots__` correctly).

---

## `functools.total_ordering` (Pre-3.10 Alternative to `order=True`)

`order=True` is always preferred. `total_ordering` is only needed when you can't use `@dataclass(order=True)` (e.g., custom `__lt__` logic).

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
        # Custom: pre-release versions sort BELOW the release
        self_key = (self.major, self.minor, self.patch, 0 if not self.pre else -1)
        other_key = (other.major, other.minor, other.patch, 0 if not other.pre else -1)
        return self_key < other_key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemVer):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.pre) == \
               (other.major, other.minor, other.patch, other.pre)
```

---

## `__slots__` Interaction (Pre-3.10)

Before Python 3.10's `slots=True`, adding `__slots__` manually to a dataclass is error-prone:

```python
# ❌ BAD (pre-3.10): manual __slots__ conflicts with dataclass-generated __dict__
@dataclass
class Broken:
    __slots__ = ('x', 'y')
    x: float
    y: float
    # This works for access but breaks __dict__, pickling, and some tools

# ✅ GOOD: just use slots=True (Python 3.10+)
@dataclass(slots=True)
class Fast:
    x: float
    y: float
```

---

## `typing.get_type_hints` — Runtime Field Type Inspection

```python
import typing
import dataclasses

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

`field(metadata=...)` accepts an immutable mapping. Use it to attach schema hints, serialization rules, or documentation.

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
