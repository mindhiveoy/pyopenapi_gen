# emitters/ - File Organization and Output

## Why This Folder?
Transform visitor-generated code strings into properly structured Python packages. Handles file creation, import resolution, and package organization.

## Key Dependencies
- **Input**: Code strings from `../visit/` visitors
- **Output**: Python files in target package structure
- **Services**: `FileManager` from `../context/file_manager.py`
- **Context**: `RenderContext` for import management

## Essential Architecture

### 1. Emitter Responsibilities
```python
# Each emitter handles one aspect of the generated client
models_emitter.py     → models/ directory with dataclasses/enums
endpoints_emitter.py  → endpoints/ directory with operation methods
client_emitter.py     → client.py main interface
core_emitter.py       → core/ directory with runtime dependencies
exceptions_emitter.py → exceptions.py error hierarchy
```

### 2. Package Structure Creation
```python
# Target structure for generated client
output_package/
├── __init__.py           # Package initialization
├── client.py            # Main client class
├── models/              # Data models
│   ├── __init__.py
│   ├── user.py
│   └── order.py
├── endpoints/           # Operation methods
│   ├── __init__.py
│   ├── users.py
│   └── orders.py
├── core/                # Runtime dependencies
│   ├── __init__.py
│   ├── auth/
│   ├── exceptions.py
│   └── http_transport.py
└── exceptions.py        # Exception hierarchy
```

## Critical Components

### models_emitter.py
**Purpose**: Create models/ directory with dataclass and enum files
```python
def emit_models(self, schemas: Dict[str, IRSchema], context: RenderContext) -> None:
    # 1. Group schemas by module (one file per schema or logical grouping)
    # 2. Generate code for each schema using ModelVisitor
    # 3. Create __init__.py with imports
    # 4. Write files to models/ directory
    
    for schema_name, schema in schemas.items():
        module_name = self.get_module_name(schema_name)
        file_path = self.output_path / "models" / f"{module_name}.py"
        
        # Generate model code
        model_code = self.model_visitor.visit_schema(schema, context)
        
        # Write file
        self.file_manager.write_file(file_path, model_code)
```

### endpoints_emitter.py
**Purpose**: Create endpoints/ directory with operation methods grouped by tag
```python
def emit_endpoints(self, operations: List[IROperation], context: RenderContext) -> None:
    # 1. Group operations by OpenAPI tag
    operations_by_tag = self.group_by_tag(operations)
    
    # 2. Generate endpoint class for each tag
    for tag, tag_operations in operations_by_tag.items():
        class_name = f"{tag.capitalize()}Endpoints"
        file_path = self.output_path / "endpoints" / f"{tag}.py"
        
        # Generate endpoint class code
        endpoint_code = self.endpoint_visitor.visit_tag_operations(tag_operations, context)
        
        # Write file
        self.file_manager.write_file(file_path, endpoint_code)
```

### client_emitter.py
**Purpose**: Create main client.py with tag-grouped properties
```python
def emit_client(self, spec: IRSpec, context: RenderContext) -> None:
    # 1. Generate main client class
    # 2. Create properties for each tag endpoint
    # 3. Generate context manager methods
    # 4. Handle authentication setup
    
    client_code = self.client_visitor.visit_spec(spec, context)
    self.file_manager.write_file(self.output_path / "client.py", client_code)
```

### core_emitter.py
**Purpose**: Copy runtime dependencies to core/ directory
```python
def emit_core(self, output_package: str, core_package: str) -> None:
    # 1. Copy auth/ directory
    # 2. Copy exceptions.py, http_transport.py, etc.
    # 3. Update import paths for target package
    # 4. Handle shared core vs embedded core
    
    if self.use_shared_core:
        # Create symlinks or references to shared core
        pass
    else:
        # Copy all core files to client package
        self.copy_core_files()
```

## File Management Patterns

### 1. Import Resolution
```python
# Always resolve imports after code generation
def write_file_with_imports(self, file_path: Path, code: str, context: RenderContext) -> None:
    # 1. Collect imports from context
    imports = context.get_imports()
    
    # 2. Sort and deduplicate imports
    sorted_imports = self.sort_imports(imports)
    
    # 3. Combine imports with code
    final_code = self.combine_imports_and_code(sorted_imports, code)
    
    # 4. Write file
    self.file_manager.write_file(file_path, final_code)
```

