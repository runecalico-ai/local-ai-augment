---
name: python-pydantic-v2
description: Use when working with Pydantic v2.11+ for FastAPI request/response schemas, API payload validation, PATCH/update models, env/settings models, recursive models, OpenAPI/JSON schema, computed fields, TypeAdapter validation, aliases, validation_alias, ConfigDict/model_config, from_attributes, `field_validator`, `model_validator`, `field_serializer`, `model_serializer`, `BeforeValidator`, `AfterValidator`, `WrapValidator`, `PlainValidator`, `pydantic-settings` `BaseSettings` / `SettingsConfigDict`, `create_model`, `ValidateAs` (2.12+), discriminated unions, RootModel, dynamic models, choosing between Pydantic, dataclass, TypedDict, attrs, and msgspec, or troubleshooting `use_enum_values`, `validate_default`, and `model_copy(update=...)` behavior when migrating v1 patterns such as @validator, parse_obj, parse_raw, orm_mode, and class Config.
---

# Python Pydantic v2

Expert guidance for designing, validating, and serializing data with current Pydantic v2 releases, especially v2.11+.

## First Choices

**Reach for `BaseModel` when:**
- You need a named schema with reusable fields, config, validators, and JSON schema
- The data is crossing an application boundary and deserves a first-class contract

**Reach for `TypeAdapter` when:**
- You need to validate a non-model type such as `list[User]`, `dict[str, int]`, `TypedDict`, or a union
- A standalone type is enough and creating a `BaseModel` would add ceremony without value

**Prefer strict mode when:**
- Silent coercion would hide bugs at the boundary
- You are validating data from other services and want type mismatches to fail loudly

Strict behavior depends on the validation path. Python input, JSON input, and string-mode validation can differ, so test the same path your application actually uses.

Deep dives:
- [advanced-patterns.md](references/advanced-patterns.md) for PATCH updates, recursive models, `RootModel`, and serializers
- [validators-and-fields.md](references/validators-and-fields.md) for validator ordering, `json_schema_input_type`, and computed fields
- [pydantic-vs-alternatives.md](references/pydantic-vs-alternatives.md) for choosing between Pydantic, dataclasses, `TypedDict`, `attrs`, and `msgspec`

```python
from pydantic import BaseModel, TypeAdapter, ValidationError

class LoginPayload(BaseModel):
    user_id: int

user_ids = TypeAdapter(list[int]).validate_python(['1', 2, 3])

try:
    LoginPayload.model_validate({'user_id': '42'}, strict=True)
except ValidationError:
    pass

strict_payload = LoginPayload.model_validate({'user_id': 42}, strict=True)
```

```python
from datetime import datetime

from pydantic import BaseModel

class Event(BaseModel):
    happened_at: datetime

Event.model_validate_strings({'happened_at': '2024-01-01T12:00:00'})
```

## When to Use Pydantic v2

**Use Pydantic when:**
- Parsing and validating untrusted external data (API bodies, config files, env vars)
- You need rich error messages with field-level detail
- Serialization/deserialization with JSON schema generation is required
- Building FastAPI endpoints (native integration)
- Managing application settings with `pydantic-settings` (`BaseSettings`)
- You want `TypeAdapter` validation for a non-model type such as `list[User]` or `TypedDict`
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

**Use `TypedDict` + `TypeAdapter` when:**
- You want to keep dict-shaped data but still validate it at runtime
- A full `BaseModel` would add noise while a validated mapping shape is enough
- On Python < 3.12, import `TypedDict` from `typing_extensions` when feeding it to Pydantic

See [pydantic-vs-alternatives.md](references/pydantic-vs-alternatives.md) for a full comparison matrix.

---

## Model Design: Simple to Complex

### 1. Basic Model

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True
```

Plain `str` does not validate email shape. Use `EmailStr` or an explicit validator when boundary semantics require that.

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True

# Valid construction
user = User(id=1, name="Alice", email="alice@example.com")

# Pydantic coerces compatible types automatically
user = User(id="1", name="Alice", email="alice@example.com")  # id coerced str→int

# Invalid input → raises ValidationError with field-level detail
try:
    User(id="not-a-number", name="Alice", email="alice@example.com")
except ValidationError:
    pass
# pydantic_core.ValidationError: 1 validation error for User
#   id: Input should be a valid integer [type=int_parsing]
```

