# PyOpenAPI Generator Architecture

This document provides an overview of the PyOpenAPI Generator's core architecture, design patterns, and testing approach to help Claude understand and interact with the codebase.

## Core Architecture Overview

PyOpenAPI Generator is a tool for generating Python client code from OpenAPI specifications. It follows a multi-stage pipeline architecture:

1. **Loading** - Parse OpenAPI spec into intermediate representation (IR)
2. **Visiting** - Transform IR into code using visitor pattern
3. **Emitting** - Output generated code to files

The codebase is organized around these stages with clear separation of concerns.

## Key Components

### 1. Loader (IR Generation)

- `core/loader.py` - Transforms OpenAPI spec into internal IR dataclasses
- Creates `IRSpec`, `IRSchema`, `IROperation`, etc. from raw OpenAPI JSON/YAML
- Handles references, types, and schema relationships

### 2. Visitors (Code Generation)

- `visit/model_visitor.py` - Converts IR schemas to Python dataclasses/enums
- `visit/endpoint_visitor.py` - Converts IR operations to Python async methods
- `visit/client_visitor.py` - Generates the main API client class

### 3. Emitters (File Generation)

- `emitters/models_emitter.py` - Emits model files under models/
- `emitters/endpoints_emitter.py` - Emits endpoint client files under endpoints/
- `emitters/core_emitter.py` - Copies runtime files into core/
- `emitters/client_emitter.py` - Emits the main client.py file

### 4. Context and Utilities

- `context/render_context.py` - Manages the rendering context, imports
- `context/import_collector.py` - Handles import management
- `context/file_manager.py` - Manages file writing
- `core/writers/code_writer.py` - Utility for writing Python code with proper indentation
- `helpers/*` - Utilities for type helpers, URL handling, etc.

### 5. Generator (Orchestration)

- `generator/client_generator.py` - Main orchestration class that ties everything together
- `cli.py` - Command-line interface for the generator

## Design Patterns

1. **Visitor Pattern** - Core pattern for code generation. IR objects are visited to produce code.
2. **Context Object** - `RenderContext` maintains state during code generation (imports, files, etc.).
3. **Intermediate Representation (IR)** - Clean separation between schema parsing and code generation.
4. **Emitter Pattern** - Responsible for determining what files to emit and orchestrating visitors.

## Code Generation Flow

1. Parse OpenAPI spec → IR using `load_ir_from_spec`
2. Create emitters for models, endpoints, core, client
3. Each emitter:
   - Creates appropriate visitors
   - Visits IR objects using the visitors
   - Writes the resulting code to files
4. Apply post-processing (formatting, type checking)

## Testing Approach

Tests are organized under the `tests/` directory and follow these patterns:

1. **Unit Tests** - Test individual components
   - `tests/core/test_loader.py` - Test IR loading
   - `tests/core/test_http_transport.py` - Test HTTP client
   - `tests/core/writers/test_code_writer.py` - Test code writing utilities

2. **Emitter Tests** - Test code generation
   - `tests/emitters/test_models_emitter.py`
   - `tests/emitters/test_endpoints_emitter.py`

3. **Integration Tests** - End-to-end tests
   - `tests/integrations/test_end_to_end_petstore.py`

4. **Test Utilities**
   - Temporary directories for file output
   - Sample schemas for testing
   - Mock HTTP responses

## Running Tests

Tests use pytest with these common patterns:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/core/test_loader.py

# Run tests with parallel execution
pytest -xvs
```

## Key CLI Commands

```bash
# Generate client from OpenAPI spec
pyopenapi-gen gen spec.yaml --project-root /path/to/project --output-package my_package.client

# Generate docs from OpenAPI spec
pyopenapi-gen docs spec.yaml --output /path/to/docs
```

## Extension Points

The codebase is designed for extensibility in several areas:

1. **Custom Visitors** - Extend base visitors to customize code generation
2. **Post-Processors** - Add custom post-processing steps
3. **Core Functionality** - Extend/replace core runtime files