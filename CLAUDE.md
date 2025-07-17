# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and the Claude GitHub App when working with code in this repository.

## Claude GitHub App Capabilities

The Claude GitHub App is configured with extensive permissions to independently operate on this repository:

### Automated PR Review & Fixes
- **Code Review**: Automatically triggered for dependabot PRs, version bumps, and documentation changes
- **Issue Fixing**: Can directly commit fixes to PR branches for:
  - Formatting issues (Black, Ruff)
  - Linting violations
  - Type checking errors
  - Security issues
  - Small bugs and improvements
- **Quality Assurance**: Runs `make quality` and `make test` to ensure all changes meet standards
- **Merge Decisions**: Approves and merges PRs when all criteria are met

### Repository Management
- **Issue Creation**: Creates detailed issues for complex problems that need human attention
- **Branch Management**: Can work on feature branches and create new branches as needed
- **Release Management**: Assists with version bumps and changelog updates
- **Documentation**: Updates documentation to reflect code changes

### Permissions
The Claude GitHub App has the following permissions:
- `contents: write` - Modify files and commit changes
- `pull-requests: write` - Review, approve, and merge PRs
- `issues: write` - Create and manage issues
- `actions: read` - Monitor CI/CD status
- `checks: read` - Review test results
- `statuses: read` - Check status checks

### Triggering Claude Reviews
1. **Automatic**: PRs from dependabot, devops-mindhive (docs/release), or with `[claude-review]` tag
2. **Manual**: Comment `@claude` on any PR, issue, or review to request assistance
3. **On PR Events**: New PRs automatically get Claude attention for quality review

# PyOpenAPI Generator

PyOpenAPI Generator creates modern, async-first, and strongly-typed Python clients from OpenAPI specifications. Built for enterprise-grade developer experience with advanced cycle detection, unified type resolution, and production-ready generated code. Generated clients are fully independent and require no runtime dependency on this generator.

## _process Folder Management

**IMPORTANT: This project uses `_process/` folder at project root for all AI agent temporal files:**
- Plans, reports, screenshots, test files, drafts, analysis
- Anything created during task completion that isn't part of the final project
- Distinguish between project documentation (belongs in project) vs. process documentation (belongs in `_process/`)
- Keep project directories clean of AI-generated temporary content

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
make quality-fix          # Auto-fix formatting and linting issues
make quality              # Run all quality checks (format, lint, typecheck, security)

# Individual Quality Commands
make format               # Auto-format code with Black
make format-check         # Check formatting without fixing
make lint                 # Check linting with Ruff
make lint-fix             # Auto-fix linting issues with Ruff
make typecheck            # Type checking with mypy
make security             # Security scanning with Bandit

# Testing Options
make test                 # Run all tests in parallel with 2 workers and coverage (85% required - matches CI)
make test-serial          # Run tests sequentially (fallback if parallel tests hang)
make test-no-cov          # Run tests without coverage checking
make test-fast            # Run tests, stop on first failure
make test-cov             # Run tests in parallel with coverage report (85% required)
pytest -n auto            # Run tests in parallel (faster, use with --timeout=300 if needed)

# Legacy Commands (still work)
pytest --cov=src --cov-report=html  # Generate coverage report
ruff check --fix src/     # Auto-fix linting issues
mypy src/ --strict        # Strict type checking

# Development
make build                # Build package
make clean                # Clean build artifacts
```

### Quality Workflow

**Before committing or pushing changes:**

```bash
# 1. Auto-fix what's possible
make quality-fix

# 2. Run all quality checks
make quality

# 3. If issues remain, fix manually and repeat
```

**For CI/CD compliance:**
```bash
# These commands match what runs in GitHub Actions
make format-check         # Must pass (no formatting issues)
make lint                 # Must pass (no linting errors)  
make typecheck            # Must pass (no type errors)
make security             # Must pass (no security issues)
make test                 # Must pass (all tests pass + 85% coverage)
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
make test-cov
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
Command: `pyopenapi-gen openapi.yaml --project-root . --output-package pyapis.my_api_client`

**Source Layout:**
```
myproject/
├── src/
│   └── pyapis/
│       ├── __init__.py
│       └── business/     # Generated here
├── openapi.yaml
```
Command: `pyopenapi-gen openapi.yaml --project-root src --output-package pyapis.business`

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
pyopenapi-gen api_a.yaml --project-root . --output-package pyapis.client_a --core-package pyapis.core