### 2. Fields with Metadata

```python
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import Annotated

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Product display name")
    price: Decimal = Field(gt=Decimal('0'), description="Price in USD, must be positive")
    sku: str = Field(pattern=r'^[A-Z]{2}-\d{4}$', description="Format: XX-0000")
    tags: list[str] = Field(default_factory=list, max_length=10)
    quantity: int = Field(default=0, ge=0, le=9999)
```

**Prefer `Annotated` for reusable constraints (avoids repetition):**
```python
from decimal import Decimal
from typing import Annotated
from pydantic import BaseModel, Field

# Define reusable types
PositivePrice = Annotated[Decimal, Field(gt=Decimal('0'), description="Price in USD")]
SKUCode = Annotated[str, Field(pattern=r'^[A-Z]{2}-\d{4}$')]

class Product(BaseModel):
    price: PositivePrice
    sku: SKUCode
```

> Keep defaults, `default_factory`, and aliases in normal assignment form when static type checkers need an accurate generated constructor signature.

> For currency, prefer `Decimal` or minor-unit integers such as cents. Use `float` only for non-financial quantities where binary floating-point rounding is acceptable.

### 3. Nested Models

```python
from decimal import Decimal
from pydantic import BaseModel, Field

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"
    postal_code: str

class LineItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: Decimal

class Order(BaseModel):
    order_id: str
    customer_name: str
    shipping_address: Address          # nested model
    billing_address: Address | None = None  # optional nested model
    line_items: list[LineItem] = Field(default_factory=list)
```

```python
from decimal import Decimal
from pydantic import BaseModel, Field

class Address(BaseModel):
    street: str
    city: str
    country: str = "US"
    postal_code: str

class LineItem(BaseModel):
    product_id: str
    quantity: int
    unit_price: Decimal

class Order(BaseModel):
    order_id: str
    customer_name: str
    shipping_address: Address
    billing_address: Address | None = None
    line_items: list[LineItem] = Field(default_factory=list)

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
from pydantic import BaseModel, Field

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
- `mode='plain'` — replaces normal validation for that field
- `mode='wrap'` — wraps the default validator, full control
- If a `before`, `plain`, or `wrap` validator accepts input wider than the field annotation, set `json_schema_input_type` so generated schema stays accurate

```python
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

class PriceInput(BaseModel):
    price: Decimal

    @field_validator('price', mode='before', json_schema_input_type=str | int | float)
    @classmethod
    def parse_price_string(cls, value: Any) -> Any:
        """Accept '$12.99' style strings."""
        if isinstance(value, str):
            return value.lstrip('$').replace(',', '')
        return value
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
from typing import Any

from pydantic import BaseModel, model_validator
from pydantic.alias_generators import to_snake

class NormalizedPayload(BaseModel):
    first_name: str
    last_name: str

    @model_validator(mode='before')
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        """Accept both camelCase and snake_case input."""
        if isinstance(data, dict):
            return {to_snake(k): v for k, v in data.items()}
        return data
```

See [validators-and-fields.md](references/validators-and-fields.md) for the full `Field()` API and advanced validator patterns.

---

## Serialization

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool = True

user = User(id=1, name="Alice", email="alice@example.com")

# To dict
user.model_dump()
# {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'is_active': True}

# To JSON string (fast, uses Rust core)
user.model_dump_json()
# '{"id":1,"name":"Alice","email":"alice@example.com","is_active":true}'

# Exclude unset fields (useful when serializing a dedicated update model for PATCH flows; see partial-updates guidance)
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

### Serializing subclass instances

```python
from pydantic import BaseModel, SerializeAsAny

class User(BaseModel):
    name: str

class Admin(User):
    role: str

class Response(BaseModel):
    user: User
    user_any: SerializeAsAny[User]

