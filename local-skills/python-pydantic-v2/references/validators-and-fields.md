# Validators and Fields — Pydantic v2

## `Field()` Full Reference

```python
from pydantic import Field
from typing import Annotated

Field(
    default=...,              # required (use ... or omit for required fields)
    default_factory=list,     # callable that produces default; mutually exclusive with default

    # --- String constraints ---
    min_length=1,
    max_length=255,
    pattern=r'^\d{3}-\d{4}$',

    # --- Numeric constraints ---
    gt=0,                     # strictly greater than
    ge=0,                     # greater than or equal (alias: gte)
    lt=100,                   # strictly less than
    le=100,                   # less than or equal (alias: lte)
    multiple_of=5,            # value must be multiple of this

    # --- Collection constraints ---
    min_length=1,             # also applies to list/set/tuple min items
    max_length=10,            # also applies to list/set/tuple max items

    # --- Documentation / schema ---
    title='Display Name',
    description='Human-readable description for JSON schema',
    examples=[42, 100],
    json_schema_extra={'x-internal': True},  # extra OpenAPI properties

    # --- Alias / serialization ---
    alias='externalName',           # parse input using this name
    validation_alias='external_name',  # alias only for parsing (not serialization)
    serialization_alias='outputName',  # alias only for serialization
    exclude=False,                  # exclude from model_dump() / schema

    # --- Behavior flags ---
    frozen=True,              # make THIS field immutable (field-level frozen)
    repr=True,                # include in __repr__
    init=True,                # include in __init__
)
```

### Alias Chaining (accept multiple input names)

```python
from pydantic import AliasChoices, AliasPath

class Payload(BaseModel):
    user_id: int = Field(
        validation_alias=AliasChoices('user_id', 'userId', 'uid')
    )
    # AliasPath for nested access from a raw dict
    city: str = Field(
        validation_alias=AliasPath('address', 'city')
    )

Payload.model_validate({'userId': 5, 'address': {'city': 'Portland'}})
# → Payload(user_id=5, city='Portland')
```

---

## Annotated Validators (Reusable, Composable)

Prefer `Annotated` validators over `@field_validator` for constraints that apply to a *type* regardless of which model uses it.

### `BeforeValidator` — runs before type coercion

```python
from typing import Annotated
from pydantic import BeforeValidator

def parse_comma_list(v) -> list[str]:
    if isinstance(v, str):
        return [item.strip() for item in v.split(',') if item.strip()]
    return v

CommaSeparatedList = Annotated[list[str], BeforeValidator(parse_comma_list)]

class Config(BaseModel):
    allowed_hosts: CommaSeparatedList

Config(allowed_hosts="localhost, 127.0.0.1")
# → Config(allowed_hosts=['localhost', '127.0.0.1'])
```

### `AfterValidator` — runs after type coercion

```python
from pydantic import AfterValidator

def normalize_email(v: str) -> str:
    return v.strip().lower()

NormalizedEmail = Annotated[str, AfterValidator(normalize_email)]

class User(BaseModel):
    email: NormalizedEmail
```

### `PlainValidator` — replaces default validation entirely

```python
from pydantic import PlainValidator

def parse_us_phone(v) -> str:
    digits = re.sub(r'\D', '', str(v))
    if len(digits) != 10:
        raise ValueError(f'Expected 10-digit US phone, got {len(digits)} digits')
    return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'

USPhone = Annotated[str, PlainValidator(parse_us_phone)]
```

### `WrapValidator` — wraps the existing validator

```python
from pydantic import WrapValidator
from pydantic.functional_validators import ValidatorFunctionWrapHandler

def coerce_none_to_empty(v, handler: ValidatorFunctionWrapHandler) -> list:
    if v is None:
        return []
    return handler(v)

NoneableList = Annotated[list[str], WrapValidator(coerce_none_to_empty)]
```

### Combining Multiple Validators and Constraints

