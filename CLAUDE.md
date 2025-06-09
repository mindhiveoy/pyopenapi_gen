# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# PyOpenAPI Generator

PyOpenAPI Generator creates modern, async-first, and strongly-typed Python clients from OpenAPI specifications. Built for enterprise-grade developer experience with advanced cycle detection, unified type resolution, and production-ready generated code. Generated clients are fully independent and require no runtime dependency on this generator.

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
# Fast Development Workflow
pytest -xvs               # Run with verbose output, stop on first failure
mypy src/                 # Type checking
ruff check src/           # Linting
black src/                # Code formatting

# Testing Options
pytest                    # Run all tests
pytest -n auto            # Run tests in parallel (faster)
pytest --cov=src --cov-report=html  # Generate coverage report

# Quality Gates (CI checks)
pytest --cov=src --cov-report=term-missing  # Coverage with missing lines
ruff check --fix src/     # Auto-fix linting issues
mypy src/ --strict        # Strict type checking

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

# Coverage with HTML report (opens in browser)
make coverage-html

# Coverage with missing lines shown
pytest --cov=src --cov-report=term-missing
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

# With shared core package (multi-client scenarios)
pyopenapi-gen gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client --core-package pyapis.core

# Development options
--force           # Overwrite without diff check (faster iteration)
--no-postprocess  # Skip type checking (faster generation)
--verbose         # Detailed output for debugging

# Advanced options
--max-depth 200   # Custom recursion limit (default: 150)
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

### Unified Type Resolution (`types/`)
**⭐ NEW ARCHITECTURE**: Enterprise-grade, centralized type resolution system:
- **Contracts** (`contracts/`): Protocols and interfaces for clean architecture
- **Resolvers** (`resolvers/`): Core resolution logic for schemas, responses, and references  
- **Services** (`services/`): High-level orchestration with `UnifiedTypeService`
- **Benefits**: Dependency injection, comprehensive testing, single source of truth
- **Migration**: Replaces scattered `TypeHelper` usage across codebase

### Supporting Systems
- **Context** (`context/`): Manages rendering state and imports
- **Writers** (`core/writers/`): Code formatting and output utilities
- **Helpers** (`helpers/`): Legacy type resolution (delegates to unified system)

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
- **Documentation**: Include "Scenario:" and "Expected Outcome:" sections in docstrings
- **Structure**: Arrange/Act/Assert with clear separation and comments
- **Coverage**: ≥90% branch coverage enforced
- **Isolation**: Mock all external dependencies with unittest.mock
- **Assertions**: Use plain `assert` statements (pytest style)
- **Exceptions**: Use `pytest.raises` context manager for expected exceptions
- **Parameterization**: Use `pytest.mark.parametrize` for multiple test variations

### Client Independence
Generated clients must be completely self-contained:
- No runtime dependency on `pyopenapi_gen`
- All required code copied to client's `core/` module
- Relative imports only within generated package

## Generated Client Features

### Modern Python Architecture
- **Async-First**: All operations use `httpx.AsyncClient` for modern async/await patterns
- **Type Safety**: Complete type hints and dataclass models with mypy compatibility
- **Zero Dependencies**: Generated clients require no runtime dependency on this generator

### Developer Experience
- **Tag-Based Organization**: Operations grouped by OpenAPI tags for intuitive navigation
- **Rich Documentation**: Extracted from OpenAPI descriptions with proper formatting
- **IDE Support**: Full autocomplete and type checking in modern IDEs

### Advanced Features
- **Pluggable Auth**: Bearer, API key, OAuth2, and custom authentication strategies
- **Smart Pagination**: Auto-detected cursor/page/offset patterns with async iteration
- **Error Handling**: Structured exception hierarchy with meaningful error messages
- **Response Unwrapping**: Automatic extraction of `data` fields from wrapper responses
- **Streaming Support**: Built-in support for streaming responses and downloads

### Production Ready
- **Client Independence**: Completely self-contained with copied runtime dependencies
- **Shared Core Support**: Multiple clients can share common runtime components
- **Post-Processing**: Generated code is automatically formatted and type-checked

## Environment Variables

- `PYOPENAPI_MAX_DEPTH`: Schema parsing recursion limit (default: 150)
- `PYOPENAPI_MAX_CYCLES`: Cycle detection limit (default: 0, unlimited)

## Additional Documentation

See `docs/` directory for detailed guides:
- `architecture.md` - System design and patterns
- `unified_type_resolution.md` - **⭐ NEW**: Unified type resolution system
- `ir_models.md` - Intermediate representation details  
- `model_visitor.md` - Model code generation
- `endpoint_visitor.md` - Endpoint code generation

## Quick Start Examples

### Generate Your First Client
```bash
# Activate environment
source .venv/bin/activate

# Generate client from OpenAPI spec
pyopenapi-gen gen examples/petstore.yaml --project-root . --output-package pyapis.petstore

# Generated structure:
# pyapis/
# ├── __init__.py
# └── petstore/
#     ├── __init__.py
#     ├── client.py          # Main API client
#     ├── models/            # Data models
#     ├── endpoints/         # API operations
#     └── core/              # Runtime dependencies
```

### Using Generated Clients
```python
import asyncio
from pyapis.petstore import PetstoreClient

async def main():
    async with PetstoreClient(base_url="https://api.example.com") as client:
        # Type-safe API calls with full IDE support
        pets = await client.pets.list_pets(limit=10)
        
        # Automatic pagination
        async for pet in client.pets.list_pets_paginated():
            print(f"Pet: {pet.name}")
            
        # Rich error handling
        try:
            pet = await client.pets.get_pet(pet_id=123)
        except client.exceptions.PetNotFoundError as e:
            print(f"Pet not found: {e.detail}")

asyncio.run(main())
```

### Multi-Client Setup with Shared Core
```bash
# Generate first client (creates shared core)
pyopenapi-gen gen api_v1.yaml --project-root . --output-package pyapis.v1 --core-package pyapis.core

# Generate second client (reuses core)
pyopenapi-gen gen api_v2.yaml --project-root . --output-package pyapis.v2 --core-package pyapis.core

# Shared structure:
# pyapis/
# ├── core/              # Shared runtime (httpx, auth, etc.)
# ├── v1/                # First client
# └── v2/                # Second client
```

## Troubleshooting

### Common Issues

**Import Errors After Generation**
```bash
# Ensure you're in the right directory and imports are absolute
cd your_project_root
python -c "from pyapis.my_client import MyClient"
```

**Type Checking Failures**
```bash
# Run quality checks on generated code
mypy pyapis/
ruff check pyapis/

# Regenerate with post-processing if needed
pyopenapi-gen gen spec.yaml --project-root . --output-package pyapis.client
```

**Performance Issues with Large Specs**
```bash
# Skip type checking during development
pyopenapi-gen gen large_spec.yaml --no-postprocess --project-root . --output-package pyapis.large

# Increase recursion limits for deeply nested schemas
PYOPENAPI_MAX_DEPTH=300 pyopenapi-gen gen complex_spec.yaml --project-root . --output-package pyapis.complex
```

**Circular Reference Errors**
```bash
# Check cycle detection in action
pyopenapi-gen gen spec_with_cycles.yaml --verbose --project-root . --output-package pyapis.client

# Generated code will include forward references and placeholders for cycles
```

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.