payload = Response(user=Admin(name='Alice', role='admin'), user_any=Admin(name='Alice', role='admin'))
payload.model_dump()
# {'user': {'name': 'Alice'}, 'user_any': {'name': 'Alice', 'role': 'admin'}}
```

Pydantic v2 serializes according to the annotated field type by default. Prefer field-scoped `SerializeAsAny[...]` when subclass fields are intentionally part of the contract. `model_dump(serialize_as_any=True)` changes the entire serialization call and can expose subclass-only sensitive fields on sibling model-like values.

### Round-trip: Parsing from JSON / dict

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

class ORMUser:
    def __init__(self, *, id: int, name: str, email: str) -> None:
        self.id = id
        self.name = name
        self.email = email

# From dict
user = User.model_validate({'id': 1, 'name': 'Alice', 'email': 'alice@example.com'})

# From JSON string
user = User.model_validate_json('{"id": 1, "name": "Alice", "email": "alice@example.com"}')

# From ORM / object with attributes (replaces orm_mode)
orm_user = ORMUser(id=1, name='Alice', email='alice@example.com')
user = User.model_validate(orm_user, from_attributes=True)
```

Use `from_attributes=True` only with known-safe objects. On ORMs, attribute access can trigger lazy loads, N+1 queries, or property side effects, so prefer preloaded relations or explicit DTOs when the object graph is nontrivial.

---

## Model Configuration (`model_config`)

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class APIResponse(BaseModel):
    model_config = ConfigDict(
        validate_by_name=True,      # v2.11+: prefer these over populate_by_name
        validate_by_alias=True,
        str_strip_whitespace=True,  # strip leading/trailing whitespace from strings
        str_to_lower=False,
        use_enum_values=True,       # stores enum .value for validated enum inputs/defaults
        frozen=True,                # faux-immutable; hashable only if all fields are hashable
        extra='forbid',             # reject unknown fields (good for strict APIs)
        # extra='ignore' is the default
        # extra='allow' stores extras in __pydantic_extra__
    )
```

**Config caveats:**
- This skill targets current v2 releases. If you support pre-v2.11 code, use `populate_by_name=True` instead of `validate_by_name=True` / `validate_by_alias=True`
- In v2.11+, prefer `validate_by_name=True` plus `validate_by_alias=True` over `populate_by_name=True`
- `use_enum_values=True` changes what is stored in the model instance, not just how it serializes
- For any enum field with a default, use `Field(validate_default=True)` if you want that default normalized during validation too
- `frozen=True` blocks attribute reassignment, but nested mutable values can still be mutated

**Common config patterns:**
| Config | When to use |
|--------|-------------|
| `extra='forbid'` | Strict API contracts, CLI argument parsing |
| `extra='ignore'` | Tolerant parsing, forward-compat APIs |
| `frozen=True` | Faux-immutable value objects; potentially hashable if all fields are hashable |
| `validate_by_name=True, validate_by_alias=True` | When aliased fields should accept both canonical names and aliases |
| `str_strip_whitespace=True` | User input forms, CSV parsing |
| `strict=True` | Boundary validation where implicit coercion would hide bugs |
| `validate_assignment=True` | Re-run validation on attribute reassignment after model creation |

```python
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

