# types/ - Unified Type Resolution System

## Why This Folder?
Central, testable type resolution replacing scattered type conversion logic. Single source of truth for OpenAPI → Python type mappings with dependency injection architecture.

## Key Dependencies
- **Input**: `IRSchema`, `IRResponse`, `IROperation` from `../../ir.py`
- **Output**: Python type strings (`str`, `List[User]`, `Optional[Dict[str, Any]]`)
- **Context**: `RenderContext` from `../../context/render_context.py`

## Essential Patterns

### 1. Service → Resolvers → Contracts
```python
# Main entry point (services/)
UnifiedTypeService → SchemaResolver/ResponseResolver → TypeContext protocol

# Usage pattern
type_service = UnifiedTypeService(schemas, responses)
python_type = type_service.resolve_schema_type(schema, context, required=True)
```

### 2. Protocol-Based Dependency Injection
```python
# contracts/protocols.py - Define interfaces
class TypeContext(Protocol):
    def add_import(self, import_str: str) -> None: ...

# resolvers/ - Use protocols, not concrete types
def resolve_type(schema: IRSchema, context: TypeContext) -> str:
    # Implementation uses context protocol
```

### 3. Error Handling
```python
from .contracts.types import TypeResolutionError

# Always wrap resolution failures
try:
    return resolve_complex_type(schema)
except Exception as e:
    raise TypeResolutionError(f"Failed to resolve {schema.name}: {e}")
```

## Critical Implementation Details

### Schema Type Resolution Priority
1. **Enum**: `schema.enum` → `UserStatusEnum`
2. **Named Reference**: `schema.type` as schema name → `User`
3. **Primitive**: `schema.type` → `str`, `int`, `bool`
4. **Array**: `schema.type="array"` → `List[ItemType]`
5. **Object**: `schema.type="object"` → `Dict[str, Any]` or dataclass
6. **Composition**: `allOf`/`oneOf`/`anyOf` → `Union[...]`

### Forward Reference Handling
```python
# For circular dependencies
if schema.name in context.forward_refs:
    return f'"{schema.name}"'  # String annotation
```

### Response Unwrapping Logic
```python
# Detect wrapper responses with single 'data' field
if (response.schema.type == "object" and 
    "data" in response.schema.properties and 
    len(response.schema.properties) == 1):
    return resolve_schema_type(response.schema.properties["data"])
```

## Dependencies on Other Systems

### From core/
- `IRSchema`, `IRResponse`, `IROperation` definitions
- Parsing context for cycle detection state

### From context/
- `RenderContext` for import management and rendering state
- Import collection and deduplication

### From helpers/ (Legacy)
- `TypeHelper` delegates to `UnifiedTypeService`
- Maintains backward compatibility during transition

## Testing Requirements

### Unit Test Pattern
```python
def test_resolve_schema_type__string_schema__returns_str():
    # Arrange
    schema = IRSchema(type="string")
    mock_context = Mock(spec=TypeContext)
    resolver = OpenAPISchemaResolver({})
    
    # Act
    result = resolver.resolve_type(schema, mock_context)
    
    # Assert
    assert result == "str"
```

### Integration Test Pattern
```python
def test_type_service__complex_schema__resolves_correctly():
    # Test with real schemas and context
    schemas = {"User": IRSchema(...)}
    responses = {"UserResponse": IRResponse(...)}
    service = UnifiedTypeService(schemas, responses)
    # Test actual resolution
```

## Common Pitfalls

1. **Context Mutation**: Always pass context, never mutate globally
2. **Missing Imports**: Resolver must call `context.add_import()` for complex types
3. **Circular Dependencies**: Check `context.forward_refs` before resolution
4. **Error Swallowing**: Wrap exceptions in `TypeResolutionError`

## Extension Points

### Adding New Resolvers
```python
# Create new resolver implementing protocols
class CustomResolver:
    def resolve_type(self, schema: IRSchema, context: TypeContext) -> str:
        # Custom logic
        pass

# Register in UnifiedTypeService
service.register_resolver(CustomResolver())
```

### New Response Strategies
```python
# strategies/response_strategy.py
class CustomResponseStrategy:
    def should_unwrap(self, response: IRResponse) -> bool:
        # Custom unwrapping logic
        pass
```