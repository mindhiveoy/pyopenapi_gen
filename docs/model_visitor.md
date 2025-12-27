# Model Visitor (`visit/model/model_visitor.py`)

## Why This Component?

OpenAPI schemas define data structures that need to be translated into Python types. The ModelVisitor determines what kind of Python construct each schema should become (dataclass, enum, or type alias) and delegates to specialised generators for the actual code generation.

## What It Does

The ModelVisitor transforms `IRSchema` nodes into Python code:

- **Type Aliases**: Simple type mappings (e.g., `UserId = str`)
- **Enums**: Enumeration types from schemas with `enum` values
- **Dataclasses**: Object types with properties become `@dataclass` classes

## How It Works

### Architecture

ModelVisitor follows a delegation pattern with three specialised generators:

```
ModelVisitor
    ├── AliasGenerator    → Type aliases
    ├── EnumGenerator     → Enum classes
    └── DataclassGenerator → @dataclass classes
```

### Model Type Detection

The visitor determines model type using this logic:

```python
# Enum: Has name, enum values, and is string or integer type
is_enum = bool(schema.name and schema.enum and schema.type in ("string", "integer"))

# Type Alias: Has name, no properties, not an enum, not an object
is_type_alias = bool(schema.name and not schema.properties and not is_enum and schema.type != "object")

# Dataclass: Has name and either properties or is an object type
is_dataclass = bool(schema.name and (schema.properties or schema.type == "object"))
```

### Core Components

#### `ModelVisitor` Class

```python
from pyopenapi_gen.visit.model import ModelVisitor

visitor = ModelVisitor(schemas=all_schemas)
code = visitor.visit_IRSchema(schema, context)
```

**Initialisation** creates:

- `Formatter` for code formatting
- `PythonConstructRenderer` shared across generators
- Three specialised generators (alias, enum, dataclass)

**visit_IRSchema()** determines model type and delegates:

1. Detects if schema is enum, type alias, or dataclass
2. Delegates to appropriate generator
3. Returns formatted Python code string

#### `AliasGenerator`

Generates type aliases for simple type mappings:

```python
# Input: IRSchema with name="UserId", type="string"
# Output:
UserId = str
```

#### `EnumGenerator`

Generates Python Enum classes:

```python
# Input: IRSchema with name="Status", enum=["active", "inactive"]
# Output:
class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
```

#### `DataclassGenerator`

Generates dataclass definitions with proper type hints:

```python
# Input: IRSchema with name="User", properties={...}
# Output:
@dataclass
class User:
    id: int
    name: str
    email: Optional[str] = None
```

### Type Resolution

All generators use `TypeHelper` (which delegates to `UnifiedTypeService`) for:

- Mapping OpenAPI types to Python types
- Handling nullable fields with `Optional`
- Managing array types with `List`
- Resolving references to other schemas

### Import Management

Generators register required imports via `RenderContext`:

- `dataclasses.dataclass` for dataclasses
- `enum.Enum` for enums
- `typing.Optional`, `typing.List`, etc. for type hints
- References to other generated models

### Circular Reference Handling

For schemas with circular references:

- Uses forward references (string literals)
- Leverages `from __future__ import annotations`
- Ensures proper import ordering

## Usage Example

```python
from pyopenapi_gen.visit.model import ModelVisitor
from pyopenapi_gen.context import RenderContext

# Create visitor with all schemas for reference resolution
visitor = ModelVisitor(schemas=ir_spec.schemas)

# Generate code for each schema
for name, schema in ir_spec.schemas.items():
    code = visitor.visit_IRSchema(schema, context)
    if code:  # Empty string if schema shouldn't be rendered
        print(f"Generated {name}:\n{code}")
```

## Related Components

- **AliasGenerator**: Handles type alias generation
- **EnumGenerator**: Handles enum class generation
- **DataclassGenerator**: Handles dataclass generation
- **TypeHelper**: Resolves OpenAPI types to Python types
- **PythonConstructRenderer**: Formats Python code constructs
