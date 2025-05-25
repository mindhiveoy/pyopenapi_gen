# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# PyOpenAPI Generator

PyOpenAPI Generator creates modern, async-first, and strongly-typed Python clients from OpenAPI specifications. Generated clients are fully independent and require no runtime dependency on this generator.

## Development Environment

**IMPORTANT: This project uses a virtual environment at `.venv/`. Always activate it before running any commands.**

### Setup

```bash
# Activate virtual environment (REQUIRED for all operations)
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
poetry install

# Alternative: pip install in development mode
pip install -e '.[dev]'
```

### Essential Commands

**Note: Always run `source .venv/bin/activate` first!**

```bash
# Testing
pytest                    # Run all tests
pytest -xvs               # Run with verbose output, stop on first failure
pytest -n auto            # Run tests in parallel
pytest --cov=src --cov-report=html  # Generate coverage report

# Code Quality
mypy src/                 # Type checking
ruff check src/           # Linting
black src/                # Code formatting

# Development
python -m build           # Build package
```

### Running Specific Tests

```bash
# Single test file
pytest tests/core/test_loader.py

# Single test function  
pytest tests/core/test_pagination.py::test_paginate_by_next__iterates_through_multiple_pages

# Tests by pattern
pytest -k "test_cycle_detection"
```

### Generator CLI

The CLI generates Python client code from OpenAPI specs. Understanding the project structure is crucial:

#### Project Structure Examples

**Standard Structure:**
```
myproject/
├── pyapis/
│   ├── __init__.py
│   └── my_api_client/    # Generated here
└── openapi.yaml
```
Command: `pyopenapi-gen gen openapi.yaml --project-root . --output-package pyapis.my_api_client`

**Source Layout:**
```
myproject/
├── src/
│   └── pyapis/
│       ├── __init__.py
│       └── business/     # Generated here
├── openapi.yaml
```
Command: `pyopenapi-gen gen openapi.yaml --project-root src --output-package pyapis.business`

**Multiple Clients with Shared Core:**
```
myproject/
├── pyapis/
│   ├── core/            # Shared runtime
│   ├── client_a/        # Generated client A
│   └── client_b/        # Generated client B
```
Commands:
```bash
# Generate first client (creates shared core)
pyopenapi-gen gen api_a.yaml --project-root . --output-package pyapis.client_a --core-package pyapis.core

# Generate second client (reuses core)
pyopenapi-gen gen api_b.yaml --project-root . --output-package pyapis.client_b --core-package pyapis.core
```

#### CLI Options

```bash
# Basic generation
pyopenapi-gen gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client

# With shared core package
pyopenapi-gen gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client --core-package pyapis.core

# Additional options
--force           # Overwrite without diff check
--no-postprocess  # Skip type checking (faster)
```

#### Common Project Root Issues

**Problem:** Imports like `from .models.user import User` instead of `from pyapis.business.models.user import User`

**Solution:** Check your project structure. If you have:
```
myproject/
├── pyapis/
│   └── src/
│       └── pyapis/
│           └── business/  # You want code here
```

Use: `--project-root myproject/pyapis/src --output-package pyapis.business`

**Not:** `--project-root myproject/pyapis --output-package pyapis.business` (creates wrong path)

**Verification:** The generated code should be at: `{project-root}/{output-package-as-path}`
- `project-root` + `pyapis.business` → `project-root/pyapis/business/`


## Architecture

The generator follows a three-stage pipeline:

1. **Loading** → Parse OpenAPI spec into Intermediate Representation (IR)
2. **Visiting** → Transform IR into Python code using visitor pattern  
3. **Emitting** → Write generated code to files

### Generation Pipeline

```
OpenAPI Spec → IR (schemas, operations) → Python Code → Files
```

1. **Load**: Parse YAML/JSON spec into `IRSpec` with unified cycle detection
2. **Visit**: Transform IR nodes into code strings using specialized visitors
3. **Emit**: Write code to structured output directory with proper imports
4. **Post-process**: Format and type-check generated code

