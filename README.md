# Python OpenAPI/Swagger Client Generator

A modern, async-first Python client generator for OpenAPI (Swagger) specifications. This tool creates robust, ergonomic, and highly-typed Python clients that make integrating with any HTTP API seamless, safe, and developer-friendly.

---

## Quick Start

### 1. Install

```bash
pip install pyopenapi-gen
```

### 2. Generate a Client

```bash
pyopenapi-gen gen input/openapi.yaml \
  --project-root . \
  --output-package pyapis.my_api_client
```

- By default, the core package will be generated as a subpackage under your output package (e.g., `pyapis/my_api_client/core/`).
- All imports in the generated client will use relative imports (e.g., `from .core.http_transport import ...`).

#### To use a shared core package:

```bash
pyopenapi-gen gen input/openapi.yaml \
  --project-root . \
  --output-package pyapis.my_api_client \
  --core-package pyapis.core
```

- Core files: `/absolute/path/to/your/project/pyapis/core/`
- Client files: `/absolute/path/to/your/project/pyapis/my_api_client/`
- Imports: `from pyapis.core.http_transport import ...`

### 3. Use the Generated Client

```python
import asyncio
from pyapis.my_api_client.config import ClientConfig
from pyapis.my_api_client.client import APIClient

async def main():
    config = ClientConfig(base_url="https://api.example.com", timeout=5.0)
    # Option 1: Manual close
    client = APIClient(config)
    users = await client.users.listUsers(page=1, pageSize=10)
    print(users)
    await client.close()

    # Option 2: Async context manager (recommended)
    async with APIClient(config) as client:
        users = await client.users.listUsers(page=1)
        print(users)

asyncio.run(main())
```

### 4. Customizing the Core Module Name/Location

> **IMPORTANT:**
> The value of `--core-package` **must match the full Python import path** to your core package as it will be imported in your project. For example, if your project is called `pyapis` and your core code is in `pyapis/core/`, you must use `--core-package pyapis.core`.
> 
> - If you do not set `--core-package`, the core code will be generated as a subpackage under your output package (e.g., `pyapis/my_api_client/core/`), and imports will be relative.
> - For most real-world projects, always use the full dotted path (e.g., `pyapis.core`) for shared core scenarios.
> 
> **Tip:** Using `--core-package` is strongly encouraged when you are generating multiple clients that should share the same core code. This is a common pattern in backend projects that integrate with multiple external systems—each client package can import from a single, shared core implementation, reducing duplication and easing maintenance.

#### Example: Shared Core in a Monorepo

Suppose your project structure is:

```bash
my-monorepo/
  pyapis/
    core/
    my_api_client/
    another_client/
```

Generate the client with:

```bash
pyopenapi-gen gen input/business_swagger.json \
  --project-root /absolute/path/to/my-monorepo \
  --output-package pyapis.my_api_client \
  --core-package pyapis.core
```

- Core files: `/absolute/path/to/my-monorepo/pyapis/core/`
- Client files: `/absolute/path/to/my-monorepo/pyapis/my_api_client/`
- Imports: `from pyapis.core.http_transport import ...`

> **Note:** This approach is ideal for backend projects with multiple API integrations, as it allows all generated clients to share a single, well-maintained core implementation.

#### Example: Standalone Client (Default)

If you want the core code inside the client output folder (standalone client):

```bash
pyopenapi-gen gen input/business_swagger.json \
  --project-root /absolute/path/to/my-monorepo \
  --output-package pyapis.my_api_client
```

- Core files: `/absolute/path/to/my-monorepo/pyapis/my_api_client/core/`
- Client files: `/absolute/path/to/my-monorepo/pyapis/my_api_client/`
- Imports: `from .core.http_transport import ...`

---

## Motivation

Building and maintaining HTTP clients for APIs by hand is a repetitive and error-prone process, especially as APIs evolve. While OpenAPI/Swagger specs promise automation, most generators fall short in type safety, extensibility, and developer experience. This project was created to address these challenges and provide a modern Python client generator.

- **Type Safety**: 100% type hints and dataclasses for all models and endpoints.
- **Async-First**: Modern Python codebases demand async support; this generator delivers it out of the box.
- **Modular & Extensible**: You can provide your own `http_transport.py` for custom HTTP client logic, and the generator supports pluggable authentication and pagination.
- **IntelliSense & DX**: Rich docstrings, grouped endpoints, and strong typing for a first-class IDE experience.
- **Minimal Dependencies**: Generated clients have ≤1 runtime dependency.
- **Graceful Degradation**: Handles incomplete specs with actionable warnings, not cryptic errors.
- **Testability**: Pure functions, clear boundaries, and high test coverage.
- **Strict Error Handling**: All errors received from the API are handled by raising an exception; only successful responses are returned as strongly typed response objects.

---

## What Kind of Client Does This Generator Create?

