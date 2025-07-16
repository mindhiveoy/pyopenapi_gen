# context/ - Rendering Context Management

## Why This Folder?
Manage stateful information during code generation: imports, templates, file paths, and rendering state. Provides clean interface between visitors and emitters.

## Key Dependencies
- **Input**: Path configuration, package names, template data
- **Output**: Import statements, resolved file paths, template rendering
- **Used by**: All visitors and emitters for consistent code generation

## Essential Architecture

### 1. Context Lifecycle
```python
# 1. Create context for generation session
context = RenderContext(project_root="/path/to/project", output_package="my_client")

# 2. Visitors use context for type resolution and imports
visitor.visit_schema(schema, context)  # Registers imports

# 3. Emitters use context for file organization
emitter.emit_models(schemas, context)  # Consumes imports
```

### 2. State Management
```python
# render_context.py
class RenderContext:
    def __init__(self, project_root: Path, output_package: str):
        self.import_collector = ImportCollector()
        self.file_manager = FileManager(project_root)
        self.template_vars = {}
        self.output_package = output_package
        self.forward_refs = set()
```

## Critical Components

### render_context.py
**Purpose**: Main context object passed through generation pipeline
```python
class RenderContext:
    def add_import(self, import_statement: str) -> None:
        """Register import for current file being generated"""
        self.import_collector.add_import(import_statement)
    
    def get_imports(self) -> List[str]:
        """Get sorted, deduplicated imports for current file"""
        return self.import_collector.get_sorted_imports()
    
    def clear_imports(self) -> None:
        """Clear imports for next file generation"""
        self.import_collector.clear()
    
    def resolve_relative_import(self, from_package: str, to_package: str) -> str:
        """Convert absolute import to relative import"""
        return self.import_collector.make_relative_import(from_package, to_package)
```

### import_collector.py
**Purpose**: Collect and manage import statements during code generation
```python
class ImportCollector:
    def __init__(self):
        self.imports: Set[str] = set()
        self.from_imports: Dict[str, Set[str]] = defaultdict(set)
    
    def add_import(self, import_statement: str) -> None:
        """Add import statement, handling both 'import' and 'from' forms"""
        if import_statement.startswith("from "):
            self.parse_from_import(import_statement)
        else:
            self.imports.add(import_statement)
    
    def get_sorted_imports(self) -> List[str]:
        """Return sorted imports: stdlib, third-party, local"""
        return self.sort_imports_by_category()
```

### file_manager.py
**Purpose**: Handle file operations and path resolution
```python
class FileManager:
    def __init__(self, project_root: Path):
        self.project_root = project_root
    
    def write_file(self, file_path: Path, content: str) -> None:
        """Write file with proper directory creation"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
    
    def resolve_package_path(self, package_name: str) -> Path:
        """Convert package.name to file system path"""
        parts = package_name.split(".")
        return self.project_root / Path(*parts)
```

## Import Management Patterns

### 1. Import Categories
```python
# import_collector.py
def categorize_import(self, import_statement: str) -> ImportCategory:
    """Categorize imports for proper sorting"""
    if self.is_stdlib_import(import_statement):
        return ImportCategory.STDLIB
    elif self.is_third_party_import(import_statement):
        return ImportCategory.THIRD_PARTY
    else:
        return ImportCategory.LOCAL
```

### 2. From Import Consolidation
```python
# Convert multiple from imports to single statement
# "from typing import List"
# "from typing import Dict"
# →
# "from typing import Dict, List"

def consolidate_from_imports(self) -> List[str]:
    consolidated = []
    for module, imports in self.from_imports.items():
        sorted_imports = sorted(imports)
        consolidated.append(f"from {module} import {', '.join(sorted_imports)}")
    return consolidated
```

