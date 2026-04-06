# Advanced Pydantic v2 Patterns

## Discriminated Unions

Use when a field can be one of several model types distinguished by a `type` tag. Pydantic routes validation to the correct model without trying each in turn.

```python
from typing import Literal, Annotated, Union
from pydantic import BaseModel, Field

class CatPayload(BaseModel):
    type: Literal['cat']
    indoor: bool
    breed: str

class DogPayload(BaseModel):
    type: Literal['dog']
    trained: bool
    size: Literal['small', 'medium', 'large']

class BirdPayload(BaseModel):
    type: Literal['bird']
    can_talk: bool
    species: str

AnimalPayload = Annotated[
    Union[CatPayload, DogPayload, BirdPayload],
    Field(discriminator='type'),
]

class AdoptionRequest(BaseModel):
    applicant_name: str
    animal: AnimalPayload   # parsed to the correct subtype automatically

req = AdoptionRequest.model_validate({
    'applicant_name': 'Alice',
    'animal': {'type': 'dog', 'trained': True, 'size': 'medium'},
})
assert isinstance(req.animal, DogPayload)
```

### Discriminated Union with Alias

```python
from typing import Annotated, Any, Literal, Union

from pydantic import AliasChoices, BaseModel, Discriminator, Field, Tag, TypeAdapter

def get_kind(value: Any) -> str | None:
    if isinstance(value, dict):
        return value.get('kind') or value.get('event_type')
    return getattr(value, 'kind', None) or getattr(value, 'event_type', None)

class ClickEvent(BaseModel):
    kind: Literal['click'] = Field(validation_alias=AliasChoices('kind', 'event_type'))
    x: int
    y: int

class KeyEvent(BaseModel):
    kind: Literal['key'] = Field(validation_alias=AliasChoices('kind', 'event_type'))
    key: str

Event = Annotated[
    Union[
        Annotated[ClickEvent, Tag('click')],
        Annotated[KeyEvent, Tag('key')],
    ],
    Discriminator(get_kind),
]

event = TypeAdapter(Event).validate_python({'event_type': 'click', 'x': 10, 'y': 20})
assert isinstance(event, ClickEvent)
assert event.kind == 'click'
```

`validation_alias` is input-only. If serialized output must also use the external field name, add `serialization_alias='event_type'`, then serialize with `by_alias=True` or enable `serialize_by_alias=True` in `model_config`. A full `alias=` strategy couples input and output names, so use it only when that tighter contract is intended, or pair it with `validate_by_name=True` when canonical field names must still be accepted.

---

## Generic Models

```python
from typing import Generic, TypeVar

from pydantic import BaseModel, Field, computed_field, model_validator

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(gt=0)
    page_size: int = Field(gt=0)
    has_next: bool

    @computed_field
    @property
    def total_pages(self) -> int:
        return -(-self.total // self.page_size)  # ceiling division

class UserSummary(BaseModel):
    id: int
    name: str
    email: str

# Concrete instantiation
class UserPage(PaginatedResponse[UserSummary]):
    pass

# Or inline
response = PaginatedResponse[UserSummary].model_validate({
    'items': [{'id': 1, 'name': 'Alice', 'email': 'a@b.com'}],
    'total': 100,
    'page': 1,
    'page_size': 20,
    'has_next': True,
})

# At boundaries, always parametrize the generic or use a concrete subclass.
# Unparametrized generic models can weaken validation and, for bounded/defaulted
# type variables, even lose subtype data during validation or serialization.

# Wrapping any success/error response
class APIResult(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None

    @model_validator(mode='after')
    def check_state(self) -> 'APIResult[T]':
        if self.success:
            if self.error is not None:
                raise ValueError('Successful results must not include error details')
            if self.data is None:
                raise ValueError('Successful results must include data')
        else:
            if self.data is not None:
                raise ValueError('Failed results must not include success data')
            if self.error is None:
                raise ValueError('Failed results must include error details')
        return self

# Prefer a non-optional T here. Public API contracts are often clearer as separate
# success/error models or a discriminated union instead of one nullable envelope.

    @classmethod
    def ok(cls, data: T) -> 'APIResult[T]':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'APIResult[T]':
        return cls(success=False, error=error)
```

---

## `RootModel` — Wrapping a Bare Type

Use when your model IS a single value (list, dict, custom type) rather than having named fields.

