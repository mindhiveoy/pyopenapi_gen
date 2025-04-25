# Python Swagger Client Generator

An async-first Python client generator that creates feature-rich, easy-to-use clients from OpenAPI (Swagger) specifications. It lowers the barrier to integrating with any HTTP API by automating model classes, endpoint methods, CLI tooling, and plugin extensions.

## Motivation

Maintaining hand-crafted HTTP clients for every API is time-consuming, error-prone, and hard to keep up-to-date. With this generator, you can:

- Automate client generation directly from your OpenAPI spec
- Leverage async HTTP calls using `httpx` out of the box
- Eliminate boilerplate for request/response models and endpoint wrappers
- Integrate docs, telemetry, and plugins in a unified pipeline

## Features

- **Async-only Client**: Built on `httpx.AsyncClient` for modern async codebases
- **Data Models**: Typed Python dataclasses for every schema
- **Strong Typing & IDE Support**: Auto-generated type hints and method signatures for robust code completion and a superior developer experience
- **Endpoints Emitter**: Per-tag modules with support for path, query, JSON body, multipart, and streaming responses
- **Pagination Helpers**: Cursor- and page-based pagination utilities via plugins
- **Plugin Architecture**: Extend with custom emitters, auth plugins (`BaseAuth`), and pagination strategies
- **Telemetry**: Optional, opt-in telemetry for usage tracking
- **Documentation Emitter**: Generate Markdown docs and publish via MkDocs Material
- **CLI**: `gen` and `docs` commands with diff-check, force flags, and verbose options

## Quickstart

Install the generator (requires Python 3.10+):

```bash
pip install pyopenapi-gen
```

Generate a client from your spec:

```bash
pyopenapi-gen gen input/business_swagger.json --output generated --force
```

## Using the Generated Client

```python
import asyncio
from my_client.config import ClientConfig
from my_client.client import APIClient

async def main():
    config = ClientConfig(base_url="https://api.example.com", timeout=5.0)
    client = APIClient(config)

    # Call an endpoint (e.g., list_pets)
    pets = await client.pets.list_pets(limit=10)
    print(pets)

    await client.close()

asyncio.run(main())
```

## Plugin Architecture

The generator is built around a plugin system:

- **Custom Emitters**: Swap or extend any of the built-in emitters (models, endpoints, client)
- **Auth Plugins**: Implement the `BaseAuth` protocol to add new authentication methods
- **Pagination Plugins**: Provide custom pagination via the `paginate_by_next` or new strategies

You can pass plugins via the CLI (`--auth` flag) or wire them up in code. Check the `auth/` directory for examples.

## Contributing

Contributions are welcome! To get started:

1. Fork the repository and create a feature branch
2. Add or update tests to cover your changes
3. Follow PEP 8 and run `black .`
4. Open a pull request referencing any related issues
5. Ensure all tests pass locally with `pytest`

## License

MIT © Your Name
