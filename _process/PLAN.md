# Project Plan – Python Swagger Client Generator

## 1. Vision
Build a modern, ergonomic Python 3.12 client‑library generator for OpenAPI/Swagger specs that emphasises:
* 100 % type hints & dataclasses (default)
* Modular plugin architecture for emitters & feature extensions – default dataclasses (emitter) with optional plugins (Pydantic/attrs, auth schemes, etc.)
* Rich IntelliSense: full docstrings extracted from OpenAPI and attached to methods & model fields
* Endpoint grouping: methods organised by OpenAPI tags – each tag becomes its own class & module for concise imports
* Lazy loading architecture for efficient imports and reduced memory footprint
* Uniform error handling via custom exception hierarchy (HTTPError, ValidationError, etc.) that surfaces actionable hints
* Pluggable authentication system with default support for bearer tokens and custom headers
* Initial spec support: OpenAPI 3.1 (plugin‑driven design will allow 3.0/2.x later)
* Async-first API implementation with architecture supporting sync API generation in the future
* Graceful handling of incomplete specs with actionable warnings
* Minimal external runtime dependencies (≤1)
* Highly testable design with clear component boundaries and pure functions
* Excellent DX – black‑formatted, ruff‑clean, 100 % mypy‑typed
* One‑line CLI (`pyopenapi-gen gen <spec_url> -o <path>`) with rich `--help` and shell completion

## 2. High‑Level Milestones
| Phase | Deliverable | Target Date (tbd) |
|-------|-------------|--------------------|
| 0 | Project bootstrap (repo, CI, tooling, this PLAN) | done |
| 1 | MVP generator that fetches spec & emits basic async client (models + endpoints) | |
| 2 | Pagination, authentication helpers, retry & timeout plumbing | |
| 3 | Complete test suite against public pet‑store API | |
| 4 | Documentation site & example projects | |
| 5 | Package v1.0.0 on PyPI + Homebrew formula | |
| 6 | Add sync client generation capability | |

## 3. Architecture Sketch
```
Swagger/OpenAPI spec  →  `pyopenapi_gen` core
                                       ↓
   ┌─────────────────────────────────────────────────────────┐
   │  1. Parsing & validation – openapi-spec-validator       │
   │  2. Schema traversal – openapi-core                     │
   │  3. Internal IR (dataclasses)                           │
   │  4. Code‑emitter (Jinja2 + Python `ast`)                │
   │     - Async-first with abstraction for future sync      │
   │     - Pure transformation functions where possible      │
   │     - Dependency injection for testability              │
   │     - Warning collection with remediation hints         │
   │     - Lazy-loading module structure                     │
   └─────────────────────────────────────────────────────────┘
                                        ↓
     `dist/my_api_client/`  (PEP 517 package with modular structure)
```

## 4. Implementation Backlog
- [ ] Setup continuous integration (GitHub Actions) with 3.12 matrix
- [ ] Add pre‑commit hooks: black, ruff, mypy
- [x] Research parser libs – DECISION: use openapi-spec-validator for validation and openapi-core for schema traversal to ensure OpenAPI 3.1 compliance
- [ ] Define internal IR dataclasses
- [ ] Design test fixtures for various OpenAPI spec patterns
- [ ] Implement unit test helpers and mocks for each component
- [ ] Implement warning system for incomplete specs with actionable remediation hints
- [ ] Create fallback strategies for missing metadata (e.g., generating operationIds, inferring types, auto-tagging)
- [ ] Design modular folder structure for generated client
- [ ] Implement lazy loading mechanism for tag classes and endpoints
- [ ] Design and implement authentication plugin system
  - [ ] Default bearer token authentication
  - [ ] Custom header authentication
  - [ ] Extension mechanism for custom auth methods
- [ ] Write model renderer → `models/` directory with one file per model
- [ ] Write async endpoint renderer: generate per‑tag modules/classes with async methods
- [ ] Design HTTP client abstraction that supports async now but allows for sync in the future
- [ ] Extract OpenAPI descriptions → docstrings for methods & dataclass fields
- [ ] Design and implement exception hierarchy (`pyopenapi_gen.exceptions`) with helpful, hint‑rich error messages
- [ ] Define generic plugin interface (emitters, spec adapters, extras)
- [ ] CLI wrapper (`pyopenapi-gen gen <spec_url> -o <path> --name <client_name>`) using typer/click
- [ ] Provide `tests/test_petstore.py` using generated async client
- [ ] Design pagination helper (cursor, page‑number, offset – auto‑detect from spec)
- [ ] Design HTTP client abstraction that supports async now but allows for sync in the future
- [ ] Implement configuration layer (retries, timeouts, base‑url overrides)
- [ ] Generate API reference docs using mkdocs‑material & pdoc
- [ ] Publish docs site via GitHub Pages
- [ ] Add optional anonymous telemetry toggle to gather generator usage stats

