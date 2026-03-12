---
name: python-pydantic-v2
description: Use when working with Pydantic v2 models, validation, serialization, settings management, or deciding between Pydantic v2 and Python dataclasses/TypedDict. Covers BaseModel design, field validators, model validators, custom types, and common migration issues from v1.
---

# Python Pydantic v2

Expert guidance for designing, validating, and serializing data with Pydantic v2 (2.0+).

## When to Use Pydantic v2

**Use Pydantic when:**
- Parsing and validating untrusted external data (API bodies, config files, env vars)
- You need rich error messages with field-level detail
- Serialization/deserialization with JSON schema generation is required
- Building FastAPI endpoints (native integration)
- Managing application settings with `BaseSettings`
- Schema validation that must be enforced at runtime

**Use Python dataclasses instead when:**
- Data is purely internal with no external input
- You need minimal overhead and Python stdlib only
- No validation or coercion is needed
- You just want to group related fields

**Use `TypedDict` instead when:**
- Describing dict shapes for static type checkers only
- No runtime validation or instantiation needed
- Working with existing dict-based APIs

See [pydantic-vs-alternatives.md](references/pydantic-vs-alternatives.md) for a full comparison matrix.

---

## Model Design: Simple to Complex

### 1. Basic Model

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True
```

```python
# Valid construction
user = User(id=1, name="Alice", email="alice@example.com")

# Pydantic coerces compatible types automatically
user = User(id="1", name="Alice", email="alice@example.com")  # id coerced str→int

# Invalid input → raises ValidationError with field-level detail
User(id="not-a-number", name="Alice", email="alice@example.com")
# pydantic_core.ValidationError: 1 validation error for User
#   id: Input should be a valid integer [type=int_parsing]
```

### 2. Fields with Metadata

```python
from pydantic import BaseModel, Field
from typing import Annotated

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Product display name")
    price: float = Field(gt=0, description="Price in USD, must be positive")
    sku: str = Field(pattern=r'^[A-Z]{2}-\d{4}$', description="Format: XX-0000")
    tags: list[str] = Field(default_factory=list, max_length=10)
    quantity: int = Field(default=0, ge=0, le=9999)
```

**Prefer `Annotated` for reusable constraints (avoids repetition):**
```python
from typing import Annotated
from pydantic import Field

# Define reusable types
PositivePrice = Annotated[float, Field(gt=0, description="Price in USD")]
SKUCode = Annotated[str, Field(pattern=r'^[A-Z]{2}-\d{4}$')]

class Product(BaseModel):
    price: PositivePrice
    sku: SKUCode
```

### 3. Nested Models

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"
    postal_code: str

class LineItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: float

class Order(BaseModel):
    order_id: str
    customer_name: str
    shipping_address: Address          # nested model
    billing_address: Address | None = None  # optional nested model
    line_items: list[LineItem] = Field(default_factory=list)
```

```python
# Nest via raw dict — Pydantic constructs the nested model automatically
order = Order(
    order_id="ORD-001",
    customer_name="Bob",
    shipping_address={"street": "123 Main St", "city": "Portland", "postal_code": "97201"},
    line_items=[],
)
```

### 4. Optional Fields and Defaults

```python
from datetime import datetime, timezone
from pydantic import BaseModel

class Event(BaseModel):
    title: str
    description: str | None = None          # optional, defaults None
    start_time: datetime
    end_time: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)
```

---

## Validation

### Field Validators (`@field_validator`)

```python
from pydantic import BaseModel, field_validator

class UserSignup(BaseModel):
    username: str
    email: str
    password: str

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores allowed)')
        return v.lower()  # normalize: return transformed value

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator('password')
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
```

**Validator modes:**
- `mode='before'` — runs before type coercion (receives raw input)
- `mode='after'` (default) — runs after type coercion (receives typed value)
- `mode='wrap'` — wraps the default validator, full control

```python
@field_validator('price', mode='before')
@classmethod
def parse_price_string(cls, v):
    """Accept '$12.99' style strings."""
    if isinstance(v, str):
        return v.lstrip('$').replace(',', '')
    return v
```

### Model Validators (`@model_validator`)

Use when validation needs access to multiple fields.