## Key Components

### Loader (`core/loader/` & `core/parsing/`)
Transforms OpenAPI specs into Intermediate Representation (IR):
- **Schema Parser**: Core parsing with unified cycle detection
- **Reference Resolution**: Handles `$ref` links and circular dependencies  
- **Keyword Parsers**: Specialized handlers for `allOf`, `oneOf`, `anyOf`, `properties`
- **Transformers**: Extract inline enums, promote inline objects

### Visitors (`visit/`)
Transform IR into Python code:
- **Model Visitor**: Generates dataclasses and enums from schemas
- **Endpoint Visitor**: Creates async methods from operations
- **Client Visitor**: Builds main API client class
- **Exception Visitor**: Generates error hierarchies

### Emitters (`emitters/`)
Write code to files with proper structure:
- **Models Emitter**: Creates `models/` directory with schema classes
- **Endpoints Emitter**: Creates `endpoints/` with operation methods
- **Core Emitter**: Copies runtime dependencies to `core/`
- **Client Emitter**: Generates main client interface

### Supporting Systems
- **Context** (`context/`): Manages rendering state and imports
- **Writers** (`core/writers/`): Code formatting and output utilities
- **Helpers** (`helpers/`): Type resolution and utility functions

## Unified Cycle Detection

Critical system for handling complex schema relationships without infinite recursion:

### Detection Types
- **Structural Cycles**: Schema reference loops (A → B → A)
- **Self-References**: Direct self-references (A → A)
- **Depth Limits**: Recursion depth exceeded (configurable via `PYOPENAPI_MAX_DEPTH`)

### Resolution Strategies
- **Allowed Self-References**: Creates referential stubs when permitted
- **Circular Placeholders**: Creates marked placeholders for problematic cycles
- **Depth Placeholders**: Handles deep nesting gracefully

### Implementation
Located in `core/parsing/unified_cycle_detection.py` with schema state tracking through parsing lifecycle.

## Development Standards

### Code Quality
- **Formatting**: Black (120 char line length)
- **Linting**: Ruff for code quality and import sorting
- **Type Safety**: mypy strict mode with 100% coverage
- **Compatibility**: Python 3.10-3.12

### Testing Requirements
Follow cursor rules strictly:
- **Framework**: pytest only (no unittest.TestCase)
- **Naming**: `test_<unit_of_work>__<condition>__<expected_outcome>()`
- **Documentation**: Include "Scenario:" and "Expected Outcome:" sections
- **Structure**: Arrange/Act/Assert with clear separation
- **Coverage**: ≥90% branch coverage
- **Isolation**: Mock all external dependencies

### Client Independence
Generated clients must be completely self-contained:
- No runtime dependency on `pyopenapi_gen`
- All required code copied to client's `core/` module
- Relative imports only within generated package

## Generated Client Features

- **Async-First**: All operations use `httpx.AsyncClient`
- **Type Safety**: Full type hints and dataclass models
- **Tag-Based Organization**: Operations grouped by OpenAPI tags
- **Rich Documentation**: Extracted from OpenAPI descriptions
- **Pluggable Auth**: Bearer, API key, OAuth2, and custom auth strategies
- **Pagination Support**: Auto-detected cursor/page/offset patterns
- **Error Handling**: Structured exception hierarchy
- **Response Unwrapping**: Automatic extraction of common wrapper patterns

## Environment Variables

- `PYOPENAPI_MAX_DEPTH`: Schema parsing recursion limit (default: 150)
- `PYOPENAPI_MAX_CYCLES`: Cycle detection limit (default: 0, unlimited)

## Additional Documentation

See `docs/` directory for detailed guides:
- `architecture.md` - System design and patterns
- `ir_models.md` - Intermediate representation details  
- `model_visitor.md` - Model code generation
- `endpoint_visitor.md` - Endpoint code generation