Prefer `TypeAdapter` for one-off validation of a bare type. Reach for `RootModel` when you want a named model type with config, methods, schema, or serializers around that root value.

```python
from pydantic import RootModel

# Validated list
class TagList(RootModel[list[str]]):
    def __iter__(self):
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

tags = TagList.model_validate(['python', 'pydantic', 'validation'])
tags.model_dump()   # ['python', 'pydantic', 'validation']

# Validated dict / mapping
class FeatureFlags(RootModel[dict[str, bool]]):
    def is_enabled(self, flag: str) -> bool:
        return self.root.get(flag, False)

flags = FeatureFlags.model_validate({'dark_mode': True, 'beta': False})
flags.is_enabled('dark_mode')  # True
```

---

## Recursive / Self-Referential Models

```python
from pydantic import BaseModel, Field

class TreeNode(BaseModel):
    value: int
    children: list['TreeNode'] = Field(default_factory=list)

class Comment(BaseModel):
    id: int
    text: str
    author: str
    replies: list['Comment'] = Field(default_factory=list)

tree = TreeNode.model_validate({
    'value': 1,
    'children': [
        {'value': 2, 'children': []},
        {'value': 3, 'children': [{'value': 4, 'children': []}]},
    ],
})
```

Quoted recursive annotations keep the snippet copy-paste safe. The alternative is enabling `from __future__ import annotations` at the top of the module.

These examples are acyclic. Cyclic graphs or ORM back-references need explicit cycle handling; otherwise validation can raise `recursion_loop` and serialization can fail on circular references.

---

## Partial Updates (PATCH Endpoints)

For untrusted PATCH payloads, merge only the provided fields and then revalidate the target model. `model_copy(update=...)` does **not** validate the update mapping, so treat it as a trusted-data shortcut.

```python
from pydantic import BaseModel, ConfigDict

class UserProfile(BaseModel):
    name: str
    email: str
    bio: str | None = None
    avatar_url: str | None = None

class UserProfileUpdate(BaseModel):
    """Nullable fields are both omittable and nullable in this PATCH schema."""

    model_config = ConfigDict(extra='forbid')

    bio: str | None = None
    avatar_url: str | None = None

def patch_user(existing: UserProfile, patch: UserProfileUpdate) -> UserProfile:
    # Only update fields explicitly provided in the PATCH body.
    # This shortcut is only for shallow, round-trippable models like this one.
    # Exclude computed fields and prefer round_trip=True to avoid serializer drift.
    updates = patch.model_dump(exclude_unset=True)
    merged = existing.model_dump(
        round_trip=True,
        exclude=set(type(existing).model_computed_fields),
    )
    merged.update(updates)
    return UserProfile.model_validate(merged)

# Example
current = UserProfile(name="Alice", email="a@b.com")
patch = UserProfileUpdate(bio="Python developer")   # only bio was sent

updated = patch_user(current, patch)
# UserProfile(name='Alice', email='a@b.com', bio='Python developer', avatar_url=None)
```

For nested models, define an explicit recursive merge strategy or dedicated nested update models instead of reusing this shallow-merge pattern blindly.

For omittable-but-non-nullable fields such as `email`, use a dedicated fields-set or sentinel pattern rather than `field: T | None = None`, because that public PATCH schema explicitly allows `null`.

```python
from typing_extensions import NotRequired, TypedDict

from pydantic import ConfigDict, TypeAdapter

class UserProfilePatch(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')

    email: NotRequired[str]        # omittable, but not nullable
    bio: NotRequired[str | None]   # omittable and nullable

patch_adapter = TypeAdapter(UserProfilePatch)
patch_data = patch_adapter.validate_python({'email': 'new@example.com'})
```

Dict-shaped PATCH contracts are often the simplest public schema when some fields are omittable-but-non-nullable and others are genuinely nullable. Add `__pydantic_config__ = ConfigDict(extra='forbid')` when unknown keys should fail instead of being ignored.

**Trusted-data shortcut:**

```python
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    email: str
    bio: str | None = None

current = UserProfile(name="Alice", email="a@b.com")
trusted_updates = {'bio': 'Already validated elsewhere'}
updated = current.model_copy(update=trusted_updates)  # skips validation
```

For nested fields, pass already-validated submodels here or revalidate after merging. `model_copy(update={'child': {...}})` can otherwise leave raw dicts inside the copied model.

**Prefer explicit update models over generated “partial” models.**