# Generate second client (reuses core)
pyopenapi-gen api_b.yaml --project-root . --output-package pyapis.client_b --core-package pyapis.core
```

#### CLI Options

```bash
# Basic generation
pyopenapi-gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client

# With shared core package (multi-client scenarios)
pyopenapi-gen input/openapi.yaml --project-root . --output-package pyapis.my_api_client --core-package pyapis.core

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

### Why This Architecture?
Modern OpenAPI specifications contain complex schemas with circular references, deep nesting, and intricate type relationships. Traditional code generators struggle with these complexities, often producing broken code or failing entirely. This architecture was designed to handle enterprise-grade OpenAPI specs reliably while generating production-ready, type-safe Python clients.

### What Is the Architecture?
The generator implements a sophisticated three-stage pipeline with unified type resolution and advanced cycle detection. Each stage has distinct responsibilities and clean interfaces, enabling robust processing of complex schemas while maintaining code quality.

```mermaid
graph TD
    A[OpenAPI Spec] --> B[Loading Stage]
    B --> C[Intermediate Representation]
    C --> D[Unified Type Resolution]
    D --> E[Visiting Stage]
    E --> F[Python Code AST]
    F --> G[Emitting Stage]
    G --> H[Generated Files]
    H --> I[Post-Processing]
    I --> J[Final Client Package]
    
    B --> K[Schema Parser]
    B --> L[Cycle Detection]
    B --> M[Reference Resolution]
    
    E --> N[Model Visitor]
    E --> O[Endpoint Visitor]
    E --> P[Client Visitor]
    
    G --> Q[Models Emitter]
    G --> R[Endpoints Emitter]
    G --> S[Core Emitter]
```

### How the Architecture Works

#### Stage 1: Loading (Parse & Normalize)
1. **Parse**: YAML/JSON spec into structured data
2. **Detect Cycles**: Identify circular references and deep nesting
3. **Resolve References**: Handle `$ref` links across the specification
4. **Create IR**: Build normalized `IRSpec` with all schemas and operations

#### Stage 2: Visiting (Transform & Generate)
1. **Type Resolution**: Convert IR schemas to Python types via `UnifiedTypeService`
2. **Code Generation**: Transform IR nodes into Python code strings
3. **Import Management**: Track and resolve all necessary imports
4. **Template Rendering**: Apply Jinja2 templates for consistent code structure

#### Stage 3: Emitting (Write & Organize)
1. **Structure Creation**: Build proper package directory structure
2. **File Writing**: Write generated code to appropriate modules
3. **Import Resolution**: Ensure all imports are correctly formatted
4. **Post-Processing**: Apply formatting (Black) and type checking (mypy)

## Key Components

### Why These Components?
Complex OpenAPI specifications require specialized handling at each stage. Breaking the system into focused components allows for clear separation of concerns, easier testing, and maintainable code. Each component has a specific responsibility and well-defined interfaces.

### What Are the Components?

```mermaid
graph TB
    subgraph "Loading & Parsing"
        A[Schema Parser] --> B[Reference Resolver]
        B --> C[Cycle Detector]
        C --> D[Keyword Parsers]
    end
    
    subgraph "Type Resolution"
        E[UnifiedTypeService] --> F[Schema Resolver]
        E --> G[Response Resolver]
        E --> H[Reference Resolver]
    end
    
    subgraph "Code Generation"
        I[Model Visitor] --> J[Endpoint Visitor]
        J --> K[Client Visitor]
        K --> L[Exception Visitor]
    end
    
    subgraph "File Output"
        M[Models Emitter] --> N[Endpoints Emitter]
        N --> O[Core Emitter]
        O --> P[Client Emitter]
    end
    
    D --> E
    E --> I
    L --> M
```

### How the Components Work

#### Unified Type Resolution (`types/`) ⭐ NEW ARCHITECTURE
**Why**: Previous type resolution was scattered across multiple files, making it hard to test and maintain. The unified system provides a single source of truth for all type conversions.

**What**: Enterprise-grade, centralized type resolution with clean architecture:
- **Contracts** (`contracts/`): Protocols and interfaces defining type resolution contracts
- **Resolvers** (`resolvers/`): Core resolution logic for schemas, responses, and references  
- **Services** (`services/`): High-level orchestration with `UnifiedTypeService`

