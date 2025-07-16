# helpers/ - Legacy Compatibility Layer

## Why This Folder?
Backward compatibility during transition to unified type system. Delegates to new `types/` system while maintaining old API surface for gradual migration.

## Key Dependencies
- **Delegates to**: `../types/services/UnifiedTypeService`
- **Used by**: Legacy code that hasn't migrated to unified system
- **Status**: Transitional - prefer `types/` for new code

## Critical Architecture

### 1. Legacy → Unified Delegation
```python
# type_helper.py
class TypeHelper:
    @staticmethod
    def get_python_type_for_schema(schema: IRSchema, all_schemas: Dict[str, IRSchema], 
                                   context: RenderContext, required: bool = True,
                                   resolve_alias_target: bool = False) -> str:
        """Legacy API - delegates to UnifiedTypeService"""
        type_service = UnifiedTypeService(all_schemas)
        return type_service.resolve_schema_type(
            schema, context, required, resolve_underlying=resolve_alias_target
        )
```

### 2. Type Resolution Subdirectory
```python
# type_resolution/ - Legacy individual resolvers
# These now delegate to unified system components
array_resolver.py → types/resolvers/schema_resolver.py
composition_resolver.py → types/resolvers/schema_resolver.py
object_resolver.py → types/resolvers/schema_resolver.py
primitive_resolver.py → types/resolvers/schema_resolver.py
```

## Migration Strategy

### 1. Deprecation Pattern
```python
import warnings
from ..types.services import UnifiedTypeService

def legacy_function(schema: IRSchema, context: RenderContext) -> str:
    """
    DEPRECATED: Use UnifiedTypeService.resolve_schema_type() instead.
    This function will be removed in version 2.0.
    """
    warnings.warn(
        "legacy_function is deprecated. Use UnifiedTypeService.resolve_schema_type()",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Delegate to new system
    type_service = UnifiedTypeService({})
    return type_service.resolve_schema_type(schema, context)
```

### 2. API Compatibility
```python
# Maintain old signatures while delegating
def get_return_type(operation: IROperation, context: RenderContext, 
                   schemas: Dict[str, IRSchema]) -> Tuple[str, bool]:
    """Legacy endpoint_utils function"""
    type_service = UnifiedTypeService(schemas)
    return type_service.resolve_operation_response_with_unwrap_info(operation, context)
```

## Critical Components

### type_helper.py
**Purpose**: Main legacy entry point for type resolution
```python
class TypeHelper:
    @staticmethod
    def get_python_type_for_schema(schema: IRSchema, all_schemas: Dict[str, IRSchema], 
                                   context: RenderContext, required: bool = True,
                                   resolve_alias_target: bool = False) -> str:
        """
        Legacy type resolution - delegates to UnifiedTypeService
        
        Args:
            schema: Schema to resolve
            all_schemas: All schemas in spec (for references)
            context: Render context for imports
            required: Whether field is required (affects Optional[])
            resolve_alias_target: Whether to resolve through aliases
            
        Returns:
            Python type string
        """
        type_service = UnifiedTypeService(all_schemas)
        return type_service.resolve_schema_type(
            schema, context, required, resolve_underlying=resolve_alias_target
        )
```

### endpoint_utils.py
**Purpose**: Legacy endpoint-specific utilities
```python
def get_return_type(operation: IROperation, context: RenderContext, 
                   schemas: Dict[str, IRSchema]) -> Tuple[str, bool]:
    """
    Legacy function for getting operation return type
    
    Returns:
        Tuple of (python_type, was_unwrapped)
    """
    type_service = UnifiedTypeService(schemas)
    return type_service.resolve_operation_response_with_unwrap_info(operation, context)

def get_endpoint_return_types(operation: IROperation, context: RenderContext,
                             schemas: Dict[str, IRSchema]) -> Dict[str, str]:
    """Legacy function for getting all response types"""
    type_service = UnifiedTypeService(schemas)
    return type_service.resolve_all_response_types(operation, context)
```

### type_resolution/ Subdirectory
**Purpose**: Legacy individual type resolvers

#### array_resolver.py
```python
def resolve_array_type(schema: IRSchema, context: RenderContext, 
                      all_schemas: Dict[str, IRSchema]) -> str:
    """Legacy array type resolution"""
    type_service = UnifiedTypeService(all_schemas)
    return type_service.resolve_schema_type(schema, context)
```

#### composition_resolver.py
```python
def resolve_composition_type(schema: IRSchema, context: RenderContext,
                           all_schemas: Dict[str, IRSchema]) -> str:
    """Legacy composition (allOf/oneOf/anyOf) resolution"""
    type_service = UnifiedTypeService(all_schemas)
    return type_service.resolve_schema_type(schema, context)
```

## Usage Patterns (Legacy)