```python
from datetime import date
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start_date: date
    end_date: date
    max_days: int = 30

    @model_validator(mode='after')
    def check_date_order(self) -> 'DateRange':
        if self.end_date <= self.start_date:
            raise ValueError('end_date must be after start_date')
        delta = (self.end_date - self.start_date).days
        if delta > self.max_days:
            raise ValueError(f'Range exceeds max_days={self.max_days} (got {delta})')
        return self
```

```python
# mode='before' receives raw dict, useful for pre-processing
@model_validator(mode='before')
@classmethod
def normalize_keys(cls, data: dict) -> dict:
    """Accept both camelCase and snake_case input."""
    return {to_snake(k): v for k, v in data.items()}
```

See [validators-and-fields.md](references/validators-and-fields.md) for the full `Field()` API and advanced validator patterns.

---

## Serialization

```python
user = User(id=1, name="Alice", email="alice@example.com")

# To dict
user.model_dump()
# {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'is_active': True}

# To JSON string (fast, uses Rust core)
user.model_dump_json()
# '{"id":1,"name":"Alice","email":"alice@example.com","is_active":true}'

# Exclude unset fields (useful for PATCH endpoints)
user.model_dump(exclude_unset=True)

# Exclude specific fields
user.model_dump(exclude={'email'})

# Include only specific fields
user.model_dump(include={'id', 'name'})

# Custom serialization alias
class UserResponse(BaseModel):
    user_id: int = Field(serialization_alias='userId')
    full_name: str = Field(serialization_alias='fullName')

UserResponse(user_id=1, full_name="Alice").model_dump(by_alias=True)
# {'userId': 1, 'fullName': 'Alice'}
```

### Round-trip: Parsing from JSON / dict

```python
# From dict
user = User.model_validate({'id': 1, 'name': 'Alice', 'email': 'alice@example.com'})

# From JSON string
user = User.model_validate_json('{"id": 1, "name": "Alice", "email": "alice@example.com"}')

# From ORM / object with attributes (replaces orm_mode)
user = User.model_validate(orm_user, from_attributes=True)
```

---

## Model Configuration (`model_config`)

```python
from pydantic import BaseModel, ConfigDict

class APIResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,      # accept both alias and field name
        str_strip_whitespace=True,  # strip leading/trailing whitespace from strings
        str_to_lower=False,
        use_enum_values=True,       # store enum .value instead of enum instance
        frozen=True,                # make model immutable (hashable)
        extra='forbid',             # reject unknown fields (good for strict APIs)
        # extra='ignore' is the default
        # extra='allow' stores extras in __pydantic_extra__
    )
```

**Common config patterns:**
| Config | When to use |
|--------|-------------|
| `extra='forbid'` | Strict API contracts, CLI argument parsing |
| `extra='ignore'` | Tolerant parsing, forward-compat APIs |
| `frozen=True` | Immutable value objects, safe as dict keys |
| `populate_by_name=True` | When using `alias` but also need field-name access |
| `str_strip_whitespace=True` | User input forms, CSV parsing |

---

## Settings Management (`BaseSettings`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='APP_',      # reads APP_DATABASE_URL, APP_SECRET_KEY, etc.
        case_sensitive=False,
    )

    database_url: str
    secret_key: str
    debug: bool = False
    max_connections: int = 10
    allowed_hosts: list[str] = ['localhost']

# Usage — reads from environment, then .env file, then defaults
settings = AppSettings()
```

> `pydantic-settings` is a separate package: `pip install pydantic-settings`

---

## Anti-Patterns

### ❌ Using `dict` as a return type instead of a proper model

```python
# BAD: loses all validation and IDE support
def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "Alice"}

# GOOD: typed, validated, serializable
def get_user(user_id: int) -> User:
    return User(id=user_id, name="Alice", email="alice@example.com")
```

### ❌ Mutating a frozen model (use `model_copy`)

```python
# BAD: raises TypeError on frozen models; error-prone even on mutable ones
user.name = "Bob"

# GOOD: returns a new instance with the change applied
updated = user.model_copy(update={"name": "Bob"})
```

### ❌ Using `__init__` instead of `model_validate` for untrusted data

```python
# BAD: no coercion, bypasses validators if data comes from a dict directly
user = User(**raw_dict)   # still validates but misses from_attributes coercion

