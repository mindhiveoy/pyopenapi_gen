# PyOpenAPI Generator

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Modern, enterprise-grade Python client generator for OpenAPI specifications.**

Generate async-first Python clients from OpenAPI specs with complete type safety, automatic field mapping, and zero runtime dependencies.

## Why PyOpenAPI Generator?

### Modern Python Architecture

- **Async-First**: All operations use `async`/`await` with `httpx` for high performance
- **Complete Type Safety**: Full type hints, dataclass models, and mypy strict mode compatibility
- **Truly Independent**: Generated clients require no runtime dependency on this package

### Enterprise-Grade Features

- **Complex Schema Handling**: Advanced cycle detection for circular references and deep nesting
- **Automatic Field Mapping**: Seamless conversion between API naming (snake_case, camelCase) and Python conventions
- **Pluggable Authentication**: Bearer tokens, API keys, OAuth2, custom auth, or combine multiple strategies
- **Streaming Support**: Built-in SSE and binary streaming for real-time data

### Superior Developer Experience

- **Rich IDE Support**: Full autocomplete, inline docs, and type checking in modern editors
- **Tag-Based Organization**: Operations automatically grouped by OpenAPI tags for intuitive navigation
- **Structured Exceptions**: Type-safe error handling with meaningful exception hierarchy
- **Easy Testing**: Auto-generated Protocol classes for each endpoint enable strict type-safe mocking

## Installation

```bash
pip install pyopenapi-gen
```

Or with Poetry:

```bash
poetry add pyopenapi-gen
```

## ⚡ Quick Start

### 1. Generate Your First Client

```bash
pyopenapi-gen openapi.yaml \
  --project-root . \
  --output-package my_api_client
```

This creates a complete Python package at `./my_api_client/` with:

- Type-safe models from your schemas
- Async methods for all operations
- Built-in authentication support
- Complete independence from this generator

### 2. Use the Generated Client

```python
import asyncio
from my_api_client.client import APIClient
from my_api_client.core.config import ClientConfig
from my_api_client.core.http_transport import HttpxTransport
from my_api_client.core.auth.plugins import BearerAuth

async def main():
    # Configure the client
    config = ClientConfig(
        base_url="https://api.example.com",
        timeout=30.0
    )
  
    # Optional: Add authentication
    auth = BearerAuth("your-api-token")
    transport = HttpxTransport(
        base_url=config.base_url,
        timeout=config.timeout,
        auth=auth
    )
  
    # Use as async context manager
    async with APIClient(config, transport=transport) as client:
        # Type-safe API calls with full IDE support
        users = await client.users.list_users(limit=10)
  
        # All operations are fully typed
        user = await client.users.get_user(user_id=123)
        print(f"User: {user.name}, Email: {user.email}")

asyncio.run(main())
```

## Using as a Library (Programmatic API)

The generator was designed to work both as a CLI tool and as a Python library. Programmatic usage enables integration with build systems, CI/CD pipelines, code generators, and custom tooling. You get the same powerful code generation capabilities with full Python API access.

### How to Use Programmatically

#### Basic Usage

```python
from pyopenapi_gen import generate_client

# Simple client generation
files = generate_client(
    spec_path="input/openapi.yaml",
    project_root=".",
    output_package="pyapis.my_client"
)

print(f"Generated {len(files)} files")
```

#### Advanced Usage with All Options

```python
from pyopenapi_gen import generate_client, GenerationError

try:
    files = generate_client(
        spec_path="input/openapi.yaml",
        project_root=".",
        output_package="pyapis.my_client",
        core_package="pyapis.core",  # Optional shared core
        force=True,                   # Overwrite without diff check
        no_postprocess=False,         # Run Black + mypy
        verbose=True                  # Show progress
    )

    # Process generated files
    for file_path in files:
        print(f"Generated: {file_path}")

except GenerationError as e:
    print(f"Generation failed: {e}")
```

#### Multi-Client Generation Script

```python
from pyopenapi_gen import generate_client
from pathlib import Path

# Configuration for multiple clients
clients = [
    {"spec": "api_v1.yaml", "package": "pyapis.client_v1"},
    {"spec": "api_v2.yaml", "package": "pyapis.client_v2"},
]

# Shared core package
core_package = "pyapis.core"

# Generate all clients
for client_config in clients:
    print(f"Generating {client_config['package']}...")
  
    generate_client(
        spec_path=client_config["spec"],
        project_root=".",
        output_package=client_config["package"],
        core_package=core_package,
        force=True,
        verbose=True
    )

print("All clients generated successfully!")
```

