# Validators and Fields — Pydantic v2

## `Field()` Quick Reference

| Category | Args | Notes |
|----------|------|-------|
| Required/defaults | `default`, `default_factory`, `validate_default` | Defaults are not validated unless `validate_default=True`; `default_factory` can take zero args or the already validated data from earlier fields only |
| Strings and collections | `min_length`, `max_length`, `pattern` | `min_length` / `max_length` also apply to list, set, tuple, and dict |
| Numbers | `gt`, `ge`, `lt`, `le`, `multiple_of`, `allow_inf_nan`, `max_digits`, `decimal_places` | `ge` / `le` are the actual kwargs; there are no `gte` / `lte` aliases |
| Aliases | `alias`, `validation_alias`, `serialization_alias`, `alias_priority` | Use `AliasChoices` / `AliasPath` for multiple or nested inputs |
| Schema and serialization | `title`, `description`, `examples`, `json_schema_extra`, `exclude`, `exclude_if` (2.12+), `discriminator` | `exclude` affects serialization, not validation |
| Per-field behavior | `frozen`, `repr`, `strict`, `coerce_numbers_to_str`, `union_mode`, `fail_fast` | `strict=True` enables field-level strict mode; `fail_fast` is for iterable fields such as list/tuple/set/frozenset |
| Dataclass-only | `init`, `init_var`, `kw_only` | Only applies to Pydantic or stdlib dataclasses, not regular `BaseModel` fields |

Some `Field()` options were added after early v2.0 releases. If an argument such as `exclude_if` (2.12+), `coerce_numbers_to_str`, or `fail_fast` is missing in your environment, check the docs for your installed Pydantic version.

If `default_factory` takes one argument, that dict contains only fields that were already validated earlier in model-definition order. For cross-field defaults that should not depend on field order, prefer a model validator.

```python
from typing import Annotated
from pydantic import BaseModel, Field

ProductCode = Annotated[str, Field(pattern=r'^[A-Z]{3}-\d{4}$', min_length=8, max_length=8)]

class Product(BaseModel):
    code: ProductCode
    quantity: int = Field(ge=0, le=1000, strict=True)
```

### Alias Chaining (accept multiple input names)

```python
from pydantic import AliasChoices, AliasPath, BaseModel, Field

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

Keep defaults, `default_factory`, and aliases in normal assignment form when static type checkers need an accurate generated constructor signature.

### `BeforeValidator` — runs before type coercion

```python
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator

def parse_comma_list(v: Any) -> Any:
    if isinstance(v, str):
        return [item.strip() for item in v.split(',') if item.strip()]
    return v

CommaSeparatedList = Annotated[
    list[str],
    BeforeValidator(parse_comma_list, json_schema_input_type=str | list[str]),
]

class Config(BaseModel):
    allowed_hosts: CommaSeparatedList

Config(allowed_hosts="localhost, 127.0.0.1")
# → Config(allowed_hosts=['localhost', '127.0.0.1'])
```

If a `before`, `plain`, or `wrap` validator accepts values broader than the field annotation, set `json_schema_input_type` so generated JSON Schema reflects the real input shape.

### `AfterValidator` — runs after type coercion

```python
from typing import Annotated

from pydantic import AfterValidator, BaseModel

def normalize_email(v: str) -> str:
    return v.strip().lower()

NormalizedEmail = Annotated[str, AfterValidator(normalize_email)]

class User(BaseModel):
    email: NormalizedEmail
```

### `PlainValidator` — replaces default validation entirely

```python
import re
from typing import Annotated, Any

from pydantic import PlainValidator

def parse_us_phone(v: Any) -> str:
    digits = re.sub(r'\D', '', str(v))
    if len(digits) != 10:
        raise ValueError(f'Expected 10-digit US phone, got {len(digits)} digits')
    return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'

USPhone = Annotated[
    str,
    PlainValidator(parse_us_phone, json_schema_input_type=str | int),
]
```

### `WrapValidator` — wraps the existing validator

```python
from typing import Annotated, Any

from pydantic import ValidatorFunctionWrapHandler, WrapValidator

def coerce_none_to_empty(v: Any, handler: ValidatorFunctionWrapHandler) -> Any:
    if v is None:
        return handler([])
    return handler(v)

NoneableList = Annotated[
    list[str],
    WrapValidator(coerce_none_to_empty, json_schema_input_type=list[str] | None),
]
```

### Combining Multiple Validators and Constraints

```python
from typing import Annotated

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
from pydantic import BaseModel, field_validator

class Profile(BaseModel):
    first_name: str
    last_name: str
    bio: str

    @field_validator('first_name', 'last_name')
    @classmethod
    def title_case_name(cls, v: str) -> str:
        return v.strip().title()
```
### `mode='plain'` with decorator syntax

```python
import re
from typing import Any

from pydantic import BaseModel, field_validator

