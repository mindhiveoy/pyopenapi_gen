# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# PyOpenAPI Generator

PyOpenAPI Generator is a tool for generating Python client code from OpenAPI specifications. It creates modern, async-first, and strongly-typed Python clients.

## Development Environment

### Setup and Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pyopenapi-gen.git
cd pyopenapi-gen

# Install dependencies with Poetry
poetry install

# Alternatively, install in development mode with pip
pip install -e '.[dev]'
```

### Common Commands

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/core/test_loader.py
pytest tests/visit/test_model_visitor.py

# Run tests with parallel execution (faster for large test suites)
pytest -xvs

# Run tests with xdist (distributed testing)
pytest -n auto

# Run a specific test function
pytest tests/core/test_pagination.py::test_paginate_by_next__iterates_through_multiple_pages

# Run tests with coverage
pytest --cov=src --cov-report=html
# Open coverage report
open htmlcov/index.html

# Check types
mypy src/

# Lint code
ruff check src/

# Format code
black src/

# Build the package
python -m build
```

### CLI Usage

```bash
# Generate client from OpenAPI spec
pyopenapi-gen gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client

# With shared core package
pyopenapi-gen gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client --core-package pyapis.core

# Skip post-processing (faster but without type checking)
pyopenapi-gen gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client --no-postprocess

# Force overwrite existing files without diff check
pyopenapi-gen gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client --force
```

## Debugging

The repository includes some debug scripts:

```bash
# Debug generation process
python debug_generate.py

# Debug project-specific issues
python debug_project.py
```

## Core Architecture Overview

PyOpenAPI Generator follows a multi-stage pipeline architecture:

1. **Loading** - Parse OpenAPI spec into intermediate representation (IR)
2. **Visiting** - Transform IR into code using visitor pattern
3. **Emitting** - Output generated code to files

The codebase is organized around these stages with clear separation of concerns.

## Generation Flow

The process of generating a client follows these sequential steps:

1. **Load Spec**: `ClientGenerator` loads the OpenAPI spec file (YAML/JSON) into a Python dictionary.
2. **Parse to IR**: `load_ir_from_spec` processes the dictionary, resolves references (where possible), validates structure, and builds the `IRSpec` object containing all IR nodes.
3. **Emit Code**: `ClientGenerator` invokes the various `Emitters` (`CoreEmitter`, `ModelsEmitter`, `EndpointsEmitter`, `ClientEmitter`, etc.).
4. **Visit & Render**: Each `Emitter` uses its corresponding `Visitor` to traverse the relevant parts of the `IRSpec`.
5. **Generate Code**: `Visitors` use `Helpers` (like `CodeWriter`) to render Python code strings for classes, methods, etc.
6. **Write Files**: `Emitters` write the generated code strings to the appropriate `.py` files in the specified output directory structure.
7. **Post-process**: Optional steps like running code formatters (e.g., Ruff, Black) or type checkers (`mypy`) on the generated code.

## Key Components

### 1. Loader (IR Generation)

- `core/loader.py` - Transforms OpenAPI spec into internal IR dataclasses
- Creates `IRSpec`, `IRSchema`, `IROperation`, etc. from raw OpenAPI JSON/YAML
- Handles references, types, and schema relationships
- Recently being refactored to use separate modules in `core/parsing/`:
  - `ref_resolver.py` - Handles resolution of `$ref` references
  - `all_of_merger.py` - Processes `allOf` schema combinations
  - `inline_enum_extractor.py` - Extracts inline enums into standalone schemas
  - `inline_object_promoter.py` - Promotes inline objects to top-level schemas
  - `schema_parser.py` - Core schema parsing logic
  - `type_parser.py` - Handles type resolution and formatting

### 2. Visitors (Code Generation)

- `visit/model_visitor.py` - Converts IR schemas to Python dataclasses/enums
- `visit/endpoint_visitor.py` - Converts IR operations to Python async methods
- `visit/client_visitor.py` - Generates the main API client class
- `visit/endpoint_method_generator.py` - Helper for generating endpoint methods
- `visit/exception_visitor.py` - Generates exception classes/aliases
- `visit/docs_visitor.py` - Generates Markdown documentation

### 3. Emitters (File Generation)