### API Reference

#### `generate_client()` Function

```python
def generate_client(
    spec_path: str,
    project_root: str,
    output_package: str,
    core_package: str | None = None,
    force: bool = False,
    no_postprocess: bool = False,
    verbose: bool = False,
) -> List[Path]
```

**Parameters**:

- `spec_path`: Path to OpenAPI spec file (YAML or JSON)
- `project_root`: Root directory of your Python project
- `output_package`: Python package name (e.g., `'pyapis.my_client'`)
- `core_package`: Optional shared core package name (defaults to `{output_package}.core`)
- `force`: Skip diff check and overwrite existing output
- `no_postprocess`: Skip Black formatting and mypy type checking
- `verbose`: Print detailed progress information

**Returns**: List of `Path` objects for all generated files

**Raises**: `GenerationError` if generation fails

#### `ClientGenerator` Class (Advanced)

For advanced use cases requiring more control:

```python
from pyopenapi_gen import ClientGenerator, GenerationError
from pathlib import Path

# Create generator with custom settings
generator = ClientGenerator(verbose=True)

# Generate with full control
try:
    files = generator.generate(
        spec_path="openapi.yaml",
        project_root=Path("."),
        output_package="pyapis.my_client",
        core_package="pyapis.core",
        force=False,
        no_postprocess=False
    )
except GenerationError as e:
    print(f"Generation failed: {e}")
```

#### `GenerationError` Exception

Raised when generation fails. Contains contextual information about the failure:

```python
from pyopenapi_gen import generate_client, GenerationError

try:
    generate_client(
        spec_path="invalid.yaml",
        project_root=".",
        output_package="test"
    )
except GenerationError as e:
    # Exception message includes context
    print(f"Error: {e}")
    # Typical causes:
    # - Invalid OpenAPI specification
    # - File I/O errors
    # - Type checking failures
    # - Invalid project structure
```

## Configuration Options

### Standalone Client (Default)

```bash
pyopenapi-gen openapi.yaml \
  --project-root . \
  --output-package my_api_client
```

Creates self-contained client with embedded core dependencies.

### Shared Core (Multiple Clients)

```bash
pyopenapi-gen openapi.yaml \
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

## Authentication

The generated clients support flexible authentication through the transport layer. Authentication plugins modify requests before they're sent.

### Bearer Token Authentication

```python
from my_api_client.core.auth.plugins import BearerAuth
from my_api_client.core.http_transport import HttpxTransport

auth = BearerAuth("your-api-token")
transport = HttpxTransport(
    base_url="https://api.example.com",
    auth=auth
)

async with APIClient(config, transport=transport) as client:
    # All requests automatically include: Authorization: Bearer your-api-token
    users = await client.users.list_users()
```

### API Key (Header, Query, or Cookie)

```python
from my_api_client.core.auth.plugins import ApiKeyAuth

# API key in header
auth = ApiKeyAuth("your-key", location="header", name="X-API-Key")

# API key in query string
auth = ApiKeyAuth("your-key", location="query", name="api_key")

# API key in cookie
auth = ApiKeyAuth("your-key", location="cookie", name="session")

transport = HttpxTransport(
    base_url="https://api.example.com",
    auth=auth
)
```

### OAuth2 with Token Refresh

```python
from my_api_client.core.auth.plugins import OAuth2Auth

async def refresh_token(current_token: str) -> str:
    # Your token refresh logic
    # Call your auth server to get a new token
    new_token = await get_new_token()
    return new_token

auth = OAuth2Auth(
    access_token="initial-token",
    refresh_callback=refresh_token
)

transport = HttpxTransport(
    base_url="https://api.example.com",
    auth=auth
)
```

### Composite Authentication (Multiple Auth Methods)

```python
from my_api_client.core.auth.base import CompositeAuth
from my_api_client.core.auth.plugins import BearerAuth, HeadersAuth

# Combine multiple authentication methods
auth = CompositeAuth(
    BearerAuth("api-token"),
    HeadersAuth({"X-Client-ID": "my-app", "X-Version": "1.0"})
)

transport = HttpxTransport(
    base_url="https://api.example.com",
    auth=auth
)