**How**: Uses dependency injection and protocol-based design for comprehensive testing and extensibility.

#### Loader & Parser (`core/loader/` & `core/parsing/`)
**Why**: OpenAPI specs contain complex nested structures, circular references, and various schema patterns that need careful parsing.

**What**: Transforms OpenAPI specs into normalized Intermediate Representation (IR):
- **Schema Parser**: Core parsing with unified cycle detection
- **Reference Resolution**: Handles `$ref` links and circular dependencies  
- **Keyword Parsers**: Specialized handlers for `allOf`, `oneOf`, `anyOf`, `properties`
- **Transformers**: Extract inline enums, promote inline objects

**How**: Multi-pass parsing with state tracking and cycle detection to build clean IR models.

#### Visitors (`visit/`)
**Why**: Different parts of the generated client (models, endpoints, exceptions) require different code generation strategies.

**What**: Transform IR into Python code using the visitor pattern:
- **Model Visitor**: Generates dataclasses and enums from schemas
- **Endpoint Visitor**: Creates async methods from operations
- **Client Visitor**: Builds main API client class
- **Exception Visitor**: Generates error hierarchies

**How**: Each visitor specializes in one aspect of code generation, using templates and the unified type system.

#### Emitters (`emitters/`)
**Why**: Generated code must be properly organized into packages with correct imports and structure.

**What**: Write code to files with proper package structure:
- **Models Emitter**: Creates `models/` directory with schema classes
- **Endpoints Emitter**: Creates `endpoints/` with operation methods
- **Core Emitter**: Copies runtime dependencies to `core/`
- **Client Emitter**: Generates main client interface

**How**: Orchestrates file writing, import resolution, and package structure creation.

#### Supporting Systems
- **Context** (`context/`): Manages rendering state and imports across generation
- **Writers** (`core/writers/`): Code formatting and output utilities
- **Helpers** (`helpers/`): Legacy type resolution (now delegates to unified system)

## Unified Cycle Detection

### Why Cycle Detection?
OpenAPI specifications often contain circular references where Schema A references Schema B, which references back to Schema A. Without proper handling, this causes infinite recursion during code generation, resulting in stack overflow errors or infinite loops. Enterprise APIs commonly have these patterns in their data models.

### What Is Cycle Detection?
A sophisticated system that identifies and resolves circular dependencies in schema relationships while preserving the intended data structure. It tracks schema states throughout the parsing lifecycle and applies different resolution strategies based on the type of cycle detected.

```mermaid
graph TD
    A[Schema A] --> B[Schema B]
    B --> C[Schema C]
    C --> A
    
    D[Direct Self-Reference] --> D
    
    E[Deep Nesting] --> F[Level 1]
    F --> G[Level 2]
    G --> H[...]
    H --> I[Level N > MAX_DEPTH]
    
    subgraph "Detection Types"
        J[Structural Cycles]
        K[Self-References]
        L[Depth Limits]
    end
    
    subgraph "Resolution Strategies"
        M[Forward References]
        N[Placeholder Types]
        O[Depth Cutoffs]
    end
    
    J --> M
    K --> N
    L --> O
```

### How Cycle Detection Works

#### Detection Types
- **Structural Cycles**: Schema reference loops (A → B → C → A)
- **Self-References**: Direct self-references (User → User)
- **Depth Limits**: Recursion depth exceeded (configurable via `PYOPENAPI_MAX_DEPTH`)

#### Resolution Strategies
- **Forward References**: Uses Python string annotations `"ClassName"` for forward declarations
- **Placeholder Types**: Creates marked placeholders for problematic circular dependencies
- **Depth Cutoffs**: Handles deep nesting gracefully with configurable limits

#### Implementation Details
Located in `core/parsing/unified_cycle_detection.py` with:
- Schema state tracking through parsing lifecycle
- Configurable depth limits (default: 150 levels)
- Multiple placeholder strategies for different cycle types
- Integration with the unified type resolution system

## Development Standards

### Code Quality
- **Formatting**: Black (120 char line length)
- **Linting**: Ruff for code quality and import sorting
- **Type Safety**: mypy strict mode with 100% coverage
- **Compatibility**: Python 3.12+