class Status(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

class Job(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: Status = Field(default=Status.ACTIVE, validate_default=True)
```

### Assignment Validation (`validate_assignment=True`)

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class MutableUser(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    name: str

user = MutableUser(name='Alice')

try:
    user.name = 123
except ValidationError:
    pass
```

Without `validate_assignment=True`, direct attribute reassignment is not revalidated. This still does not make nested mutable values safe; use immutable field types or explicit copy-and-validate flows where needed.

This also does not revalidate reused model instances when they are embedded inside other models. For that boundary, configure `revalidate_instances` on the model type being reused.

---

## Settings Management (`pydantic-settings` / `BaseSettings`)

Install first: `pip install pydantic-settings`

```python
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='APP_',      # reads APP_DATABASE_URL, APP_SECRET_KEY, etc.
        case_sensitive=False,
    )

    database_url: str
    secret_key: SecretStr
    debug: bool = False
    max_connections: int = 10
    allowed_hosts: list[str] = Field(default_factory=lambda: ['localhost'])

# Usage — simplified source order for this example: init kwargs, then environment, then .env file, then defaults
settings = AppSettings()
```

> `pydantic-settings` is a separate package: `pip install pydantic-settings`

For collection or nested settings such as `list[str]`, environment values usually need JSON-style content, init kwargs take precedence over environment and `.env` values in this simplified example, and `BaseSettings` validates defaults by default unlike plain `BaseModel`. Secrets directories, CLI parsing, and custom source ordering can change the effective precedence.

Example env value: `APP_ALLOWED_HOSTS='["localhost", "api.example.com"]'`

If a field overrides its env name via alias-style configuration, that explicit env name takes precedence over the default `env_prefix`-derived name for that field.

---

## Anti-Patterns

### ❌ Returning untyped `dict` objects for stable external contracts

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str

# BAD: loses all validation and IDE support
def get_user(user_id: int) -> dict:
    return {"id": user_id, "name": "Alice"}

# GOOD: typed, validated, serializable
def get_user(user_id: int) -> User:
    return User(id=user_id, name="Alice", email="alice@example.com")
```

Internal transforms can still use plain `dict` objects when that is the clearer tradeoff. Prefer models at boundaries that need validation, schema generation, or stable typed contracts.

### ❌ Mutating a frozen model (use `model_copy` only for trusted updates)

```python
from pydantic import BaseModel, ConfigDict, ValidationError

class User(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str

user = User(name='Alice')

# BAD: raises ValidationError on frozen models; nested mutables can still change
try:
    user.name = "Bob"
except ValidationError:
    pass

# GOOD for trusted updates only; skips validation
updated = user.model_copy(update={"name": "Bob"})

# GOOD for untrusted external input on shallow, round-trippable flat models only
external_update = {"name": "Bob"}
revalidated = User.model_validate({
    **user.model_dump(round_trip=True, exclude=set(type(user).model_computed_fields)),
    **external_update,
})
```

For nested updates, computed fields, custom serializers, or field-exclusion-heavy models, define an explicit merge strategy instead of reusing this shortcut.

> `frozen=True` provides faux-immutability. It prevents attribute reassignment, but it does not make nested `dict`, `list`, or `set` values immutable.

### ❌ Using `model_construct()` or a custom `__init__` for untrusted data

```python
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

class ORMUser:
    def __init__(self, *, id: int, name: str) -> None:
        self.id = id
        self.name = name

raw_dict = {'id': 1, 'name': 'Alice'}
orm_user = ORMUser(id=1, name='Alice')

# Both of these validate input data
user = User(**raw_dict)
user = User.model_validate(raw_dict)

# BAD: skips validation entirely; trusted data only
user = User.model_construct(**raw_dict)

# GOOD: use model_validate when you need boundary-focused options
user = User.model_validate(raw_dict, strict=True)
user = User.model_validate(orm_user, from_attributes=True)
```

Custom `__init__` implementations are generally not recommended. If you define one, you must call `super().__init__(**data)`, but constructor-level hooks still do not expose validation-call options such as `strict`, `extra`, or validation context. Prefer `model_post_init`, `@field_validator`, or `@model_validator` instead.

### ❌ Optional field anti-pattern — `Optional[X]` doesn't mean "not required"

```python
from pydantic import BaseModel

# BAD: str | None still means the field is REQUIRED if no default is provided
class Broken(BaseModel):
    nickname: str | None      # STILL raises error if missing entirely

# GOOD: add a default to make it truly optional
class Fixed(BaseModel):
    nickname: str | None = None
```

### ❌ Validators that silently swallow errors

```python
from pydantic import BaseModel, field_validator

class BrokenBatch(BaseModel):
    quantity: int

    @field_validator('quantity', mode='before')
    @classmethod
    def validate_quantity(cls, v):
        try:
            return int(v)
        except Exception:
            return 0   # ← silently converts bad data to zero

class FixedBatch(BaseModel):
    quantity: int

    @field_validator('quantity', mode='before')
    @classmethod
    def validate_quantity(cls, v):
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError(f"Expected an integer quantity, got: {v!r}")
```

### ❌ Putting business logic in validators

```python
from pydantic import BaseModel, field_validator

class DomainError(Exception):
    pass

class FakeDb:
    def is_banned(self, email: str) -> bool:
        return email.endswith('@blocked.test')

db = FakeDb()

class BrokenSignup(BaseModel):
    email: str

    # BAD: validators should check shape/format, not call external services
    @field_validator('email')
    @classmethod
    def check_email_not_banned(cls, v: str) -> str:
        if db.is_banned(v):          # ← database call in validator
            raise ValueError('Email is banned')
        return v

class User(BaseModel):
    email: str

class UserSignup(BaseModel):
    email: str

    # GOOD: validate structure in the model, check business rules in the service layer
    @field_validator('email')
    @classmethod
    def email_format(cls, v: str) -> str:
        return v.strip().lower()   # pure transformation / format check only

def register_user(data: UserSignup) -> User:
    if db.is_banned(data.email):
        raise DomainError('Email is banned')
    return User(email=data.email)
```

### ❌ Pydantic v1 style (common migration mistakes)

| Pydantic v1 | Pydantic v2 |
|-------------|-------------|
| `@validator('name')` | `@field_validator('name')` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `orm_mode = True` | `from_attributes=True` |
| `user.dict()` | `user.model_dump()` |
| `user.json()` | `user.model_dump_json()` |
| `User.parse_obj(data)` | `User.model_validate(data)` |
| `User.parse_raw(json_str)` | `User.model_validate_json(json_str)` |
| `User.schema()` | `User.model_json_schema()` |

---

## Error Handling

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    id: int
    name: str
    email: str

raw_input = {'id': 'bad', 'name': 'Alice', 'email': 'alice@example.com'}

try:
    user = User.model_validate(raw_input)
except ValidationError as exc:
    # Structured error access
    for error in exc.errors():
        print(error['loc'])    # field path, e.g. ('address', 'postal_code')
        print(error['msg'])    # human-readable message
        print(error['type'])   # machine-readable error code
        print(error['input'])  # debug-only: raw input can contain secrets or PII

    # JSON-serializable error for API responses: omit raw input values by default
    api_error_payload = {'errors': exc.errors(include_input=False)}
```

For sensitive boundaries, also consider `ConfigDict(hide_input_in_errors=True)` so exception text does not echo raw input values.

---

## Quick Reference

| Task | Pattern |
|------|---------|
| Define model | `class M(BaseModel): field: type` |
| Nullable + omittable field | `field: str \| None = None` |
| Omittable but non-null PATCH field | `See PATCH guidance in advanced-patterns.md` |
| Numeric field constraints | `Field(gt=0)` |
| String or collection constraints | `Field(min_length=1, max_length=100)` |
| Reusable constraint type | `MyType = Annotated[str, Field(...)]` |
| Field validator | `@field_validator('f') @classmethod def v(cls, v): ...` |
| Cross-field validation | `@model_validator(mode='after') def v(self): ...` |
| Parse from dict | `M.model_validate(d)` |
| Parse with strict types | `M.model_validate(d, strict=True)` |
| Parse from JSON | `M.model_validate_json(s)` |
| Validation schema | `M.model_json_schema()` |
| Serialization schema | `M.model_json_schema(mode='serialization')` |
| Serialize to dict | `m.model_dump()` |
| Serialize to JSON | `m.model_dump_json()` |
| Trusted copy with change | `m.model_copy(update={...})  # skips validation` |
| Validated shallow flat-model merge update | `See PATCH guidance in advanced-patterns.md` |
| From preloaded/safe attribute object | `M.model_validate(obj, from_attributes=True)` |
| Validate a non-model type | `TypeAdapter(list[M]).validate_python(data)` |
| Forbid extra fields | `model_config = ConfigDict(extra='forbid')` |

## Reference Files

- [validators-and-fields.md](references/validators-and-fields.md) — Full `Field()` API, `Annotated` validators, `BeforeValidator`/`AfterValidator`, `PlainValidator`, custom types, computed fields
- [advanced-patterns.md](references/advanced-patterns.md) — Discriminated unions, generic models, `RootModel`, partial updates, recursive models, field/model serializers
- [pydantic-vs-alternatives.md](references/pydantic-vs-alternatives.md) — Selection guide: Pydantic vs dataclasses vs `TypedDict` vs `attrs` vs `msgspec`
