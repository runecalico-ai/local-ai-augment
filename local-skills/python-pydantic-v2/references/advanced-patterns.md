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
from pydantic import Discriminator, Tag

def get_kind(v) -> str | None:
    if isinstance(v, dict):
        return v.get('kind') or v.get('event_type')
    return getattr(v, 'kind', None)

class ClickEvent(BaseModel):
    kind: Literal['click']
    x: int
    y: int

class KeyEvent(BaseModel):
    kind: Literal['key']
    key: str

Event = Annotated[
    Union[
        Annotated[ClickEvent, Tag('click')],
        Annotated[KeyEvent, Tag('key')],
    ],
    Discriminator(get_kind),
]
```

---

## Generic Models

```python
from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool

    @property
    def total_pages(self) -> int:
        return -(-self.total // self.page_size)  # ceiling division

# Concrete instantiation
class UserPage(PaginatedResponse[User]):
    pass

# Or inline
response = PaginatedResponse[User].model_validate({
    'items': [{'id': 1, 'name': 'Alice', 'email': 'a@b.com'}],
    'total': 100,
    'page': 1,
    'page_size': 20,
    'has_next': True,
})

# Wrapping any success/error response
class APIResult(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None

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
from __future__ import annotations  # still needed for forward reference on self-referential models
from pydantic import BaseModel, Field

class TreeNode(BaseModel):
    value: int
    children: list[TreeNode] = Field(default_factory=list)

class Comment(BaseModel):
    id: int
    text: str
    author: str
    replies: list[Comment] = Field(default_factory=list)

tree = TreeNode.model_validate({
    'value': 1,
    'children': [
        {'value': 2, 'children': []},
        {'value': 3, 'children': [{'value': 4, 'children': []}]},
    ],
})
```

---

## Partial Updates (PATCH Endpoints)

Use `model_copy(update=...)` with `exclude_unset` to implement PATCH semantics safely.

```python
from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    email: str
    bio: str | None = None
    avatar_url: str | None = None

class UserProfileUpdate(BaseModel):
    """All fields optional — only provided fields are updated."""
    name: str | None = None
    email: str | None = None
    bio: str | None = None
    avatar_url: str | None = None

def patch_user(existing: UserProfile, patch: UserProfileUpdate) -> UserProfile:
    # Only update fields explicitly provided in the PATCH body
    updates = patch.model_dump(exclude_unset=True)
    return existing.model_copy(update=updates)

# Example
current = UserProfile(name="Alice", email="a@b.com")
patch = UserProfileUpdate(bio="Python developer")   # only bio was sent

updated = patch_user(current, patch)
# UserProfile(name='Alice', email='a@b.com', bio='Python developer', avatar_url=None)
```

**Generating a partial model programmatically:**

```python
from typing import get_type_hints
from pydantic import BaseModel, create_model

def make_partial(model: type[BaseModel]) -> type[BaseModel]:
    """Return a new model with all fields made optional (None default)."""
    hints = get_type_hints(model)
    return create_model(
        f'Partial{model.__name__}',
        **{
            name: (hint | None, None)
            for name, hint in hints.items()
            if name in model.model_fields
        }
    )

# Usage
PartialUser = make_partial(UserProfile)
patch = PartialUser(bio="Python dev")  # only bio set — all others are None
```

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

**Rule:** Separate *create*, *update*, and *response* schemas. Never reuse the same model for input and output.

---

## Dynamic Model Creation (`create_model`)

```python
from pydantic import create_model, Field

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

---

## JSON Schema Generation and Customization

```python
from pydantic import BaseModel, Field

class ProductSchema(BaseModel):
    name: str = Field(description="Product name", examples=["Widget Pro"])
    price: float = Field(gt=0, description="Price in USD")

# Full JSON schema
schema = ProductSchema.model_json_schema()

# Title override
schema = ProductSchema.model_json_schema(title="Product API Schema")

# Add extra OpenAPI fields without affecting validation
from pydantic import BaseModel, ConfigDict

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
from pydantic import field_serializer
from datetime import datetime

class Report(BaseModel):
    title: str
    created_at: datetime
    tags: set[str]

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime) -> str:
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    @field_serializer('tags')
    def serialize_tags(self, tags: set[str]) -> list[str]:
        return sorted(tags)  # stable serialization order
```

### `@model_serializer`

```python
from pydantic import model_serializer

class Money(BaseModel):
    amount: int    # stored in cents
    currency: str

    @model_serializer
    def to_dict(self) -> dict:
        return {
            'amount': self.amount / 100,   # serialize as dollars
            'currency': self.currency,
            'formatted': f'{self.currency} {self.amount / 100:.2f}',
        }
```

---

## Performance Tips

- **Prefer `model_validate_json()`** over `model_validate(json.loads(...))` — the JSON path is ~2x faster (pure Rust).
- **Use `model_dump_json()`** over `json.dumps(model.model_dump())` for the same reason.
- **Cache `TypeAdapter`** instances — creating them is expensive:

```python
from pydantic import TypeAdapter

# Create once at module level
user_list_adapter = TypeAdapter(list[User])

# Reuse everywhere
users = user_list_adapter.validate_json(raw_bytes)
```

- **`model_config = ConfigDict(frozen=True)`** enables hashing and improves cache performance for immutable value objects.
- **Avoid `@validator` (v1 style)** — `@field_validator` is faster because it avoids Python overhead in the validation loop.