## 5. Tooling
* black, ruff, mypy – enforced via CI and pre‑commit
* pytest + coverage with target of >90% test coverage
* pytest-mock for mocking external dependencies
* factory_boy for test data generation
* packaging with `build` & `hatchling`

## 6. Risks & Open Questions
1. Spec variability – 2.x v 3.x differences.
2. Performance on very large specs (>10 MB).
3. Designing HTTP client abstraction to cleanly support future sync implementation without code duplication.
4. Choice of async HTTP client library (aiohttp, httpx) - need one with good typing support.
5. Balancing code purity for testing vs. practical implementation concerns.
6. How aggressively to auto-fix issues vs. requiring manual intervention.
7. Performance impact of lazy loading vs. convenience of usage.

## 7. Next Actions
* Install and set up dependency packages: openapi-spec-validator and openapi-core
* Research and select async HTTP client library (httpx recommended for future sync/async compatibility)
* Design warning collection system with actionable remediation hints
* Create proof-of-concept for spec validation and traversal with unit tests
* Design HTTP client abstraction layer that will support both async now and sync later
* Implement IR dataclass prototypes and write tests for serialization/deserialization
* Define testing strategy document with examples for each component
* Design folder structure and lazy loading mechanism
* Define parameters for client customization (client name, module naming patterns)
* Scaffold CLI entrypoint

## 8. Testing Strategy
* **Unit Tests**: Test individual components in isolation (parsers, transformers, renderers)
* **Integration Tests**: Test the flow from spec to generated code
* **Snapshot Tests**: Compare generated code against expected outputs
* **Property-Based Tests**: Generate random valid specs and ensure the generator produces valid code
* **Fixtures & Mocks**: Create reusable test fixtures for common OpenAPI patterns
* **Test Coverage**: Aim for >90% test coverage across all components
* **Test Organization**: Mirror the package structure in the test directory
* **Edge Cases**: Test incomplete/malformed specs to ensure graceful handling and appropriate warnings