# All requests include both Authorization header and custom headers
```

### Custom Authentication

```python
from typing import Any
from my_api_client.core.auth.base import BaseAuth

class CustomAuth(BaseAuth):
    """Your custom authentication logic"""
  
    def __init__(self, api_key: str, secret: str):
        self.api_key = api_key
        self.secret = secret
  
    async def authenticate_request(self, request_args: dict[str, Any]) -> dict[str, Any]:
        # Add custom authentication logic
        headers = dict(request_args.get("headers", {}))
        headers["X-API-Key"] = self.api_key
        headers["X-Signature"] = self._generate_signature()
        request_args["headers"] = headers
        return request_args
  
    def _generate_signature(self) -> str:
        # Your signature generation logic
        return "signature"

auth = CustomAuth("key", "secret")
transport = HttpxTransport(base_url="https://api.example.com", auth=auth)
```

## Advanced Features

### Error Handling

The generated client raises structured exceptions for all non-2xx responses:

```python
from my_api_client.core.exceptions import HTTPError, ClientError, ServerError

try:
    user = await client.users.get_user(user_id=123)
    print(f"Found user: {user.name}")
  
except ClientError as e:
    # 4xx errors - client-side issues
    print(f"Client error {e.status_code}: {e.response.text}")
    if e.status_code == 404:
        print("User not found")
    elif e.status_code == 401:
        print("Authentication required")
  
except ServerError as e:
    # 5xx errors - server-side issues
    print(f"Server error {e.status_code}: {e.response.text}")
  
except HTTPError as e:
    # Catch-all for any HTTP errors
    print(f"HTTP error {e.status_code}: {e.response.text}")
```

### Streaming Responses

For operations that return streaming data (like SSE or file downloads):

```python
# Server-Sent Events (SSE)
async for event in client.events.stream_events():
    print(f"Received event: {event}")

# Binary streaming (files, large downloads)
async with client.files.download_file(file_id=123) as response:
    async for chunk in response:
        # Process binary chunks
        file.write(chunk)
```

### Automatic Field Name Mapping

Generated models use `BaseSchema` for seamless API ↔ Python field name conversion:

```python
from my_api_client.models.user import User

# API returns camelCase: {"firstName": "John", "lastName": "Doe"}
# Python uses snake_case automatically
user_data = await client.users.get_user(user_id=1)
print(user_data.first_name)  # "John" - automatically mapped
print(user_data.last_name)   # "Doe"

# Serialization back to API format works automatically
new_user = User(first_name="Jane", last_name="Smith")
created = await client.users.create_user(user=new_user)
# Sends: {"firstName": "Jane", "lastName": "Smith"}
```

### Type Safety and IDE Support

All generated code includes complete type hints:

```python
# Your IDE provides autocomplete for all methods
client.users.  # IDE shows: list_users(), get_user(), create_user(), etc.

# All parameters are typed
await client.users.create_user(
    user=User(  # IDE autocompletes User fields
        name="John",
        email="john@example.com",
        age=30  # Type checking catches wrong types
    )
)

# Return types are fully specified
user: User = await client.users.get_user(user_id=1)
# mypy validates the entire chain
```

## 💼 Common Use Cases

### Microservice Communication

```python
# Generate clients for internal services
pyopenapi-gen services/user-api/openapi.yaml \
  --project-root . \
  --output-package myapp.clients.users

pyopenapi-gen services/order-api/openapi.yaml \
  --project-root . \
  --output-package myapp.clients.orders

# Use in your application
from myapp.clients.users.client import APIClient as UserClient
from myapp.clients.orders.client import APIClient as OrderClient

async def process_order(user_id: int, order_id: int):
    async with UserClient(user_config) as user_client:
        user = await user_client.users.get_user(user_id=user_id)
  
    async with OrderClient(order_config) as order_client:
        order = await order_client.orders.get_order(order_id=order_id)
```

### SDK Generation for Public APIs

```python
# Generate a distributable SDK
pyopenapi-gen public-api.yaml \
  --project-root sdk \
  --output-package mycompany_sdk

# Package structure for distribution:
# sdk/
#   mycompany_sdk/
#     __init__.py
#     client.py
#     models/
#     endpoints/
#     core/
#   setup.py
#   README.md