### 3. Relative Import Conversion
```python
def make_relative_import(self, from_package: str, to_package: str) -> str:
    """Convert absolute import to relative import"""
    # from my_client.models.user import User
    # →
    # from ..models.user import User (when called from my_client.endpoints)
    
    from_parts = from_package.split(".")
    to_parts = to_package.split(".")
    
    # Find common prefix
    common_len = self.find_common_prefix_length(from_parts, to_parts)
    
    # Calculate relative depth
    relative_depth = len(from_parts) - common_len
    prefix = "." * relative_depth
    
    # Build relative import
    remaining_path = ".".join(to_parts[common_len:])
    return f"from {prefix}{remaining_path} import"
```

## Template Management

### 1. Template Variables
```python
# Store template variables for consistent rendering
context.template_vars.update({
    "client_name": "MyAPIClient",
    "base_url": "https://api.example.com",
    "version": "1.0.0",
    "auth_type": "bearer"
})
```

### 2. Template Rendering
```python
def render_template(self, template: str, **kwargs) -> str:
    """Render template with context variables"""
    all_vars = {**self.template_vars, **kwargs}
    return template.format(**all_vars)
```

## Dependencies on Other Systems

### From types/
- Implements `TypeContext` protocol for type resolution
- Provides import registration for complex types

### From visit/
- Receives import registration during code generation
- Provides path resolution for relative imports

### From emitters/
- Provides file writing capabilities
- Supplies consolidated imports for file headers

## Testing Requirements

### Import Management Tests
```python
def test_import_collector__multiple_from_imports__consolidates_correctly():
    # Arrange
    collector = ImportCollector()
    collector.add_import("from typing import List")
    collector.add_import("from typing import Dict")
    
    # Act
    imports = collector.get_sorted_imports()
    
    # Assert
    assert "from typing import Dict, List" in imports
```

### Path Resolution Tests
```python
def test_file_manager__package_path__resolves_correctly():
    # Test package name to file path conversion
    manager = FileManager(Path("/project"))
    path = manager.resolve_package_path("my_client.models")
    
    assert path == Path("/project/my_client/models")
```

## Extension Points

### Custom Import Sorting
```python
class CustomImportCollector(ImportCollector):
    def sort_imports_by_category(self) -> List[str]:
        # Custom import sorting logic
        # Example: Group all async imports together
        pass
```

### Template System Integration
```python
def add_template_engine(self, engine: TemplateEngine) -> None:
    """Add custom template engine (Jinja2, etc.)"""
    self.template_engine = engine
    
def render_template(self, template_name: str, **kwargs) -> str:
    """Render template using custom engine"""
    return self.template_engine.render(template_name, **kwargs)
```

## Critical Implementation Details

### Thread Safety
```python
# Context is NOT thread-safe by design
# Each generation session gets its own context instance
def create_context() -> RenderContext:
    return RenderContext(project_root, output_package)
```

### Memory Management
```python
# Clear context between files to prevent memory leaks
def emit_file(self, file_path: Path, generator_func: Callable) -> None:
    self.context.clear_imports()
    
    # Generate code
    code = generator_func(self.context)
    
    # Write file with imports
    imports = self.context.get_imports()
    final_code = self.combine_imports_and_code(imports, code)
    
    self.file_manager.write_file(file_path, final_code)
```

### Error Context
```python
# Always provide context in error messages
def add_import_with_context(self, import_statement: str, file_context: str) -> None:
    try:
        self.import_collector.add_import(import_statement)
    except Exception as e:
        raise ImportError(f"Failed to add import '{import_statement}' in {file_context}: {e}")
```

## Common Pitfalls

1. **Import Leakage**: Not clearing imports between files
2. **Path Confusion**: Using absolute paths instead of relative
3. **State Mutation**: Modifying context from multiple threads
4. **Memory Leaks**: Not cleaning up context after generation

## Best Practices

1. **One Context Per Session**: Create new context for each generation
2. **Clear Between Files**: Always clear imports between file generations
3. **Use Relative Imports**: Convert absolute imports to relative
4. **Error Context**: Include file/operation context in errors