```python
from pydantic import Field, AfterValidator, BeforeValidator

def strip_whitespace(v: str) -> str:
    return v.strip()

def validate_no_html(v: str) -> str:
    if '<' in v or '>' in v:
        raise ValueError('HTML tags not allowed')
    return v

SafeString = Annotated[
    str,
    BeforeValidator(strip_whitespace),
    Field(min_length=1, max_length=500),
    AfterValidator(validate_no_html),
]
```

---

## `@field_validator` — In-depth

### Multiple fields in one validator

```python
from pydantic import field_validator

class Profile(BaseModel):
    first_name: str
    last_name: str
    bio: str

    @field_validator('first_name', 'last_name')
    @classmethod
    def title_case_name(cls, v: str) -> str:
        return v.strip().title()
```

### Accessing sibling field values (use `model_validator` instead)

`@field_validator` cannot reliably access other field values. Use `@model_validator(mode='after')` for cross-field logic.

### `info` parameter — accessing field name and config

```python
from pydantic import field_validator, FieldValidationInfo

class Model(BaseModel):
    value: int

    @field_validator('value')
    @classmethod
    def check_positive(cls, v: int, info: FieldValidationInfo) -> int:
        if v <= 0:
            raise ValueError(f"Field '{info.field_name}' must be positive, got {v}")
        return v
```

### Validator execution order

For a single field, class-level validators are **outermost** (run first/last); Annotated validators are **innermost** (closest to the type):

1. `@field_validator(mode='before')` — outermost, runs first (before coercion)
2. `BeforeValidator` (Annotated) — left to right, before coercion
3. Pydantic type coercion
4. `AfterValidator` (Annotated) — left to right, after coercion
5. `@field_validator(mode='after')` — outermost, runs last (after coercion)

---

## `@model_validator` — In-depth

### `mode='after'` (most common) — receives the constructed model

```python
from pydantic import model_validator

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode='after')
    def passwords_match(self) -> 'PasswordChange':
        if self.new_password != self.confirm_password:
            raise ValueError('new_password and confirm_password must match')
        if self.new_password == self.current_password:
            raise ValueError('new_password must differ from current_password')
        return self
```

### `mode='before'` — receives raw dict before any field processing

```python
from pydantic import model_validator

class FlexibleInput(BaseModel):
    name: str
    value: float

    @model_validator(mode='before')
    @classmethod
    def handle_legacy_format(cls, data):
        # Support old API that sent {'label': ..., 'amount': ...}
        if isinstance(data, dict) and 'label' in data:
            return {'name': data['label'], 'value': data['amount']}
        return data
```

### `mode='wrap'` — full control, can short-circuit validation

```python
from pydantic import model_validator

class CachedModel(BaseModel):
    id: int
    data: str

    @model_validator(mode='wrap')
    @classmethod
    def from_cache(cls, v, handler):
        if isinstance(v, cls):
            return v           # already an instance, skip re-parsing
        return handler(v)      # normal validation path
```

---

## Custom Types with `__get_validators__` / `__get_pydantic_core_schema__`

### Using `Annotated` with `GetCoreSchemaHandler` (v2 recommended approach)

```python
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class Color:
    def __init__(self, hex_code: str):
        if not hex_code.startswith('#') or len(hex_code) not in (4, 7):
            raise ValueError(f'Invalid hex color: {hex_code}')
        self.hex_code = hex_code

    def __repr__(self) -> str:
        return f'Color({self.hex_code!r})'

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type,
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_plain_validator_function(
            lambda v: cls(v) if isinstance(v, str) else v,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda c: c.hex_code,
                info_arg=False,
            ),
        )

class Theme(BaseModel):
    primary_color: Color
    secondary_color: Color = Color('#FFFFFF')

t = Theme(primary_color='#FF5733')
t.model_dump()  # {'primary_color': '#FF5733', 'secondary_color': '#FFFFFF'}
```

---

## Computed Fields (`@computed_field`)

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

    @computed_field
    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

r = Rectangle(width=3.0, height=4.0)
r.model_dump()  # {'width': 3.0, 'height': 4.0, 'area': 12.0, 'perimeter': 14.0}
```