- `emitters/models_emitter.py` - Emits model files under models/
- `emitters/endpoints_emitter.py` - Emits endpoint client files under endpoints/
- `emitters/core_emitter.py` - Copies runtime files into core/
- `emitters/client_emitter.py` - Emits the main client.py file
- `emitters/exceptions_emitter.py` - Emits exception classes
- `emitters/docs_emitter.py` - Emits documentation files

### 4. Context and Utilities

- `context/render_context.py` - Manages the rendering context, imports
- `context/import_collector.py` - Handles import management
- `context/file_manager.py` - Manages file writing
- `core/writers/code_writer.py` - Utility for writing Python code with proper indentation
- `core/writers/line_writer.py` - Low-level utility for writing lines with indentation
- `core/writers/documentation_writer.py` - Utility for writing documentation
- `helpers/` - Utilities for type helpers, URL handling, etc.

### 5. Generator (Orchestration)

- `generator/client_generator.py` - Main orchestration class that ties everything together
- `cli.py` - Command-line interface for the generator

## Design Patterns

1. **Visitor Pattern** - Core pattern for code generation. IR objects are visited to produce code.
2. **Context Object** - `RenderContext` maintains state during code generation (imports, files, etc.).
3. **Intermediate Representation (IR)** - Clean separation between schema parsing and code generation.
4. **Emitter Pattern** - Responsible for determining what files to emit and orchestrating visitors.

## Recent Architectural Changes

The project has completed a major refactoring of the schema parsing and cycle detection systems:

1. **Unified Cycle Detection**: Implemented a comprehensive, conflict-free cycle detection system in `core/parsing/unified_cycle_detection.py` that handles structural cycles, processing cycles, and depth limits consistently.

2. **Modular Schema Parsing**: The schema parsing logic has been broken down into focused components with clear separation of concerns:
   - `schema_parser.py` - Core schema parsing logic
   - `ref_resolution/` - Reference resolution helpers
   - `keywords/` - Keyword-specific parsers (allOf, oneOf, etc.)
   - `transformers/` - Schema transformation utilities

3. **Enhanced ParsingContext**: The `ParsingContext` now integrates with the unified cycle detection system while maintaining backward compatibility.

The codebase now follows a more modular, testable architecture with comprehensive cycle detection and robust error handling.

## Project Standards

1. **Code Style**:
   - Black for formatting with 120 character line length
   - Ruff for linting
   - 100% mypy type coverage with strict mode enabled
   - Python 3.10-3.12 compatibility

2. **Testing**:
   - All code changes should have tests
   - Maintain high test coverage, especially for core components
   - Use pytest fixtures and mocks appropriately
   - Tests are organized to mirror the package structure in the `tests/` directory

3. **Version Control**:
   - Meaningful commit messages
   - Feature branches with descriptive names
   - Pull requests with clear descriptions

## Extension Points

The codebase is designed for extensibility in several areas:

1. **Custom Visitors** - Extend base visitors to customize code generation
2. **Post-Processors** - Add custom post-processing steps
3. **Core Functionality** - Extend/replace core runtime files
4. **Authentication Plugins** - Implement the `BaseAuth` protocol for custom authentication methods
5. **Pagination Plugins** - Create custom pagination strategies for different API patterns

## Generated Client Features

The generated clients include:

1. **Async-Only API**: All HTTP calls are async, using `httpx.AsyncClient` by default
2. **Per-Tag Endpoint Grouping**: Each OpenAPI tag becomes a Python class
3. **Typed Models**: Every schema becomes a Python dataclass with type hints
4. **Rich Docstrings**: Endpoint methods and model fields include docstrings
5. **Pluggable Authentication**: Built-in Bearer and custom header auth plugins
6. **Pagination Helpers**: Async iterators for cursor/page/offset-based pagination
7. **Error Handling**: Uniform exception hierarchy with specific aliases
8. **Response Unwrapping**: Automatic unwrapping of common response patterns

## Documentation

Additional documentation files are available in the `docs/` directory:
- `architecture.md` - Detailed architecture overview with diagrams
- `ir_models.md` - Details of the Intermediate Representation
- `model_visitor.md` - How model code is generated
- `endpoint_visitor.md` - How endpoint code is generated
- `render_context.md` - How the rendering context works