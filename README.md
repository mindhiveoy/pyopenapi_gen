# PyOpenAPI Generator

Modern, async-first Python client generator for OpenAPI specifications. Creates robust, type-safe clients that require no runtime dependencies on this generator.

## Quick Start

### Install
```bash
pip install pyopenapi-gen
```

### Generate Client
```bash
pyopenapi-gen gen openapi.yaml \
  --project-root . \
  --output-package my_api_client
```

### Use Generated Client
```python
import asyncio
from my_api_client.client import APIClient
from my_api_client.core.config import ClientConfig

async def main():
    config = ClientConfig(base_url="https://api.example.com")
    async with APIClient(config) as client:
        users = await client.users.list_users(page=1)
        print(users)

asyncio.run(main())
```

## Configuration Options

### Standalone Client (Default)
```bash
pyopenapi-gen gen openapi.yaml \
  --project-root . \
  --output-package my_api_client
```
Creates self-contained client with embedded core dependencies.

### Shared Core (Multiple Clients)
```bash
pyopenapi-gen gen openapi.yaml \
  --project-root . \
  --output-package clients.api_client \
  --core-package clients.core
```
Multiple clients share a single core implementation.

### Additional Options
```bash
--force           # Overwrite without prompting
--no-postprocess  # Skip formatting and type checking
```

## Features

✨ **Type Safety**: Full type hints and dataclass models  
⚡ **Async-First**: Built for modern Python async/await patterns  
🏗️ **Modular**: Pluggable authentication, pagination, and HTTP transport  
🧠 **Smart IDE Support**: Rich docstrings and auto-completion  
📦 **Zero Dependencies**: Generated clients are self-contained  
🛡️ **Robust**: Graceful handling of incomplete specs  
🎯 **Error Handling**: Structured exceptions, only successful responses returned

## Generated Client Structure

```
my_api_client/
├── client.py           # Main APIClient with tag-grouped methods
├── core/               # Self-contained runtime dependencies
│   ├── config.py       # Configuration management
│   ├── http_transport.py # HTTP client abstraction
│   ├── exceptions.py   # Error hierarchy
│   └── auth/           # Authentication plugins
├── models/             # Dataclass models from schemas
│   └── user.py
├── endpoints/          # Operation methods grouped by tag
│   └── users.py
└── __init__.py
```

## Client Features

- **Tag Organization**: Operations grouped by OpenAPI tags (`client.users.list_users()`)
- **Type Safety**: Full dataclass models with type hints
- **Async Iterators**: Auto-detected pagination patterns
- **Rich Auth**: Bearer, API key, OAuth2, and custom strategies
- **Error Handling**: Structured `HTTPError`, `ClientError`, `ServerError` hierarchy
- **Response Unwrapping**: Automatic extraction of `{ "data": ... }` patterns

## Known Limitations

Some OpenAPI features have simplified implementations:

- **Parameter Serialization**: Uses HTTP client defaults rather than OpenAPI `style`/`explode` directives
- **Complex Multipart**: Basic file upload support; complex multipart schemas simplified  
- **Response Headers**: Only response body is returned, not headers
- **Parameter Defaults**: OpenAPI schema defaults not automatically applied to method signatures

Contributions welcome to enhance OpenAPI specification coverage!

### Bearer Token
```python
from .core.auth.plugins import BearerAuth
auth = BearerAuth("your-token")
```

### API Key
```python
from .core.auth.plugins import ApiKeyAuth
# Header, query, or cookie
auth = ApiKeyAuth("key", location="header", name="X-API-Key")
```

### OAuth2 with Refresh
```python
from .core.auth.plugins import OAuth2Auth
auth = OAuth2Auth("token", refresh_callback=refresh_func)
```

### Custom Headers
```python
from .core.auth.plugins import HeadersAuth
auth = HeadersAuth({"X-Custom": "value"})
```

### Composite Auth
```python
from .core.auth.base import CompositeAuth
auth = CompositeAuth(BearerAuth("token"), HeadersAuth({"X-Key": "val"}))
```

## Development

### Setup
```bash
git clone https://github.com/your-org/pyopenapi_gen.git
cd pyopenapi_gen
source .venv/bin/activate  # Activate virtual environment
pip install -e '.[dev]'   # Install in development mode
```

### Quality Workflow
```bash
# Before committing - auto-fix what's possible
make quality-fix

# Run all quality checks (matches CI pipeline)
make quality

# Individual commands
make format               # Auto-format with Black
make lint-fix             # Auto-fix linting with Ruff  
make typecheck            # Type checking with mypy
make security             # Security scanning with Bandit
make test                 # Run all tests
```

### Contributing

Contributions welcome! Please ensure:

- **Code Quality**: All `make quality` checks pass
- **Testing**: pytest with ≥90% branch coverage
- **Compatibility**: Python 3.10-3.12 support
- **Documentation**: Update relevant docs for new features

The `make quality-fix` command will auto-fix most formatting and linting issues. All pull requests must pass the full `make quality` check suite.

## License

MIT License - Generated clients are Apache-2.0 by default.