### 2. Package Initialization
```python
# Always create __init__.py files
def create_package_init(self, package_path: Path, exports: List[str]) -> None:
    init_content = []
    
    # Add imports for all public exports
    for export in exports:
        init_content.append(f"from .{export} import {export}")
    
    # Add __all__ for explicit exports
    init_content.append(f"__all__ = {exports}")
    
    self.file_manager.write_file(package_path / "__init__.py", "\n".join(init_content))
```

### 3. Relative Import Handling
```python
# Convert absolute imports to relative for generated packages
def convert_to_relative_imports(self, code: str, current_package: str) -> str:
    # Replace absolute imports with relative imports
    # Example: "from my_client.models.user import User" → "from ..models.user import User"
    
    import_pattern = re.compile(rf"from {re.escape(current_package)}\.(.+?) import")
    
    def replace_import(match):
        import_path = match.group(1)
        depth = len(import_path.split("."))
        relative_prefix = "." * depth
        return f"from {relative_prefix}{import_path} import"
    
    return import_pattern.sub(replace_import, code)
```

## Dependencies on Other Systems

### From visit/
- Consumes generated code strings
- Coordinates with visitors for code generation

### From context/
- `FileManager` for file operations
- `RenderContext` for import management
- Path resolution utilities

### From core/
- Runtime components copied to generated clients
- Template files for package structure

## Testing Requirements

### File Creation Tests
```python
def test_models_emitter__simple_schema__creates_correct_file():
    # Arrange
    schema = IRSchema(name="User", type="object", properties={"name": {"type": "string"}})
    emitter = ModelsEmitter(output_path="/tmp/test")
    
    # Act
    emitter.emit_models({"User": schema}, context)
    
    # Assert
    assert Path("/tmp/test/models/user.py").exists()
    content = Path("/tmp/test/models/user.py").read_text()
    assert "@dataclass" in content
    assert "name: str" in content
```

### Import Resolution Tests
```python
def test_emitter__complex_types__resolves_imports_correctly():
    # Test that imports are correctly collected and written
    # Verify no duplicate imports
    # Verify correct import sorting
```

## Extension Points

### Adding New Emitters
```python
# Create new emitter for new output aspects
class CustomEmitter:
    def __init__(self, output_path: Path, file_manager: FileManager):
        self.output_path = output_path
        self.file_manager = file_manager
    
    def emit_custom(self, data: Any, context: RenderContext) -> None:
        # Custom file creation logic
        pass
```

### Custom Package Structures
```python
# Modify emitters to create different package layouts
class AlternativeModelsEmitter(ModelsEmitter):
    def get_file_path(self, schema_name: str) -> Path:
        # Custom file organization logic
        # Example: Group models by domain
        domain = self.get_domain(schema_name)
        return self.output_path / "models" / domain / f"{schema_name.lower()}.py"
```

## Critical Implementation Details

### File Path Resolution
```python
# Always use pathlib.Path for cross-platform compatibility
def get_output_path(self, package_name: str, module_name: str) -> Path:
    # Convert package.module to file path
    parts = package_name.split(".")
    path = Path(self.project_root)
    for part in parts:
        path = path / part
    return path / f"{module_name}.py"
```

### Error Handling
```python
def emit_safely(self, generator_func: Callable, context: RenderContext) -> None:
    try:
        generator_func(context)
    except Exception as e:
        # Add context to file emission errors
        raise FileEmissionError(f"Failed to emit {self.__class__.__name__}: {e}")
```

### Atomic File Operations
```python
def write_file_atomically(self, file_path: Path, content: str) -> None:
    # Write to temporary file first, then move
    temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")
    
    try:
        temp_path.write_text(content)
        temp_path.replace(file_path)  # Atomic move
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        raise
```

### Diff Checking
```python
def should_write_file(self, file_path: Path, new_content: str) -> bool:
    # Only write if content changed
    if not file_path.exists():
        return True
    
    existing_content = file_path.read_text()
    return existing_content != new_content
```