### Testing Requirements
Follow cursor rules strictly:
- **Framework**: pytest only (no unittest.TestCase)  
- **Naming**: `test_<unit_of_work>__<condition>__<expected_outcome>()`
- **Documentation**: Include "Scenario:" and "Expected Outcome:" sections in docstrings
- **Structure**: Arrange/Act/Assert with clear separation and comments
- **Coverage**: ≥85% branch coverage enforced
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

### Why These Features?
Modern APIs require sophisticated clients that handle async operations, complex authentication, pagination, and error scenarios gracefully. Developers need type-safe, well-documented clients that integrate seamlessly with their development workflow and provide excellent IDE support.

### What Features Are Generated?
Production-ready Python clients with enterprise-grade capabilities, designed for modern async/await patterns and comprehensive type safety.

```mermaid
graph TB
    subgraph "Client Architecture"
        A[Main Client] --> B[Authentication Layer]
        A --> C[HTTP Transport]
        A --> D[Operation Endpoints]
    end
    
    subgraph "Type System"
        E[Dataclass Models] --> F[Enum Types]
        F --> G[Union Types]
        G --> H[Generic Collections]
    end
    
    subgraph "Advanced Features"
        I[Async Pagination] --> J[Response Unwrapping]
        J --> K[Error Handling]
        K --> L[Streaming Support]
    end
    
    subgraph "Developer Experience"
        M[IDE Autocomplete] --> N[Type Checking]
        N --> O[Rich Documentation]
        O --> P[Tag Organization]
    end
    
    A --> E
    D --> I
    B --> M
```

### How the Generated Clients Work

#### Modern Python Architecture
**Why**: APIs need to handle concurrent requests efficiently, and Python's async/await provides the best performance for I/O-bound operations.

**What**: 
- **Async-First**: All operations use `httpx.AsyncClient` for modern async/await patterns
- **Type Safety**: Complete type hints and dataclass models with mypy compatibility
- **Zero Dependencies**: Generated clients require no runtime dependency on this generator

**How**: Uses async context managers, typed dataclasses, and self-contained runtime code.

#### Developer Experience
**Why**: Developers spend significant time navigating APIs, and good tooling dramatically improves productivity.

**What**:
- **Tag-Based Organization**: Operations grouped by OpenAPI tags for intuitive navigation
- **Rich Documentation**: Extracted from OpenAPI descriptions with proper formatting
- **IDE Support**: Full autocomplete and type checking in modern IDEs

**How**: Generates structured modules with comprehensive docstrings and type annotations.

#### Advanced Features
**Why**: Production APIs require sophisticated features like pagination, authentication, and error handling.

**What**:
- **Pluggable Auth**: Bearer, API key, OAuth2, and custom authentication strategies
- **Smart Pagination**: Auto-detected cursor/page/offset patterns with async iteration
- **Error Handling**: Structured exception hierarchy with meaningful error messages
- **Response Unwrapping**: Automatic extraction of `data` fields from wrapper responses
- **Streaming Support**: Built-in support for streaming responses and downloads

**How**: Implements auth plugins, async iterators, custom exception classes, and response processors.

#### Production Ready
**Why**: Generated clients must work reliably in production environments without external dependencies.

**What**:
- **Client Independence**: Completely self-contained with copied runtime dependencies
- **Shared Core Support**: Multiple clients can share common runtime components
- **Post-Processing**: Generated code is automatically formatted and type-checked

**How**: Copies all required runtime code, supports shared core packages, and runs quality checks.

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
pyopenapi-gen examples/petstore.yaml --project-root . --output-package pyapis.petstore

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
pyopenapi-gen api_v1.yaml --project-root . --output-package pyapis.v1 --core-package pyapis.core

# Generate second client (reuses core)
pyopenapi-gen api_v2.yaml --project-root . --output-package pyapis.v2 --core-package pyapis.core

# Shared structure:
# pyapis/
# ├── core/              # Shared runtime (httpx, auth, etc.)
# ├── v1/                # First client
# └── v2/                # Second client
```

## Release Management & Semantic Versioning

### Automated Release Pipeline

The project uses **semantic-release** for automated version bumping, changelog generation, and publishing:

```mermaid
graph TD
    A[Conventional Commits] --> B[Push to main]
    B --> C[Semantic Release Workflow]
    C --> D{Analyze Commits}
    D -->|feat:| E[Minor Version Bump]
    D -->|fix:| F[Patch Version Bump]
    D -->|BREAKING CHANGE:| G[Major Version Bump]
    E --> H[Update pyproject.toml & __init__.py]
    F --> H
    G --> H
    H --> I[Generate CHANGELOG.md]
    I --> J[Create Git Tag]
    J --> K[Build & Publish to PyPI]
    K --> L[Create GitHub Release]