# Users install: pip install mycompany-sdk
# Users use: from mycompany_sdk.client import APIClient
```

### Multi-Environment Setup

```python
# Generate once, configure per environment
from my_api_client.client import APIClient
from my_api_client.core.config import ClientConfig
from my_api_client.core.http_transport import HttpxTransport
from my_api_client.core.auth.plugins import BearerAuth

# Development
dev_config = ClientConfig(base_url="https://dev-api.example.com")
dev_auth = BearerAuth(os.getenv("DEV_API_TOKEN"))
dev_transport = HttpxTransport(dev_config.base_url, auth=dev_auth)

# Production
prod_config = ClientConfig(base_url="https://api.example.com")
prod_auth = BearerAuth(os.getenv("PROD_API_TOKEN"))
prod_transport = HttpxTransport(prod_config.base_url, auth=prod_auth)

# Use the same client code with different configs
async with APIClient(dev_config, transport=dev_transport) as client:
    users = await client.users.list_users()
```

### Testing with Mock Servers

```python
# Point generated client at mock server for testing
import pytest
from my_api_client.client import APIClient
from my_api_client.core.config import ClientConfig

@pytest.fixture
async def api_client(mock_server_url):
    """API client pointing to mock server"""
    config = ClientConfig(base_url=mock_server_url)
    async with APIClient(config) as client:
        yield client

async def test_user_creation(api_client):
    # Mock server returns predictable responses
    user = await api_client.users.create_user(
        user={"name": "Test User", "email": "test@example.com"}
    )
    assert user.name == "Test User"
```

## Testing and Mocking

### Protocol-Based Design for Strict Type Safety

The generator **automatically creates Protocol classes** for every endpoint client, enforcing strict type safety through explicit contracts. This enables easy testing with compile-time guarantees.

#### Generated Protocol Structure

For each OpenAPI tag, the generator creates:

```python
# Generated automatically from your OpenAPI spec:

@runtime_checkable
class UsersClientProtocol(Protocol):
    """Protocol defining the interface of UsersClient for dependency injection."""
  
    async def get_user(self, user_id: int) -> User: ...
    async def list_users(self, limit: int = 10) -> list[User]: ...
    async def create_user(self, user: User) -> User: ...

class UsersClient(UsersClientProtocol):
    """Real implementation - explicitly implements the protocol"""
  
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url = base_url
  
    async def get_user(self, user_id: int) -> User:
        # Real HTTP implementation
        ...
```

**Key Point**: The real implementation **explicitly inherits from the Protocol**, ensuring mypy validates it implements all methods correctly!

### Creating Type-Safe Mocks

Your mocks **must explicitly inherit from the generated Protocol** to get compile-time safety:

```python
import pytest
from my_api_client.endpoints.users import UsersClientProtocol
from my_api_client.endpoints.orders import OrdersClientProtocol
from my_api_client.models.user import User
from my_api_client.models.order import Order

class MockUsersClient(UsersClientProtocol):
    """
    Mock implementation that explicitly inherits from the generated Protocol.
  
    CRITICAL: If UsersClientProtocol changes (new method, different signature),
    mypy will immediately flag this class as incomplete.
    """
  
    def __init__(self):
        self.calls: list[tuple[str, dict]] = []  # Track method calls
        self.mock_data: dict[int, User] = {}     # Store mock responses
  
    async def get_user(self, user_id: int) -> User:
        """Mock implementation of get_user"""
        self.calls.append(("get_user", {"user_id": user_id}))
  
        # Return mock data
        if user_id in self.mock_data:
            return self.mock_data[user_id]
  
        # Return default mock user
        return User(
            id=user_id,
            name="Test User",
            email=f"user{user_id}@example.com"
        )
  
    async def list_users(self, limit: int = 10) -> list[User]:
        """Mock implementation of list_users"""
        self.calls.append(("list_users", {"limit": limit}))
        return [
            User(id=1, name="User 1", email="user1@example.com"),
            User(id=2, name="User 2", email="user2@example.com"),
        ][:limit]
  
    async def create_user(self, user: User) -> User:
        """Mock implementation of create_user"""
        self.calls.append(("create_user", {"user": user}))
        user.id = 123
        return user

class MockOrdersClient(OrdersClientProtocol):
    """Mock OrdersClient - explicitly implements the protocol"""
  
    async def get_order(self, order_id: int) -> Order:
        return Order(id=order_id, status="completed", total=99.99)
  
    async def create_order(self, order: Order) -> Order:
        order.id = 456
        order.status = "pending"
        return order

