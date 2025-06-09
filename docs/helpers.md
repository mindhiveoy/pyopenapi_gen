# Helpers (`helpers/`)

This directory provides utility classes and functions that support various tasks within the code generation pipeline, promoting code reuse and separation of concerns.

## Current Modules

### Type Resolution (`helpers/type_resolution/`)
**DEPRECATED**: Legacy type resolution system, now delegates to unified type system:
- **`resolver.py`**: Main orchestrator that delegates to `UnifiedTypeService`
- **`array_resolver.py`**: Array-specific type resolution (legacy)
- **`composition_resolver.py`**: Handles `allOf`, `oneOf`, `anyOf` compositions (legacy)
- **`object_resolver.py`**: Object schema resolution (legacy)  
- **`primitive_resolver.py`**: Primitive type resolution (legacy)
- **`named_resolver.py`**: Named schema resolution (legacy)
- **`finalizer.py`**: Type finalization utilities (legacy)

**Note**: These resolvers are maintained for backward compatibility but delegate to the new unified type resolution system in `types/` package.

### Core Utilities
- **`type_helper.py`**: Main interface for type resolution, now delegates to `UnifiedTypeService`
- **`type_cleaner.py`**: Utilities for cleaning and formatting type strings
- **`endpoint_utils.py`**: Endpoint-specific utilities including request/response type resolution
- **`url_utils.py`**: URL manipulation utilities

## Migration to Unified System

The type resolution logic has been refactored into a new unified system:

**Old Pattern**:
```python
from pyopenapi_gen.helpers.type_helper import TypeHelper
python_type = TypeHelper.get_python_type_for_schema(schema, schemas, context, required)
```

**New Pattern** (Recommended):
```python
from pyopenapi_gen.types.services import UnifiedTypeService
type_service = UnifiedTypeService(schemas, responses)
python_type = type_service.resolve_schema_type(schema, context, required)
```

The old `TypeHelper` interface is maintained for backward compatibility and delegates to the unified system.

## Architecture Benefits

The unified type resolution system provides:
- **Consistency**: Single source of truth for type resolution
- **Testability**: Clean architecture with dependency injection
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Protocol-based design for easy additions 