### 1. Type Resolution
```python
# OLD WAY (still works, but deprecated)
from pyopenapi_gen.helpers.type_helper import TypeHelper

python_type = TypeHelper.get_python_type_for_schema(
    schema, all_schemas, context, required=True
)

# NEW WAY (preferred)
from pyopenapi_gen.types.services import UnifiedTypeService

type_service = UnifiedTypeService(all_schemas)
python_type = type_service.resolve_schema_type(schema, context, required=True)
```

### 2. Endpoint Type Resolution
```python
# OLD WAY (still works, but deprecated)
from pyopenapi_gen.helpers.endpoint_utils import get_return_type

return_type, was_unwrapped = get_return_type(operation, context, schemas)

# NEW WAY (preferred)
from pyopenapi_gen.types.services import UnifiedTypeService

type_service = UnifiedTypeService(schemas)
return_type, was_unwrapped = type_service.resolve_operation_response_with_unwrap_info(
    operation, context
)
```

## Migration Guide

### 1. Type Helper Migration
```python
# Before
from pyopenapi_gen.helpers.type_helper import TypeHelper

class MyVisitor:
    def resolve_type(self, schema: IRSchema) -> str:
        return TypeHelper.get_python_type_for_schema(
            schema, self.all_schemas, self.context, required=True
        )

# After
from pyopenapi_gen.types.services import UnifiedTypeService

class MyVisitor:
    def __init__(self, all_schemas: Dict[str, IRSchema]):
        self.type_service = UnifiedTypeService(all_schemas)
    
    def resolve_type(self, schema: IRSchema) -> str:
        return self.type_service.resolve_schema_type(
            schema, self.context, required=True
        )
```

### 2. Endpoint Utils Migration
```python
# Before
from pyopenapi_gen.helpers.endpoint_utils import get_return_type

def generate_method(self, operation: IROperation):
    return_type, was_unwrapped = get_return_type(operation, self.context, self.schemas)

# After
from pyopenapi_gen.types.services import UnifiedTypeService

def generate_method(self, operation: IROperation):
    return_type, was_unwrapped = self.type_service.resolve_operation_response_with_unwrap_info(
        operation, self.context
    )
```

## Testing Strategy

### 1. Compatibility Tests
```python
def test_type_helper__legacy_api__matches_unified_service():
    """Ensure legacy API produces same results as unified service"""
    
    # Test with legacy API
    legacy_result = TypeHelper.get_python_type_for_schema(
        schema, all_schemas, context, required=True
    )
    
    # Test with unified service
    type_service = UnifiedTypeService(all_schemas)
    unified_result = type_service.resolve_schema_type(
        schema, context, required=True
    )
    
    assert legacy_result == unified_result
```

### 2. Deprecation Warning Tests
```python
def test_legacy_function__emits_deprecation_warning():
    """Ensure legacy functions emit deprecation warnings"""
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        
        # Call legacy function
        TypeHelper.get_python_type_for_schema(schema, all_schemas, context)
        
        # Check warning was emitted
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message)
```

## Removal Timeline

### Phase 1: Deprecation (Current)
- Add deprecation warnings to all legacy functions
- Update internal code to use unified system
- Maintain backward compatibility

### Phase 2: Migration (Future)
- Remove legacy functions
- Update all external references
- Remove helpers/ directory

## Extension Points

### Custom Legacy Adapters
```python
class CustomLegacyAdapter:
    """Adapt old custom APIs to unified system"""
    
    def __init__(self, type_service: UnifiedTypeService):
        self.type_service = type_service
    
    def old_custom_method(self, schema: IRSchema) -> str:
        # Convert old API to new unified service call
        return self.type_service.resolve_schema_type(schema, context)
```

## Critical Implementation Details

### Error Handling
```python
def legacy_function(schema: IRSchema) -> str:
    """Legacy function with error handling"""
    try:
        # Delegate to unified system
        return unified_function(schema)
    except Exception as e:
        # Convert unified errors to legacy error format
        raise LegacyError(f"Legacy function failed: {e}")
```

### Performance Considerations
```python
# Cache UnifiedTypeService instances to avoid recreation
_type_service_cache = {}

def get_cached_type_service(schemas: Dict[str, IRSchema]) -> UnifiedTypeService:
    """Get cached type service for performance"""
    schema_hash = hash(frozenset(schemas.keys()))
    
    if schema_hash not in _type_service_cache:
        _type_service_cache[schema_hash] = UnifiedTypeService(schemas)
    
    return _type_service_cache[schema_hash]
```

## Common Pitfalls

1. **Direct Usage**: Using legacy functions in new code
2. **Missing Warnings**: Not emitting deprecation warnings
3. **Inconsistent Results**: Legacy and unified APIs returning different results
4. **Performance**: Creating new UnifiedTypeService instances repeatedly

## Best Practices

1. **Prefer Unified System**: Use `types/` for all new code
2. **Emit Warnings**: Always emit deprecation warnings in legacy functions
3. **Test Compatibility**: Ensure legacy and unified APIs return same results
4. **Document Migration**: Provide clear migration paths in docstrings