# Type checking ensures mocks match protocols at compile time!
# If you forget a method or have wrong signatures:
# mypy error: Cannot instantiate abstract class 'MockUsersClient' with abstract method 'new_method'

@pytest.fixture
def mock_users_client() -> UsersClientProtocol:
    """
    Fixture providing a mock users client.
    Return type annotation ensures type safety.
    """
    return MockUsersClient()

@pytest.fixture
def mock_orders_client() -> OrdersClientProtocol:
    """Fixture providing a mock orders client"""
    return MockOrdersClient()
```

### Using Mocked Endpoint Clients in Your Code

Now inject the mocks into your business logic:

```python
async def test_user_service_with_mocks(mock_users_client, mock_orders_client):
    """Test your business logic with mocked API clients"""
  
    # Your business logic that depends on API clients
    async def process_user_order(users_client, orders_client, user_id: int):
        user = await users_client.get_user(user_id=user_id)
        order = await orders_client.create_order(Order(user_id=user.id, items=[]))
        return user, order
  
    # Test with mocked clients
    user, order = await process_user_order(
        mock_users_client,
        mock_orders_client,
        user_id=123
    )
  
    # Assertions on business logic results
    assert user.name == "Test User"
    assert order.status == "pending"
  
    # Verify interactions with the mock
    assert len(mock_users_client.calls) == 1
    assert mock_users_client.calls[0] == ("get_user", {"user_id": 123})
```

### Dependency Injection Pattern

Structure your code to accept **Protocol types**, not concrete implementations:

```python
from my_api_client.endpoints.users import UsersClientProtocol
from my_api_client.endpoints.orders import OrdersClientProtocol

class UserService:
    """
    Service that depends on Protocol interfaces.
  
    CRITICAL: Accept Protocol types, not concrete classes!
    This allows injecting both real clients and mocks.
    """
  
    def __init__(
        self, 
        users_client: UsersClientProtocol,  # Protocol type!
        orders_client: OrdersClientProtocol  # Protocol type!
    ):
        self.users = users_client
        self.orders = orders_client
  
    async def get_user_with_orders(self, user_id: int):
        user = await self.users.get_user(user_id=user_id)
        orders = await self.orders.list_orders(user_id=user_id)
        return {"user": user, "orders": orders}

# In production: inject real clients (they implement the protocols)
from my_api_client.client import APIClient
from my_api_client.core.config import ClientConfig

config = ClientConfig(base_url="https://api.example.com")
async with APIClient(config) as client:
    service = UserService(
        users_client=client.users,    # UsersClient implements UsersClientProtocol
        orders_client=client.orders   # OrdersClient implements OrdersClientProtocol
    )
    result = await service.get_user_with_orders(user_id=123)

# In tests: inject mocks (they also implement the protocols)
async def test_user_service(mock_users_client, mock_orders_client):
    service = UserService(
        users_client=mock_users_client,    # MockUsersClient implements UsersClientProtocol
        orders_client=mock_orders_client   # MockOrdersClient implements OrdersClientProtocol
    )
  
    result = await service.get_user_with_orders(user_id=123)
  
    assert result["user"].name == "Test User"
    assert len(result["orders"]) > 0
  
    # Verify mock was called correctly
    assert ("get_user", {"user_id": 123}) in mock_users_client.calls
```

### Benefits of Generated Protocols

1. **Automatic Generation**: Protocols are generated from your OpenAPI spec - no manual writing
2. **Compile-Time Safety**: mypy catches missing/incorrect methods immediately
3. **Forced Updates**: When API changes, stale mocks break at compile time, not runtime
4. **Test at Right Level**: Mock business operations (get_user, create_order), not HTTP transport
5. **IDE Support**: Full autocomplete and inline errors for protocol implementations
6. **Refactoring Safety**: Rename operations? All implementations must update or fail type checking
7. **Documentation**: Protocol serves as explicit, enforced contract documentation
8. **No Runtime Overhead**: Protocols are pure type-checking, zero runtime cost

### Real-World Testing Example

Complete example showing protocol-based testing in action:

```python
# my_service.py
from my_api_client.endpoints.users import UsersClientProtocol
from my_api_client.models.user import User