# GOOD: explicit intent, supports from_attributes and custom pre-parse hooks
user = User.model_validate(raw_dict)
```

### ❌ Optional field anti-pattern — `Optional[X]` doesn't mean "not required"

```python
# BAD: confusing — Optional[str] just means str | None, the field is still REQUIRED
class Broken(BaseModel):
    nickname: Optional[str]   # STILL raises error if missing entirely

# GOOD: add a default to make it truly optional
class Fixed(BaseModel):
    nickname: str | None = None
```

### ❌ Validators that silently swallow errors

```python
# BAD: hides bugs
@field_validator('amount')
@classmethod
def validate_amount(cls, v):
    try:
        return float(v)
    except Exception:
        return 0.0   # ← silently converts bad data to zero

# GOOD: raise ValueError with a clear message
@field_validator('amount')
@classmethod
def validate_amount(cls, v):
    try:
        return float(v)
    except (TypeError, ValueError):
        raise ValueError(f"Expected a numeric amount, got: {v!r}")
```

### ❌ Putting business logic in validators

```python
# BAD: validators should check shape/format, not call external services
@field_validator('email')
@classmethod
def check_email_not_banned(cls, v):
    if db.is_banned(v):          # ← database call in validator
        raise ValueError('...')
    return v

# GOOD: validate structure in the model, check business rules in the service layer
@field_validator('email')
@classmethod
def email_format(cls, v):
    return v.strip().lower()   # pure transformation / format check only

# Service layer handles domain rules
def register_user(data: UserSignup) -> User:
    if db.is_banned(data.email):
        raise DomainError('Email is banned')
    ...
```

### ❌ Pydantic v1 style (common migration mistakes)

```python
# v1 style → v2 equivalent
@validator('name')                     # → @field_validator('name')
def check_name(cls, v): ...            # (same)

class Config:                          # → model_config = ConfigDict(...)
    orm_mode = True                    # → from_attributes=True

user.dict()                            # → user.model_dump()
user.json()                            # → user.model_dump_json()
User.parse_obj(data)                   # → User.model_validate(data)
User.parse_raw(json_str)               # → User.model_validate_json(json_str)
User.schema()                          # → User.model_json_schema()
```

---

## Error Handling

```python
from pydantic import ValidationError

try:
    user = User.model_validate(raw_input)
except ValidationError as exc:
    # Structured error access
    for error in exc.errors():
        print(error['loc'])    # field path, e.g. ('address', 'postal_code')
        print(error['msg'])    # human-readable message
        print(error['type'])   # machine-readable error code
        print(error['input'])  # the problematic input value

    # JSON-serializable error for API responses
    return {"errors": exc.errors()}
```

---

## Quick Reference

| Task | Code |
|------|------|
| Define model | `class M(BaseModel): field: type` |
| Optional field | `field: str \| None = None` |
| Field with constraints | `Field(gt=0, max_length=100)` |
| Reusable constraint type | `MyType = Annotated[str, Field(...)]` |
| Field validator | `@field_validator('f') @classmethod def v(cls, v): ...` |
| Cross-field validation | `@model_validator(mode='after') def v(self): ...` |
| Parse from dict | `M.model_validate(d)` |
| Parse from JSON | `M.model_validate_json(s)` |
| Serialize to dict | `m.model_dump()` |
| Serialize to JSON | `m.model_dump_json()` |
| Immutable copy with change | `m.model_copy(update={...})` |
| From ORM object | `M.model_validate(obj, from_attributes=True)` |
| Forbid extra fields | `model_config = ConfigDict(extra='forbid')` |
| JSON schema | `M.model_json_schema()` |

## Reference Files

- [validators-and-fields.md](references/validators-and-fields.md) — Full `Field()` API, `Annotated` validators, `BeforeValidator`/`AfterValidator`, `PlainValidator`, custom types
- [advanced-patterns.md](references/advanced-patterns.md) — Discriminated unions, generic models, `RootModel`, partial updates, recursive models
- [pydantic-vs-alternatives.md](references/pydantic-vs-alternatives.md) — Decision matrix: Pydantic vs dataclasses vs TypedDict vs attrs
