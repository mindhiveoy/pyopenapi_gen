# Python OpenAPI/Swagger Client Generator

A modern, async-first Python client generator for OpenAPI (Swagger) specifications. This tool creates robust, ergonomic, and highly-typed Python clients that make integrating with any HTTP API seamless, safe, and developer-friendly.

---

## Motivation

Building and maintaining HTTP clients for APIs by hand is a repetitive and error-prone process, especially as APIs evolve. While OpenAPI/Swagger specs promise automation, most generators fall short in type safety, extensibility, and developer experience. This project was created to address these challenges and provide a truly modern Python client generator.

- **Type Safety**: 100% type hints and dataclasses for all models and endpoints.
- **Async-First**: Modern Python codebases demand async support; this generator delivers it out of the box.
- **Modular & Extensible**: Plugin architecture for emitters, authentication, and pagination.
- **IntelliSense & DX**: Rich docstrings, grouped endpoints, and strong typing for a first-class IDE experience.
- **Minimal Dependencies**: Generated clients have ≤1 runtime dependency.
- **Graceful Degradation**: Handles incomplete specs with actionable warnings, not cryptic errors.
- **Testability**: Pure functions, clear boundaries, and high test coverage.

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

```
my_api_client/
├── __init__.py
├── client.py                # Main APIClient class, tag clients as attributes
├── config.py                # ClientConfig: env/TOML/kwarg config layering
├── exceptions.py            # HTTPError, ClientError, ServerError, etc.
├── auth/
│   ├── base.py              # BaseAuth protocol for plugins
│   ├── plugins.py           # BearerAuth, HeadersAuth, etc.
├── models/
│   ├── <model>.py           # One file per schema, all as dataclasses
├── endpoints/
│   ├── <tag>.py             # One file per tag, with async methods per operation
└── ...
```

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
    client = APIClient(config)

    # Call an endpoint (e.g., list users)
    users = await client.users.listUsers(page=1, pageSize=10)
    print(users)

    await client.close()

asyncio.run(main())
```

### 6. **CLI Usage**

The generator comes with a powerful CLI that makes it easy to generate clients from your OpenAPI spec. You can customize the output, enable plugins, and control overwriting behavior with simple flags.

```bash
pip install pyopenapi-gen
pyopenapi-gen gen input/openapi.yaml --output generated --force
```

- `--name`: Custom client package name
- `--auth`: Comma-separated list of auth plugins
- `--docs`: Also generate Markdown docs
- `--telemetry`: Enable opt-in telemetry
- `--force`: Overwrite output directory without diff check

---

## Advanced Features

Beyond the basics, the generator and generated clients include advanced features for real-world API integration, error handling, and configuration.

- **Pagination**: Built-in async paginator for APIs using `next` tokens, page numbers, or offset.
- **Error Mapping**: Maps HTTP status codes to exception classes; generates spec-specific exceptions if defined.
- **Config Layering**: Supports constructor kwargs, environment variables (`PYOPENAPI_*`), and TOML config at `~/.config/pyopenapi-gen.toml`.
- **Telemetry**: Optional, opt-in anonymous usage stats (disabled by default).
- **Docs Generation**: Emit Markdown docs and publish via MkDocs Material.

---

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, please follow the guidelines below to ensure a smooth process.

- Fork, branch, and PR as usual.
- All code must be Black-formatted, Ruff-clean, and 100% mypy-typed.
- Tests must pass locally and on CI (macOS & Ubuntu, Python 3.10–3.12).

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