class UserRegistrationService:
    """Business logic for user registration"""
  
    def __init__(self, users_client: UsersClientProtocol):
        self.users_client = users_client
  
    async def register_user(self, name: str, email: str) -> User:
        """Register a new user with validation"""
        # Business logic
        if not email or "@" not in email:
            raise ValueError("Invalid email")
  
        # Use API client
        user = User(name=name, email=email)
        return await self.users_client.create_user(user=user)

# test_my_service.py
import pytest
from my_service import UserRegistrationService
from my_api_client.endpoints.users import UsersClientProtocol
from my_api_client.models.user import User

class MockUsersClient(UsersClientProtocol):
    """Type-safe mock for testing"""
  
    def __init__(self):
        self.created_users: list[User] = []
  
    async def get_user(self, user_id: int) -> User:
        return User(id=user_id, name="Test", email="test@example.com")
  
    async def list_users(self, limit: int = 10) -> list[User]:
        return []
  
    async def create_user(self, user: User) -> User:
        user.id = 123  # Simulate server assigning ID
        self.created_users.append(user)
        return user

@pytest.fixture
def mock_users_client() -> UsersClientProtocol:
    return MockUsersClient()

async def test_register_user__valid_data__creates_user(mock_users_client):
    """
    When: Registering with valid data
    Then: User is created via API
    """
    service = UserRegistrationService(mock_users_client)
  
    user = await service.register_user(name="John", email="john@example.com")
  
    assert user.id == 123
    assert user.name == "John"
    assert len(mock_users_client.created_users) == 1

async def test_register_user__invalid_email__raises_error(mock_users_client):
    """
    When: Registering with invalid email
    Then: ValueError is raised
    """
    service = UserRegistrationService(mock_users_client)
  
    with pytest.raises(ValueError, match="Invalid email"):
        await service.register_user(name="John", email="invalid")

# If UsersClientProtocol changes (e.g., create_user signature changes):
# mypy error: Cannot instantiate abstract class 'MockUsersClient' with abstract method 'create_user'
# This forces you to update your mock, keeping tests in sync with API!
```

### Auto-Generated Mock Helper Classes

The generator creates ready-to-use mock helper classes in the `mocks/` directory, providing a faster path to testable code.

#### Generated Mocks Structure

```
my_api_client/
├── mocks/
│   ├── __init__.py           # Exports MockAPIClient and all endpoint mocks
│   ├── mock_client.py        # MockAPIClient with auto-create pattern
│   └── endpoints/
│       ├── __init__.py       # Exports MockUsersClient, MockOrdersClient, etc.
│       ├── mock_users.py     # MockUsersClient helper
│       └── mock_orders.py    # MockOrdersClient helper
```

#### Quick Start with Auto-Generated Mocks

Instead of manually creating mock classes, inherit from the generated helpers:

```python
from my_api_client.mocks import MockAPIClient, MockUsersClient
from my_api_client.models.user import User

# Option 1: Override specific methods
class TestUsersClient(MockUsersClient):
    """Inherit from generated mock, override only what you need"""

    async def get_user(self, user_id: int) -> User:
        return User(id=user_id, name="Test User", email="test@example.com")

    # list_users and create_user will raise NotImplementedError with helpful messages

# Option 2: Use MockAPIClient with hybrid auto-create pattern
client = MockAPIClient(users=TestUsersClient())

# Access your custom mock
user = await client.users.get_user(user_id=123)
assert user.name == "Test User"

# Other endpoints auto-created with NotImplementedError stubs
# await client.orders.get_order(order_id=1)  # Raises: NotImplementedError: Override MockOrdersClient.get_order()
```

#### Hybrid Auto-Create Pattern

`MockAPIClient` automatically creates mock instances for all endpoint clients you don't explicitly provide:

```python
from my_api_client.mocks import MockAPIClient, MockUsersClient, MockOrdersClient
from my_api_client.models.user import User
from my_api_client.models.order import Order

# Override only the clients you need for this test
class TestUsersClient(MockUsersClient):
    async def get_user(self, user_id: int) -> User:
        return User(id=user_id, name="Test User", email="test@example.com")

class TestOrdersClient(MockOrdersClient):
    async def get_order(self, order_id: int) -> Order:
        return Order(id=order_id, status="completed", total=99.99)

# Create client with partial overrides
client = MockAPIClient(
    users=TestUsersClient(),
    orders=TestOrdersClient()
    # products, payments, etc. auto-created with NotImplementedError stubs
)