class PhoneInput(BaseModel):
    phone: str

    @field_validator('phone', mode='plain', json_schema_input_type=str | int)
    @classmethod
    def parse_phone(cls, value: Any) -> str:
        digits = re.sub(r'\D', '', str(value))
        if len(digits) != 10:
            raise ValueError('Expected a 10-digit phone number')
        return f'({digits[:3]}) {digits[3:6]}-{digits[6:]}'
```

### Accessing sibling field values (use `model_validator` instead)

`@field_validator` can inspect earlier validated fields through `ValidationInfo.data`, but that behavior is order-dependent. Use `@model_validator(mode='after')` for general cross-field logic.

### `info` parameter — accessing field name and config

`ValidationInfo` is useful for metadata such as the current field name or model config. If you inspect `info.data`, remember that it only contains earlier validated fields.

```python
from pydantic import BaseModel, ValidationInfo, field_validator

class Model(BaseModel):
    value: int

    @field_validator('value')
    @classmethod
    def check_positive(cls, v: int, info: ValidationInfo) -> int:
        if v <= 0:
            raise ValueError(f"Field '{info.field_name}' must be positive, got {v}")
        return v
```

### Validator execution order

When using the `Annotated` pattern, validators are ordered like this:

1. `WrapValidator` and `BeforeValidator` run from **right to left**
2. Pydantic performs its internal validation and coercion
3. `AfterValidator` runs from **left to right**

Decorators such as `@field_validator` are converted to annotated metadata internally, so the same ordering rules apply.

### JSON Schema and widened validator inputs

```python
from typing import Any

from pydantic import BaseModel, field_validator

class CastIntsToStr(BaseModel):
    value: str

    @field_validator('value', mode='before', json_schema_input_type=int | str)
    @classmethod
    def cast_ints(cls, value: Any) -> Any:
        return str(value) if isinstance(value, int) else value
```

Without `json_schema_input_type`, the generated schema would claim the input is only `str`, even though the validator also accepts `int`.

---

## `@model_validator` — In-depth

### `mode='after'` (most common) — receives the constructed model

```python
from typing import Any

from pydantic import BaseModel, model_validator

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

### `mode='before'` — receives raw input before any field processing

```python
from typing import Any

from pydantic import BaseModel, model_validator

class FlexibleInput(BaseModel):
    name: str
    value: float

    @model_validator(mode='before')
    @classmethod
    def handle_legacy_format(cls, data: Any) -> Any:
        # Support old API that sent {'label': ..., 'amount': ...}
        if isinstance(data, dict) and 'label' in data:
            return {'name': data['label'], 'value': data['amount']}
        return data
```

### `mode='wrap'` — full control, can short-circuit validation

```python
from typing import Any

from pydantic import BaseModel, model_validator

class CachedModel(BaseModel):
    id: int
    data: str

    @model_validator(mode='wrap')
    @classmethod
    def from_cache(cls, v: Any, handler) -> Any:
        if isinstance(v, cls):
            return v           # already an instance, skip re-parsing
        return handler(v)      # normal validation path
```

---

## Custom Types with `__get_pydantic_core_schema__` and `ValidateAs`

`ValidateAs` is a convenient 2.12+ helper. If you need 2.11 compatibility, use the `__get_pydantic_core_schema__` pattern below or an explicit intermediate-model conversion step.

### `ValidateAs` (2.12+) for custom classes built from supported types

```python
from typing import Annotated

from pydantic import BaseModel, TypeAdapter, ValidateAs

class ColorModel(BaseModel):
    hex_code: str

class Color:
    def __init__(self, hex_code: str):
        if not hex_code.startswith('#') or len(hex_code) not in (4, 7):
            raise ValueError(f'Invalid hex color: {hex_code}')
        self.hex_code = hex_code

    def __repr__(self) -> str:
        return f'Color({self.hex_code!r})'

ColorType = Annotated[Color, ValidateAs(ColorModel, lambda value: Color(value.hex_code))]

adapter = TypeAdapter(ColorType)
color = adapter.validate_python({'hex_code': '#FF5733'})
```

### Use `__get_pydantic_core_schema__` only for low-level integration

```python
from pydantic import BaseModel, Field, GetCoreSchemaHandler
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
        parsed_color = core_schema.no_info_after_validator_function(
            cls,
            core_schema.str_schema(),
        )
        return core_schema.json_or_python_schema(
            json_schema=parsed_color,
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    parsed_color,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda c: c.hex_code,
                info_arg=False,
            ),
        )

class Theme(BaseModel):
    primary_color: Color
    secondary_color: Color = Field(default_factory=lambda: Color('#FFFFFF'))

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

validation_schema = Rectangle.model_json_schema()
serialization_schema = Rectangle.model_json_schema(mode='serialization')
```

Computed fields are included in dumps by default, so keep them pure and cheap. They appear in the serialization schema, not the default validation schema, so inspect `model_json_schema(mode='serialization')` when checking response/OpenAPI contracts. For expensive deterministic values on effectively immutable or frozen models, pair `@computed_field` with `@cached_property` instead of recomputing on every access and serialization. Decorator order matters: place `@computed_field` outermost and `@cached_property` directly beneath it.