This generator produces a Python package that is ready for production use, with a focus on async-first APIs, strong typing, and modularity. The generated client is designed to be ergonomic, extensible, and easy to integrate into any modern Python codebase.

### 1. **Async-Only, Strongly-Typed Client**

The generated client is built around asynchronous programming and strong typing, ensuring that all HTTP calls are non-blocking and that your code benefits from full type hints and docstrings.

- **Async API**: All HTTP calls are async, using `httpx.AsyncClient` by default.
- **Per-Tag Endpoint Grouping**: Each OpenAPI tag becomes a Python class (e.g., `UsersClient`, `JobsClient`), accessible as attributes on the main `APIClient`.
- **Typed Models**: Every schema in the spec becomes a Python dataclass, with type hints and docstrings extracted from the spec.
- **Rich Docstrings**: Endpoint methods and model fields include docstrings from the OpenAPI descriptions for IDE help and documentation.

### 2. **Modular Structure**

The generated client is organized as a real Python package, with a clear and modular structure. This makes it easy to use, extend, and maintain, whether you are integrating it into a large project or using it as a standalone client.

```my_api_client/
├── __init__.py
├── client.py                # Main APIClient class, tag clients as attributes
├── config.py                # ClientConfig: env/TOML/kwarg config layering
├── core/                    # All runtime dependencies (see below)
│   ├── http_transport.py
│   ├── exceptions.py
│   ├── streaming_helpers.py
│   ├── pagination.py
│   ├── utils.py
│   └── auth/
│       ├── base.py
│       └── plugins.py
├── models/
│   ├── <model>.py           # One file per schema, all as dataclasses
├── endpoints/
│   ├── <tag>.py             # One file per tag, with async methods per operation
└── ...
```

> **Note:** If you use a custom core name (e.g., `shared_core`), all imports will reference that folder instead of `core`.

### 3. **Features at a Glance**

The generator is packed with features that make the generated client powerful, flexible, and easy to use. Here are some of the highlights:

- **Endpoint Grouping**: Methods are organized by OpenAPI tags for concise imports and discoverability.
- **Pluggable Auth**: Built-in Bearer and custom header auth plugins; easy to add more.
- **Pagination Helpers**: Async iterators for cursor/page/offset-based pagination, auto-detected from the spec.
- **Error Handling**: Uniform exception hierarchy (`HTTPError`, `ClientError`, `ServerError`), with spec-specific aliases if defined.
- **Lazy Loading**: Uses `__getattr__` for efficient imports and memory usage.
- **Config Layering**: Configure via constructor, environment variables, or TOML config file.
- **CLI Tooling**: One-line CLI (`pyopenapi-gen gen <spec> -o <path>`) with diff-check, force overwrite, and plugin flags.
- **Warnings & Hints**: Actionable warnings for missing tags, operation IDs, descriptions, and more, with remediation hints.
- **Snapshot & Integration Tests**: Generator is tested against public specs (e.g., Petstore) and includes snapshot tests for generated code.

### 4. **Plugin Architecture**

Extensibility is a core design goal. The generator and the generated client both support plugins for emitters, authentication, and pagination. This allows you to customize or extend functionality without modifying the core codebase.

- **Emitters**: Swap or extend model, endpoint, or client emitters via plugins.
- **Auth Plugins**: Implement the `BaseAuth` protocol to add new authentication methods.
- **Pagination Plugins**: Provide custom pagination strategies.
- **CLI Plugin Loading**: Pass plugins via CLI flags or wire them up in code.

### 5. **Generated Client Example**

Below is a minimal example of how to use a generated client in your own code. This demonstrates async usage, configuration, and calling an endpoint.

```python
import asyncio
from my_api_client.config import ClientConfig
from my_api_client.client import APIClient

async def main():
    config = ClientConfig(base_url="https://api.example.com", timeout=5.0)
    # Option 1: Async context manager (recommended)
    async with APIClient(config) as client:
        users = await client.users.listUsers(page=1)
        print(users)

    # Option 2: Manual close
    client = APIClient(config)
    users = await client.users.listUsers(page=1, pageSize=10)
    print(users)
    await client.close()

asyncio.run(main())
```

---

## CLI Usage

The generator comes with a powerful CLI that makes it easy to generate clients from your OpenAPI spec. You can customize the output, enable plugins, and control overwriting behavior with simple flags.

```bash
pip install pyopenapi-gen
pyopenapi-gen gen input/openapi.yaml \
  --project-root . \
  --output-package pyapis.my_api_client
```

- `--project-root`: Path to the root of your Python project (can be relative or absolute; e.g., `.` or `/path/to/project`).
- `--output-package`: Python package path for the generated client (e.g., 'pyapis.my_api_client').
- `--core-package`: (Optional) Python package path for the core package (e.g., 'pyapis.core'). If not set, the core package will be placed under the output package.
- `--force`: Overwrite output without diff check.
- `--no-postprocess`: Skip post-processing (type checking, etc.)

