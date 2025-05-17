# Intermediate Representation (IR) Model Documentation

## 1. Overview

The Intermediate Representation (IR) model is a set of Python dataclasses that provide a structured, validated, and Python-native view of the OpenAPI specification. It serves as the single source of truth for all subsequent code generation steps, decoupling them from the complexities of the raw OpenAPI spec format.

## 2. Core Components

### 2.1 IRSchema

The `IRSchema` class is the fundamental building block of the IR model, representing OpenAPI schemas.

```python
@dataclass
class IRSchema:
    # Basic Schema Information
    name: Optional[str] = None
    type: Optional[str] = None  # Basic types or reference to another schema
    format: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    
    # Structural Properties
    required: List[str] = field(default_factory=list)
    properties: Dict[str, IRSchema] = field(default_factory=dict)
    items: Optional[IRSchema] = None  # For arrays
    additional_properties: Optional[Union[bool, IRSchema]] = None
    
    # Type-Specific Properties
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None
    example: Optional[Any] = None
    is_nullable: bool = False
    
    # Composition Keywords
    any_of: Optional[List[IRSchema]] = None
    one_of: Optional[List[IRSchema]] = None
    all_of: Optional[List[IRSchema]] = None
    
    # Special Flags
    is_data_wrapper: bool = False  # For simple {"data": OtherSchema} wrappers
    
    # Internal State
    _from_unresolved_ref: bool = False  # Placeholder for unresolvable $ref
    _refers_to_schema: Optional[IRSchema] = None  # Link to actual definition
    _is_circular_ref: bool = False  # Marks circular references
    _circular_ref_path: Optional[str] = None  # Path of detected cycle
```

#### 2.1.1 Schema Types

The `type` field supports the following basic types:
- `"object"`: For object schemas
- `"array"`: For array schemas
- `"string"`: For string values
- `"integer"`: For integer values
- `"number"`: For numeric values
- `"boolean"`: For boolean values
- `"null"`: For null values

#### 2.1.2 Post-Initialization Processing

The `__post_init__` method performs several important validations and transformations:

1. **Name Sanitization**
   - Sanitizes schema names to valid Python identifiers
   - Uses `NameSanitizer.sanitize_class_name`
   - Ensures consistent naming across the codebase

2. **Type Validation**
   - Ensures that reference types don't have conflicting structural fields
   - Validates against basic OpenAPI types
   - Performs runtime type checking through type hints

3. **Nested Schema Conversion**
   - Converts nested dictionaries to `IRSchema` instances
   - Handles properties, items, and composition keywords
   - Maintains reference integrity during conversion

### 2.2 IRSpec

The root container for the entire OpenAPI specification:

```python
@dataclass
class IRSpec:
    title: str
    version: str
    description: Optional[str] = None
    schemas: Dict[str, IRSchema] = field(default_factory=dict)
    operations: List[IROperation] = field(default_factory=list)
    servers: List[str] = field(default_factory=list)
```

### 2.3 IROperation

Represents an API operation (endpoint):

```python
@dataclass
class IROperation:
    operation_id: str
    method: HTTPMethod
    path: str
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[IRParameter] = field(default_factory=list)
    request_body: Optional[IRRequestBody] = None
    responses: List[IRResponse] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
```

### 2.4 Supporting Classes

#### 2.4.1 IRParameter
```python
@dataclass
class IRParameter:
    name: str
    param_in: str  # "path", "query", "header", "cookie"
    required: bool
    schema: IRSchema
    description: Optional[str] = None
```

#### 2.4.2 IRRequestBody
```python
@dataclass
class IRRequestBody:
    required: bool
    content: Dict[str, IRSchema]  # media-type → schema mapping
    description: Optional[str] = None
```

#### 2.4.3 IRResponse
```python
@dataclass
class IRResponse:
    status_code: str  # "default" or specific status like "200"
    description: Optional[str]
    content: Dict[str, IRSchema]  # media-type → schema mapping
    stream: bool = False  # For binary/streaming responses
    stream_format: Optional[str] = None
```

## 3. Reference Resolution and Cycle Detection

### 3.1 Reference Resolution

The IR model handles schema references through several mechanisms:

1. **Direct References**
   - When `type` is a string not matching basic types
   - The schema acts as a reference to another named schema
   - References are resolved through `resolve_schema_ref`

2. **Property References**
   - Properties can reference other schemas
   - Handled through `_refers_to_schema` field
   - Property cycles are detected and marked

3. **Composition References**
   - `allOf`, `anyOf`, `oneOf` can contain references
   - Each component is resolved independently
   - Composition cycles are detected and handled

### 3.2 Cycle Detection

The system implements a robust cycle detection mechanism:

1. **Direct Cycles**
   - A schema directly references itself
   - Detected through `ParsingContext.currently_parsing`
   - Logged with detailed cycle path information

2. **Indirect Cycles**
   - Multiple schemas form a cycle
   - Tracked through `ParsingContext.parsing_path`
   - Full cycle path is preserved for debugging

