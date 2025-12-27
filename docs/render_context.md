# Render Context (`context/render_context.py`)

## Why This Component?

Code generation requires tracking state across multiple files and visitors. Each generated file needs its own set of imports, and these imports must be correctly calculated based on the relative positions of modules within the package structure. RenderContext provides this central coordination point.

## What It Does

RenderContext is the central state container during code generation, managing:

- **Import tracking**: Collects and organises imports for each generated file
- **File management**: Coordinates writing files to disk
- **Module tracking**: Tracks which modules have been generated
- **Path calculation**: Computes correct import paths (relative or absolute)
- **Schema access**: Provides access to parsed schemas for cross-referencing

## How It Works

### Core Attributes

```python
class RenderContext:
    file_manager: FileManager          # Utility for writing files
    import_collector: ImportCollector  # Manages imports for current file
    generated_modules: Set[str]        # Modules generated in this run
    current_file: str | None           # Currently rendering file path
    core_package_name: str             # Python import path of core package
    package_root_for_generated_code: str | None  # Root of emitting package
    overall_project_root: str | None   # Top-level project path
    parsed_schemas: dict[str, IRSchema] | None   # All parsed schemas
    use_absolute_imports: bool         # Use absolute vs relative imports
    output_package_name: str | None    # Full output package name
    conditional_imports: dict[str, dict[str, Set[str]]]  # TYPE_CHECKING imports
```

### Key Methods

#### Import Management

```python
# Add a standard import
context.add_import("typing", "Optional")
context.add_import("datetime", "datetime")

# Add a conditional import (under TYPE_CHECKING)
context.add_conditional_import("TYPE_CHECKING", "mymodule", "MyClass")

# Get formatted import statements for current file
import_lines = context.get_imports()
```

#### File Context

```python
# Set the current file being rendered (resets import collector)
context.set_current_file("/path/to/output/models/user.py")

# Register a generated module
context.register_generated_module("models.user")
```

#### Path Calculation

```python
# Calculate import path for a schema
import_path = context.calculate_import_path("User")

# Get module path from file path
module = context.file_to_module("/path/to/models/user.py")
```

### Workflow Integration

RenderContext flows through the generation pipeline:

```
ClientGenerator
    └── creates RenderContext
            │
            ├── Visitors use context to:
            │   ├── Add imports as they generate code
            │   ├── Look up parsed schemas
            │   └── Track cross-references
            │
            └── Emitters use context to:
                ├── Set current file before writing
                ├── Collect imports for file header
                └── Write files via FileManager
```

### Import Collector

The `ImportCollector` (used internally) handles:

- Deduplication of imports
- Grouping by module
- Formatting import statements
- Handling `from X import Y` vs `import X`

### File Manager

The `FileManager` (used internally) handles:

- Creating directories as needed
- Writing file contents
- Handling encoding
- Optional diff checking before overwrite

## Usage Example

```python
from pyopenapi_gen.context import RenderContext, FileManager

# Create context for generation
context = RenderContext(
    file_manager=FileManager(project_root),
    core_package_name="myapi.core",
    output_package_name="myapi.client",
    use_absolute_imports=True,
)

# Set context for generating a specific file
context.set_current_file(str(project_root / "myapi" / "client" / "models" / "user.py"))

# Add imports as code is generated
context.add_import("dataclasses", "dataclass")
context.add_import("typing", "Optional")

# Get formatted imports for file header
imports = context.get_imports()
```

## Related Components

- **ImportCollector**: Manages import deduplication and formatting
- **FileManager**: Handles file I/O operations
- **Visitors**: Use context to track imports during code generation
- **Emitters**: Use context to write files with proper imports