```

### Commit Message Format

Use **Conventional Commits** format for automatic version bumping:

```bash
# Patch version (0.8.7 → 0.8.8)
git commit -m "fix(parser): resolve circular reference detection"
git commit -m "fix(auth): handle expired tokens correctly"

# Minor version (0.8.7 → 0.9.0)  
git commit -m "feat(cli): add --dry-run option for testing"
git commit -m "feat(models): support custom serializers"

# Major version (0.8.7 → 1.0.0)
git commit -m "feat(api): redesign authentication system

BREAKING CHANGE: AuthPlugin interface changed, migrate to new authenticate() method"

# Other types (no version bump)
git commit -m "docs(readme): update installation instructions"
git commit -m "chore(deps): update dependencies"
git commit -m "test(parser): add edge case coverage"
```

### Release Branches & Environments

```bash
# Development Releases (TestPyPI)
git push origin staging          # Auto-publishes to test.pypi.org

# Production Releases (PyPI)  
git push origin main             # Auto-publishes to pypi.org (if conventional commits found)

# Manual TestPyPI Release
gh workflow run "Publish to TestPyPI (manual)" -f reason="Testing new feature"
```

### Version Configuration

Semantic release manages versions in multiple files automatically:

- `pyproject.toml:project.version` - Package version
- `pyproject.toml:tool.commitizen.version` - Commitizen tracking
- `src/pyopenapi_gen/__init__.py:__version__` - Runtime version

### Release Notes

Generated automatically from conventional commits:

- **Features** (`feat:`) → "✨ Features" section
- **Bug Fixes** (`fix:`) → "🐛 Bug Fixes" section  
- **Breaking Changes** (`BREAKING CHANGE:`) → "💥 Breaking Changes" section
- **Documentation** (`docs:`) → "📚 Documentation" section

### Testing Tools

```bash
# Check what the next version would be
poetry run semantic-release version --print

# Preview changelog generation
poetry run semantic-release changelog --print

# Validate commit messages
poetry run cz check --rev-range HEAD~5..HEAD

# Interactive commit helper
poetry run cz commit
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
pyopenapi-gen spec.yaml --project-root . --output-package pyapis.client
```

**Performance Issues with Large Specs**
```bash
# Skip type checking during development
pyopenapi-gen large_spec.yaml --no-postprocess --project-root . --output-package pyapis.large

# Increase recursion limits for deeply nested schemas
PYOPENAPI_MAX_DEPTH=300 pyopenapi-gen complex_spec.yaml --project-root . --output-package pyapis.complex
```

**Circular Reference Errors**
```bash
# Check cycle detection in action
pyopenapi-gen spec_with_cycles.yaml --verbose --project-root . --output-package pyapis.client

# Generated code will include forward references and placeholders for cycles
```

**Semantic Release Issues**
```bash
# Check current configuration
poetry run semantic-release generate-config

# Validate commit history
poetry run semantic-release version --print --noop

# Debug release workflow
poetry run semantic-release --verbose version --print
```

# Documentation Standards

## Universal Documentation Conventions
These standards apply to ALL documentation in this project and should be followed consistently:

### 1. Mermaid Diagrams for Logic Visualization
- Always use mermaid diagrams to visualize complex logic, workflows, and system relationships
- Include diagrams before diving into implementation details
- Make abstract concepts concrete through visual representation

### 2. Chapter Structure: Why → What → How
- **Why**: Start with the purpose, motivation, and context
- **What**: Explain what the component/feature/system does  
- **How**: Then provide implementation details, code examples, and technical specifics

### 3. Progressive Information Architecture
- Orientation before implementation
- Context before code
- Understanding before examples
- Visual aids before bullet lists

These principles ensure readers understand the reasoning and context before getting into technical details, making documentation more accessible and effective.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## Recent Updates

- ✅ Enhanced PyPI publishing workflow with twine-based automation
- ✅ Added comprehensive PyPI token validation and error handling  
- ✅ Implemented automated branch synchronization after releases
- ✅ Configured PYPI_API_TOKEN secret for reliable CI/CD publishing