3. **Property-Level Cycles**
   - Cycles formed through nested properties
   - Handled by `mark_cyclic_property_references`
   - Properties involved in cycles are marked as unresolved

4. **Maximum Depth Protection**
   - Controlled by `PYOPENAPI_MAX_DEPTH` environment variable
   - Default: 100 levels of recursion
   - Exceeding depth creates a placeholder schema

### 3.3 Logging and Debugging

The system provides comprehensive logging for debugging:

1. **Cycle Detection Logging**
   - Enabled by `PYOPENAPI_DEBUG_CYCLES` environment variable
   - Logs cycle paths and detection points
   - Includes schema names and reference chains

2. **Reference Resolution Logging**
   - Tracks reference resolution attempts
   - Logs unresolved references
   - Records cycle detection events

3. **Performance Monitoring**
   - Logs recursion depth
   - Tracks schema parsing progress
   - Monitors cache hits and misses

## 4. Best Practices

### 4.1 Schema Creation

```python
# Basic schema
schema = IRSchema(
    name="User",
    type="object",
    properties={
        "id": IRSchema(type="integer", format="int64"),
        "name": IRSchema(type="string")
    },
    required=["id", "name"]
)

# Array schema
array_schema = IRSchema(
    name="UserList",
    type="array",
    items=schema
)

# Reference schema
ref_schema = IRSchema(
    name="UserRef",
    type="User"  # References the User schema
)
```

### 4.2 Cycle Handling

```python
# Creating a circular reference
circular_schema = IRSchema(
    name="Node",
    type="object",
    properties={
        "next": IRSchema(type="Node")
    }
)
circular_schema._is_circular_ref = True
circular_schema._circular_ref_path = "Node -> Node"
```

### 4.3 Composition

```python
# Using composition keywords
composite_schema = IRSchema(
    name="Composite",
    all_of=[
        IRSchema(type="object", properties={"id": IRSchema(type="integer")}),
        IRSchema(type="object", properties={"name": IRSchema(type="string")})
    ]
)
```

## 5. Testing Guidelines

1. **Basic Schema Tests**
   - Test creation of simple schemas
   - Verify property access and modification
   - Check type validation
   - Test name sanitization

2. **Reference Tests**
   - Test direct and indirect references
   - Verify reference resolution
   - Check cycle detection
   - Test reference caching

3. **Composition Tests**
   - Test `allOf`, `anyOf`, `oneOf`
   - Verify merging behavior
   - Check nullable handling
   - Test composition cycles

4. **Edge Cases**
   - Test maximum depth handling
   - Verify cycle detection in complex scenarios
   - Check error handling for invalid schemas
   - Test logging and debugging features

## 6. Implementation Notes

### 6.1 Environment Variables

The following environment variables control the behavior of the IR model:

- `PYOPENAPI_DEBUG_CYCLES`: Enable cycle detection debugging (default: "0")
- `PYOPENAPI_MAX_CYCLES`: Maximum number of cycles to handle (default: "0")
- `PYOPENAPI_MAX_DEPTH`: Maximum recursion depth (default: "100")

### 6.2 Error Handling

The IR model uses several mechanisms for error handling:

1. **Validation Errors**
   - Type checking through type hints
   - Runtime validation in `__post_init__`
   - Assertions for critical preconditions
   - Detailed error messages for debugging

2. **Reference Resolution Errors**
   - Unresolved references marked with `_from_unresolved_ref`
   - Circular references marked with `_is_circular_ref`
   - Maximum depth exceeded handling
   - Comprehensive error logging

3. **Composition Errors**
   - Validation of composition keyword usage
   - Handling of conflicting properties
   - Nullable type handling
   - Detailed error reporting

### 6.3 Performance Considerations

1. **Memory Usage**
   - Schemas are cached in `ParsingContext.parsed_schemas`
   - Circular references prevent infinite recursion
   - Maximum depth limits prevent stack overflow
   - Efficient memory management for large schemas

2. **Processing Speed**
   - Reference resolution is optimized through caching
   - Cycle detection uses efficient path tracking
   - Composition operations are performed lazily
   - Schema parsing is optimized for common cases

3. **Caching Strategy**
   - Schema caching in `ParsingContext`
   - Reference resolution caching
   - Name sanitization caching
   - Type validation caching

## 7. Future Improvements

1. **Schema Validation**
   - Add more comprehensive schema validation
   - Implement custom validation rules
   - Add support for custom validators
   - Improve error reporting

2. **Reference Resolution**
   - Improve handling of external references
   - Add support for reference aliases
   - Implement reference resolution caching
   - Enhance cycle detection

3. **Composition**
   - Add support for more composition keywords
   - Improve merging strategies
   - Add validation for composition rules
   - Enhance composition error handling

4. **Testing**
   - Add more comprehensive test coverage
   - Implement property-based testing
   - Add performance benchmarks
   - Enhance debugging tools

5. **Performance**
   - Optimize memory usage for large schemas
   - Improve caching strategies
   - Enhance parallel processing
   - Add performance monitoring

6. **Documentation**
   - Add more code examples
   - Include troubleshooting guide
   - Document common patterns
   - Add API reference 