If you must generate them dynamically, derive from `model.model_fields` / `FieldInfo` metadata rather than bare `get_type_hints()`, or you will lose aliases, constraints, defaults, and validators.

---

## Model Inheritance

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BaseEntity(BaseModel):
    """Base for all DB-persisted entities."""
    id: int
    created_at: datetime
    updated_at: datetime

class UserBase(BaseModel):
    """Fields shared by create and read schemas."""
    name: str
    email: str

class UserCreate(UserBase):
    """Request body for POST /users — no id yet."""
    password: str

class UserResponse(UserBase, BaseEntity):
    """Response schema — includes DB-assigned fields."""
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)
```

**Rule of thumb:** Separate *create*, *update*, and *response* schemas when the shapes, defaults, security rules, or serialization needs differ. If the contract is intentionally identical, reuse can be reasonable.

---

## Dynamic Model Creation (`create_model`)

```python
from pydantic import BaseModel, Field, create_model

# Build a model from a runtime schema
def build_config_model(schema: dict[str, type]) -> type[BaseModel]:
    fields = {key: (value, ...) for key, value in schema.items()}
    return create_model('DynamicConfig', **fields)

Config = build_config_model({'host': str, 'port': int, 'debug': bool})
cfg = Config(host='localhost', port=8000, debug=False)

# With Field constraints
ReportModel = create_model(
    'ReportModel',
    title=(str, Field(min_length=1, max_length=200)),
    rows=(list[dict], Field(default_factory=list)),
)
```

Use trusted annotations only when building models dynamically. If string annotations or imported symbols can be influenced by untrusted input, evaluating them can execute arbitrary code.

---

## JSON Schema Generation and Customization

```python
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class ProductSchema(BaseModel):
    model_config = ConfigDict(title='Product API Schema')

    name: str = Field(description="Product name", examples=["Widget Pro"])
    price: Decimal = Field(gt=Decimal('0'), description="Price in USD")

# Full JSON schema
schema = ProductSchema.model_json_schema()

# Add extra OpenAPI fields without affecting validation
class MyModel(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            'x-internal': False,
            'x-version': '2.0',
        }
    )
```

---

## Serialization Customization

### `@field_serializer`

```python
from datetime import datetime, timezone

from pydantic import AwareDatetime, BaseModel, field_serializer

class Report(BaseModel):
    title: str
    created_at: AwareDatetime
    tags: set[str]

    @field_serializer('created_at', when_used='json')
    def serialize_dt(self, dt: datetime) -> str:
        return dt.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    @field_serializer('tags')
    def serialize_tags(self, tags: set[str]) -> list[str]:
        return sorted(tags)  # stable serialization order
```

### `@model_serializer`

```python
from typing_extensions import TypedDict

from pydantic import BaseModel, model_serializer

class MoneyOut(TypedDict):
    amount_cents: int
    currency: str
    formatted: str

class Money(BaseModel):
    amount_cents: int
    currency: str

    @model_serializer(return_type=MoneyOut)
    def to_dict(self) -> MoneyOut:
        return {
            'amount_cents': self.amount_cents,
            'currency': self.currency,
            'formatted': f'{self.currency} {self.amount_cents / 100:.2f}',
        }
```

If you return a plain `dict` from `@model_serializer`, the serialization schema widens to a generic object. Use `return_type` or a dedicated output model/TypedDict when the serialized contract matters, and inspect `model_json_schema(mode='serialization')` when checking that output contract.

---

## Performance Tips

- **Benchmark `model_validate_json()`** against `model_validate(json.loads(...))` on your workload. It often wins because it avoids an extra Python JSON decode step, but the gap is data-shape dependent.
- **Benchmark `model_dump_json()`** against `json.dumps(model.model_dump(mode='json'))` for the same reason.
- **Cache `TypeAdapter`** instances — creating them is expensive:

```python
from pydantic import TypeAdapter

# Standalone type validation without defining another wrapper model
user_list_adapter = TypeAdapter(list[dict[str, str]])
raw_bytes = b'[{"name":"alice"},{"name":"bob"}]'

# Reuse everywhere
users = user_list_adapter.validate_json(raw_bytes)
```

- **`model_config = ConfigDict(frozen=True)`** makes the model faux-immutable and potentially hashable if all fields are hashable.
- **Prefer v2 validator APIs** (`Annotated`, `@field_validator`, `@model_validator`) over v1 `@validator`.