### Generate Markdown Documentation

```bash
pyopenapi-gen docs input/openapi.yaml --output docs/
```

---

## Authentication Plugins

The client supports pluggable authentication via the `BaseAuth` protocol. You can use built-in plugins or implement your own. Below are the available plugins:

> **Note:** In generated clients, import plugins from your own core module (e.g., `from .core.auth.plugins import BearerAuth`), not from `pyopenapi_gen`.

### BearerAuth

For simple Bearer token authentication:

```python
from .core.auth.plugins import BearerAuth  # In generated client
transport = HttpxTransport(base_url, auth=BearerAuth("your-token"))
```

### HeadersAuth

For arbitrary custom headers:

```python
from .core.auth.plugins import HeadersAuth
transport = HttpxTransport(base_url, auth=HeadersAuth({"X-API-Key": "value"}))
```

### ApiKeyAuth

For API key authentication in header, query, or cookie:

```python
from .core.auth.plugins import ApiKeyAuth
# Header
auth = ApiKeyAuth("mykey", location="header", name="X-API-Key")
# Query
auth = ApiKeyAuth("mykey", location="query", name="api_key")
# Cookie
auth = ApiKeyAuth("mykey", location="cookie", name="sessionid")
transport = HttpxTransport(base_url, auth=auth)
```

### OAuth2Auth

For OAuth2 Bearer tokens, with optional auto-refresh:

```python
from .core.auth.plugins import OAuth2Auth
# Static token
auth = OAuth2Auth("access-token")
# With refresh callback (async)
async def refresh_token(old_token):
    # ... fetch new token ...
    return "new-token"
auth = OAuth2Auth("access-token", refresh_callback=refresh_token)
transport = HttpxTransport(base_url, auth=auth)
```

### Composing Multiple Auth Plugins

For advanced scenarios, you can combine multiple authentication plugins using `CompositeAuth`. This allows you to, for example, add both a Bearer token and custom headers to every request:

```python
from .core.auth.plugins import BearerAuth, HeadersAuth
from .core.auth.base import CompositeAuth

composite_auth = CompositeAuth(
    BearerAuth("your-token"),
    HeadersAuth({"X-API-Key": "value"})
)
transport = HttpxTransport(base_url, auth=composite_auth)
```

Each plugin will be applied in sequence, so you can flexibly combine any number of authentication strategies.

See the `.core.auth.plugins` module in your generated client for details and extension points.

---

## Advanced Features

Beyond the basics, the generator and generated clients include advanced features for real-world API integration, error handling, and configuration.

- **Pagination**: Built-in async paginator for APIs using `next` tokens, page numbers, or offset.
- **Error Mapping**: Maps HTTP status codes to exception classes; generates spec-specific exceptions if defined.
- **Config Layering**: Supports constructor kwargs, environment variables (`PYOPENAPI_*`), and TOML config at `~/.config/pyopenapi-gen.toml`.
- **Telemetry**: Optional, opt-in anonymous usage stats (disabled by default).
- **Docs Generation**: Emit Markdown docs and publish via MkDocs Material.

---

## Independence from pyopenapi_gen

The generated client code is **fully independent** and does not require `pyopenapi_gen` at runtime. All runtime dependencies (HTTP transport, authentication, exceptions, utilities) are included in the generated `core/` module (or your custom core name). You can use the generated client in any Python project without installing the generator package.

### Output Structure Example

```bash
my_generated_client/
    core/
        http_transport.py
        exceptions.py
        streaming_helpers.py
        pagination.py
        utils.py
        config.py
        auth/
            base.py
            plugins.py
    models/
    endpoints/
    __init__.py
    py.typed
    README.md
```

### Shared Core

If you generate multiple clients for the same system, you can configure the generator to use a shared core module. In this case, import paths will be relative to the shared core location. See the generator options for details.

---

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, please follow the guidelines below to ensure a smooth process.

- Fork, branch, and PR as usual.
- All code must be Black-formatted, Ruff-clean, and 100% mypy-typed.
- Tests must pass locally and on CI (macOS & Ubuntu, Python 3.10–3.12).
- See the `src/pyopenapi_gen` folder for architecture and core logic.

### Running Tests and Linting Locally

```bash
pytest
mypy src/
ruff check src/
```

---

## License

This project is licensed under the MIT License for the generator itself. Generated clients are Apache-2.0 by default, making them suitable for use in both open source and proprietary projects.

---

## v1.0.0 Release Notes

- First stable release! 🎉
- Async-first, type-safe Python OpenAPI client generator
- Modular plugin architecture (emitters, auth, pagination)
- CLI for client and docs generation
- High test coverage, Black/Ruff/mypy enforced
- Ready for production use and PyPI distribution
