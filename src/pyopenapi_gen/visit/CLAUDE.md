# visit/ - Code Generation Visitor Pattern

## Why This Folder?
Transform IR objects into Python code strings using visitor pattern. Each visitor specializes in generating one aspect of the client (models, endpoints, exceptions, etc.).

## Key Dependencies
- **Input**: `IRSpec`, `IRSchema`, `IROperation` from `../ir.py`
- **Output**: Python code strings for emitters
- **Services**: `UnifiedTypeService` from `../types/services/`
- **Context**: `RenderContext` from `../context/render_context.py`

## Essential Architecture

### 1. Visitor Pattern Hierarchy
```python
# visitor.py - Base visitor
class Visitor(Generic[tNode, tRet]):
    def visit(self, node: tNode, context: RenderContext) -> tRet:
        # Dispatch to specific visit methods
        
# Concrete visitors
class ModelVisitor(Visitor[IRSchema, str]):
    def visit_schema(self, schema: IRSchema, context: RenderContext) -> str:
        # Generate dataclass/enum code
```

### 2. Generators vs Visitors
- **Visitors**: High-level orchestration, traverse IR structure
- **Generators**: Low-level code generation, create specific code blocks

```python
# endpoint/endpoint_visitor.py
class EndpointVisitor:
    def __init__(self):
        self.signature_generator = SignatureGenerator()
        self.request_generator = RequestGenerator()
        self.response_generator = ResponseHandlerGenerator()
```

## Critical Components

### model/model_visitor.py
**Purpose**: Generate dataclass and enum code from schemas
```python
def visit_schema(self, schema: IRSchema, context: RenderContext) -> str:
    if schema.enum:
        return self.enum_generator.generate_enum(schema, context)
    elif schema.type == "object":
        return self.dataclass_generator.generate_dataclass(schema, context)
    else:
        return self.alias_generator.generate_alias(schema, context)
```

### endpoint/endpoint_visitor.py
**Purpose**: Generate async method code from operations
```python
def visit_operation(self, operation: IROperation, context: RenderContext) -> str:
    # 1. Generate method signature
    signature = self.signature_generator.generate(operation, context)
    
    # 2. Generate request construction
    request_code = self.request_generator.generate(operation, context)
    
    # 3. Generate response handling
    response_code = self.response_generator.generate(operation, context)
    
    # 4. Combine into complete method
    return self.combine_method_parts(signature, request_code, response_code)
```

### client_visitor.py
**Purpose**: Generate main client class with tag-grouped methods
```python
def visit_spec(self, spec: IRSpec, context: RenderContext) -> str:
    # 1. Group operations by tag
    operations_by_tag = self.group_operations_by_tag(spec.operations)
    
    # 2. Generate client class
    # 3. Generate tag-based property methods
    # 4. Generate context manager methods
```

## Code Generation Patterns

### 1. Template-Based Generation
```python
# Use string templates for consistent formatting
METHOD_TEMPLATE = '''
async def {method_name}(self, {parameters}) -> {return_type}:
    """
    {docstring}
    """
    {body}
'''

# Fill template with generated content
method_code = METHOD_TEMPLATE.format(
    method_name=operation.operation_id,
    parameters=self.signature_generator.generate_parameters(operation),
    return_type=self.get_return_type(operation),
    docstring=self.docstring_generator.generate(operation),
    body=self.generate_method_body(operation)
)
```

### 2. Type Resolution Integration
```python
# endpoint/generators/signature_generator.py
def generate_parameters(self, operation: IROperation, context: RenderContext) -> str:
    params = []
    for param in operation.parameters:
        # Use unified type service for parameter types
        param_type = self.type_service.resolve_schema_type(
            param.schema, context, required=param.required
        )
        params.append(f"{param.name}: {param_type}")
    return ", ".join(params)
```

### 3. Import Management
```python
# Always register imports when using complex types
def generate_dataclass(self, schema: IRSchema, context: RenderContext) -> str:
    imports = []
    
    for prop_name, prop_schema in schema.properties.items():
        prop_type = self.type_service.resolve_schema_type(prop_schema, context)
        
        # Type service handles import registration
        # context.add_import() called internally
    
    return dataclass_code
```

## Specialized Generators

### endpoint/generators/
**Purpose**: Generate specific parts of endpoint methods

#### docstring_generator.py
```python
def generate_docstring(self, operation: IROperation, context: RenderContext) -> str:
    # Generate Google-style docstrings
    # Include parameter descriptions
    # Include return type information
    # Include raises information
```

#### request_generator.py
```python
def generate_request_construction(self, operation: IROperation, context: RenderContext) -> str:
    # Generate httpx.Request construction
    # Handle query parameters, headers, body
    # Apply authentication
```

#### response_handler_generator.py
```python
def generate_response_handling(self, operation: IROperation, context: RenderContext) -> str:
    # Generate match/case for status codes
    # Handle response deserialization
    # Generate exception raising
```

## Dependencies on Other Systems

### From types/
- `UnifiedTypeService` for all type resolution
- Response unwrapping detection
- Forward reference handling

### From context/
- `RenderContext` for import management
- Template rendering utilities
- Path resolution

### To emitters/
- Visitors produce code strings
- Emitters organize code into files

## Testing Requirements

### Visitor Tests
```python
def test_model_visitor__dataclass_schema__generates_correct_code():
    # Arrange
    schema = IRSchema(type="object", properties={"name": {"type": "string"}})
    context = RenderContext()
    visitor = ModelVisitor()
    
    # Act
    code = visitor.visit_schema(schema, context)
    
    # Assert
    assert "@dataclass" in code
    assert "name: str" in code
```

### Generator Tests
```python
def test_signature_generator__operation_with_params__generates_correct_signature():
    # Test specific code generation components
    operation = IROperation(parameters=[...])
    generator = SignatureGenerator()
    
    signature = generator.generate(operation, context)
    
    # Verify parameter types, defaults, etc.
```

## Extension Points

### Adding New Visitors
```python
# Create new visitor for new code aspects
class CustomVisitor(Visitor[IRCustomNode, str]):
    def visit_custom_node(self, node: IRCustomNode, context: RenderContext) -> str:
        # Custom code generation logic
        pass
```

### Adding New Generators
```python
# endpoint/generators/custom_generator.py
class CustomGenerator:
    def __init__(self, type_service: UnifiedTypeService):
        self.type_service = type_service
    
    def generate(self, operation: IROperation, context: RenderContext) -> str:
        # Custom code generation logic
        pass
```

## Critical Implementation Details

### Error Handling in Visitors
```python
def visit_schema(self, schema: IRSchema, context: RenderContext) -> str:
    try:
        return self.generate_code(schema, context)
    except Exception as e:
        # Add context to errors
        raise CodeGenerationError(f"Failed to generate code for schema {schema.name}: {e}")
```

### Context Management
```python
# Always use context for imports and state
def generate_method(self, operation: IROperation, context: RenderContext) -> str:
    # Register imports
    context.add_import("from typing import Optional")
    
    # Use context for type resolution
    return_type = self.type_service.resolve_operation_response_type(operation, context)
    
    # Return code string
    return method_code
```

### Code Formatting
```python
# Use consistent indentation and formatting
def format_method_body(self, lines: List[str]) -> str:
    # Ensure proper indentation
    formatted_lines = []
    for line in lines:
        if line.strip():
            formatted_lines.append(f"    {line}")  # 4-space indent
        else:
            formatted_lines.append("")
    return "\n".join(formatted_lines)
```