# Use your custom mocks
user = await client.users.get_user(user_id=123)
order = await client.orders.get_order(order_id=456)

# Unimplemented endpoints provide clear error messages
# await client.products.list_products()  # NotImplementedError: Override MockProductsClient.list_products()
```

#### NotImplementedError Guidance

Generated mock helpers raise `NotImplementedError` with helpful messages:

```python
from my_api_client.mocks import MockUsersClient

mock = MockUsersClient()

# Attempting to call unimplemented method:
await mock.get_user(user_id=123)
# NotImplementedError: MockUsersClient.get_user() not implemented.
# Override this method in your test:
#     class TestUsersClient(MockUsersClient):
#         async def get_user(self, user_id: int) -> User:
#             return User(...)
```

#### Comparison: Manual vs Auto-Generated

**Manual Protocol Implementation** (always available):
```python
from my_api_client.endpoints.users import UsersClientProtocol

class MockUsersClient(UsersClientProtocol):
    """Full control, implement all methods"""

    async def get_user(self, user_id: int) -> User: ...
    async def list_users(self, limit: int = 10) -> list[User]: ...
    async def create_user(self, user: User) -> User: ...
```

**Auto-Generated Helper** (faster, less boilerplate):
```python
from my_api_client.mocks import MockUsersClient

class TestUsersClient(MockUsersClient):
    """Override only what you need"""

    async def get_user(self, user_id: int) -> User:
        return User(id=user_id, name="Test User", email="test@example.com")

    # Other methods inherited with NotImplementedError stubs
```

**Use auto-generated mocks when**:
- You want to quickly get started with testing
- You only need to override specific methods
- You prefer helpful NotImplementedError messages over abstract method errors

**Use manual Protocol implementation when**:
- You need complete control over all mock behavior
- You're building reusable test fixtures
- You want explicit tracking of all method calls

Both approaches are type-safe and provide compile-time validation!

## Known Limitations

Some OpenAPI features have simplified implementations:

| Feature                           | Current Behavior                                        | Workaround                                         |
| --------------------------------- | ------------------------------------------------------- | -------------------------------------------------- |
| **Parameter Serialization**       | Uses httpx defaults (not OpenAPI `style`/`explode`)     | Manually format complex parameters                 |
| **Response Headers**              | Only body is returned, headers are ignored              | Use custom transport to access full response       |
| **Multipart Forms**               | Basic file upload only                                  | Complex multipart schemas may need manual handling |
| **Parameter Defaults**            | Schema defaults not in method signatures                | Pass defaults explicitly when calling              |
| **WebSockets**                    | Not currently supported                                 | Use separate WebSocket library                     |

> 💡 These limitations rarely affect real-world usage. Most APIs work perfectly with the current implementation.

## Architecture

PyOpenAPI Generator uses a sophisticated three-stage pipeline designed for enterprise-grade reliability:

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
  
    subgraph "Key Components"
        K[Schema Parser]
        L[Cycle Detection]
        M[Reference Resolution]
        N[Type Service]
        O[Code Emitters]
    end
```

### Why This Architecture?

**Complex Schema Handling**: Modern OpenAPI specs contain circular references, deep nesting, and intricate type relationships. Our architecture handles these robustly.

**Production Ready**: Each stage has clear responsibilities and clean interfaces, enabling comprehensive testing and reliable code generation.

**Extensible**: Plugin-based authentication, customizable type resolution, and modular emitters make the system adaptable to various use cases.

## 📚 Documentation

- **[Architecture Guide](docs/architecture.md)** - Deep dive into the system design
- **[Type Resolution](docs/unified_type_resolution.md)** - How types are resolved and generated
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project
- **[API Reference](docs/)** - Complete API documentation

## 🤝 Contributing

We welcome contributions! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

**For Contributors**: See our [Contributing Guide](CONTRIBUTING.md) for:

- Development setup and workflow
- Testing requirements (85% coverage, mypy strict mode)
- Code quality standards
- Pull request process

**Quick Links**:

- [Architecture Documentation](docs/architecture.md) - System design and patterns
- [Issue Tracker](https://github.com/mindhiveoy/pyopenapi_gen/issues) - Report bugs or request features

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

Generated clients are self-contained and can be distributed under any license compatible with your project.