## 9. Warning System
* **Warning Levels**: Info, Warning, Error (errors don't stop generation but indicate serious issues)
* **Categories**:
  * Missing Tags - Auto-assign default tags with guidance on how to add proper tags
  * Missing OperationIDs - Generate from path and method with hint on adding explicit IDs
  * Incomplete Type Information - Use fallback types (any/object) with suggestion for proper typing
  * Inconsistent Naming - Detect and suggest standardized naming conventions
  * Missing Descriptions - Flag operations/parameters without descriptions
* **Output Formats**: Console, JSON report, markdown report for easy integration into API documentation
* **Remediation Hints**: Each warning includes an explanation of the issue and specific steps to fix it
* **Examples**: Provide YAML/JSON snippets showing how to fix each warning

## 10. Generated Client Structure
```
my_api_client/
├── __init__.py                  # Client factory + version exports
├── client.py                    # Base client with auth, config
├── exceptions.py                # Exception hierarchy
├── auth/
│   ├── __init__.py              # Authentication plugin registry
│   ├── base.py                  # Base auth plugin interface
│   ├── bearer.py                # Bearer token authentication
│   └── headers.py               # Custom headers authentication
├── models/
│   ├── __init__.py              # Public exports
│   ├── base.py                  # Base model classes
│   ├── <model_name>.py          # One file per model
│   └── ...
├── tags/
│   ├── __init__.py              # Lazy imports for tag classes
│   ├── <tag_name>.py            # One file per API tag
│   └── ...
└── endpoints/
    ├── __init__.py              # Common endpoint utilities
    ├── <tag_name>/
    │   ├── __init__.py          # Lazy imports for endpoints
    │   ├── <operation_id>.py    # One file per operation
    │   └── ...
    └── ...
```

### Lazy Loading Implementation
* Use `__getattr__` in relevant `__init__.py` files to dynamically import modules on first access
* Add explicit type annotations using Protocols to maintain type checking
* Document import patterns in client examples 
* Provide explicit imports option for users who prefer to control imports 
* Support for bulk pre-loading of modules when memory efficiency is less critical

## 18. Finalised Decisions & Conventions (v1)

**Runtime & Networking**
* Standard HTTP stack: **httpx 0.25+** – offers both async & sync APIs with first‑class type hints.
* `HttpTransport` protocol defines a pluggable adapter (`async def send(request: httpx.Request) -> httpx.Response`).  Alternate transports may be registered via plugins.

**Code Generation**
* Templates rendered with Jinja2; generated source is ALWAYS run through Black (`black --quiet -`).  AST usage limited to small helper utilities (e.g., adding type checking aliases) to keep templates readable.

**IR Scope for v1.0**
* ✓  Paths / operations / params / request & response bodies / security / enums / compositional schemas (`oneOf` etc.)
* ✗  Callbacks, webhooks, links – deferred to later release.

**Pagination**
* Detection precedence: `Link` header → `next` JSON field → page/offset query params.
* Paginator base class `AsyncPaginator` exposed; users can override.

**Exception Mapping**
* Core `HTTPError(status, payload)` subclassing by status **category** (e.g., `ClientError4XX`, `ServerError5XX`).
* If spec defines a named error schema, generator emits dedicated exception class aliased to the relevant category.

**Auth Plugin Interface**
* `class BaseAuth(Protocol): async def on_request(self, req: httpx.Request) -> None` and optional `async def on_response(self, res: httpx.Response) -> None` for token refresh.
* Multiple auth plugins executed in registration order; each may mutate request/response.

**Configuration**
* `ClientConfig` values can be provided via constructor kwargs, environment variables (`PYOPENAPI_*`), or a TOML file at `~/.config/pyopenapi‑gen.toml` (later overrides earlier).

**Plugin Discovery**
* Uses Python entry‑points group `pyopenapi_gen.plugins`.  CLI flag `--plugins extra_pkg,local.path:Plugin` for ad‑hoc loading.

**Telemetry**
* POSTs anonymised payload (`generator_version`, `python_version`, `os`, `ok`) to `https://stats.pyopenapi.dev/collect`.
* Disabled by default; enabled via `--telemetry on` or `PYOPENAPI_TELEMETRY=on`.

**Package Naming Rules**
* Default: slugified spec title, lower‑snake, max 50 chars.  Reserved Python keywords suffixed with `_client`.
* `--force` flag required when output directory already exists.

**Documentation Generation**
* Docs produced only when `--docs` flag passed or via separate `pyopenapi-gen docs` command.
* Site emitted to `<output>/docs_site/`.

**CI & Release**
* Generator supports Python 3.10 → 3.12.  GitHub Actions matrix: ubuntu‑latest, macos‑latest.
* Generator released under MIT; generated clients under Apache‑2.0 with templated headers.

## 19. Implementation Workflow & File Roles

To ensure each functional slice is **production‑ready** before new work starts we adopt an incremental, test‑gated approach:

1. **Slice‑by‑Slice Development**
   * Work is broken into small, vertical slices (e.g., *IR Loader*, *Model Emitter*).
   * Each slice is considered *Done* only when its unit & integration tests meet ≥ 90 % coverage **and** the public API is frozen.
2. **Definition of Done**
   * All acceptance criteria & warnings satisfied
   * Tests green on CI matrix (Py 3.10‑3.12, macOS & Ubuntu)
   * Ruff, Black, mypy clean
   * Docs for slice generated & rendered without errors
3. **Task Tracking**
   * Granular tasks and their statuses are maintained in `_process/TASKS.md` (not shipped in final artefact).
   * Status keywords: `TODO`, `IN‑PROGRESS`, `BLOCKED`, `DONE`.
4. **Folder & File Conventions**
   * `_process/` – planning & process artefacts (PLAN.md, ARCHITECTURE.md, TASKS.md, ADRs). **Never** included in packaged release.
   * `src/pyopenapi_gen/` – generator source code.
   * `tests/` – generator test‑suite.
   * Generated client lives under the user‑specified output dir, outside repo tree.
5. **AI Instruction Boundaries**
   * Inline comments denoted `# AI‑INSTRUCTION:` may appear in process files only; generator source **must not** include any AI scaffolding commentary.
6. **Phase Gate**
   * CI enforces minimum coverage threshold before the `next‑slice` GitHub branch can merge.

> NOTE: The next commit will introduce `_process/TASKS.md` seeded with current backlog items, each mapped to the slices above.

---
_Last updated: <!-- date placeholder -->_ 