# Loader System (`core/loader/`)

## Why This Component?

OpenAPI specifications come in various formats (YAML, JSON) with complex nested structures including `$ref` references, inline schemas, and nested parameters. The loader system provides a clean transformation layer between raw specification data and the typed Intermediate Representation (IR) that the rest of the code generation pipeline relies on.

## What It Does

The loader system transforms validated OpenAPI specification dictionaries into strongly-typed IR dataclasses:

- **SpecLoader**: Main class that orchestrates the transformation
- **load_ir_from_spec()**: Convenience function for quick IR generation
- **Schema extraction**: Builds `IRSchema` objects from components/schemas
- **Operation parsing**: Creates `IROperation` objects from paths
- **Inline enum extraction**: Promotes inline enums to named schemas

## How It Works

### Core Components

#### `SpecLoader` Class

The main entry point for spec transformation:

```python
from pyopenapi_gen.core.loader.loader import SpecLoader

# Initialise with a validated spec dictionary
loader = SpecLoader(spec)

# Validate (optional, returns warnings)
warnings = loader.validate()

# Transform to IR
ir_spec: IRSpec = loader.load_ir()
```

**Initialisation** extracts and stores:

- API metadata (title, version, description)
- Raw component sections (schemas, parameters, responses, requestBodies)
- Paths for operation parsing
- Server URLs

**load_ir()** orchestrates:

1. Schema building via `build_schemas()`
2. Inline enum extraction via `extract_inline_enums()`
3. Operation parsing via `parse_operations()`
4. IRSpec assembly with all collected data

#### Convenience Function

```python
from pyopenapi_gen.core.loader.loader import load_ir_from_spec

# Quick transformation without manual SpecLoader setup
ir_spec = load_ir_from_spec(spec_dict)
```

### Sub-modules

| Module | Purpose |
|--------|---------|
| `schemas/` | Schema building and inline enum extraction |
| `operations/` | Path and operation parsing |
| `parameters/` | Parameter extraction and normalisation |
| `responses/` | Response schema extraction |

### Design by Contract

The loader follows Design by Contract principles:

- **Preconditions**: Validates input spec has required fields (`openapi`, `paths`)
- **Postconditions**: Ensures output IR objects are properly formed
- **Invariants**: Maintains consistent state throughout transformation

### Environment Variables

- `PYOPENAPI_MAX_CYCLES`: Controls cycle detection limit (default: 0, unlimited)

## Integration

The loader is called by `ClientGenerator` early in the pipeline:

```
ClientGenerator.generate()
    └── SpecLoader(spec).load_ir()
            ├── build_schemas()
            ├── extract_inline_enums()
            └── parse_operations()
```

The resulting `IRSpec` is then passed to visitors for code generation.
