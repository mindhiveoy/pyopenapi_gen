# Endpoint Visitor (`visit/endpoint/endpoint_visitor.py`)

## Why This Visitor?

APIs consist of multiple operations grouped by tags (e.g., "Users", "Orders"). The EndpointVisitor transforms these operations into type-safe Python code, creating both the implementation and structural contracts (Protocols) needed for testability.

## What It Does

The EndpointVisitor translates `IROperation` nodes from the Intermediate Representation into three key outputs:
1. **Implementation Classes**: Concrete async methods for API operations
2. **Protocol Definitions**: Structural type contracts with `@runtime_checkable` decorators
3. **Mock Helper Classes**: Pre-built test doubles with NotImplementedError stubs

## How It Works

### Core Responsibilities

#### 1. Method Generation
- Generates async Python methods for each API operation
- Parses `IROperation` details (path, method, parameters, request body, responses)
- Constructs method signatures with proper type hints
- Handles request construction and response processing
- Supports response unwrapping (e.g., extracting `.data` fields)

#### 2. Protocol Generation
Generates `@runtime_checkable` Protocol classes for dependency injection:

```python
@runtime_checkable
class UsersClientProtocol(Protocol):
    """Protocol defining the interface of UsersClient for dependency injection."""

    async def get_user(self, user_id: int) -> User: ...
    async def list_users(self, limit: int = 10) -> list[User]: ...
```

**Key Features**:
- Extracts method signatures from generated implementation code
- Handles `@overload` decorated methods (multiple content types)
- Converts async generators to `def` signatures (AsyncIterator returns)
- Provides structural typing for compile-time validation

#### 3. Mock Helper Generation
Creates mock classes with NotImplementedError stubs:

```python
class MockUsersClient:
    """Mock implementation of UsersClient for testing."""

    async def get_user(self, user_id: int) -> User:
        raise NotImplementedError(
            "MockUsersClient.get_user() not implemented.\n"
            "Override this method in your test:\n"
            "    class TestUsersClient(MockUsersClient):\n"
            "        async def get_user(self, user_id: int) -> User:\n"
            "            return User(...)"
        )
```

**Key Features**:
- Generates helpful error messages guiding developers
- Provides base classes for test inheritance
- Maintains type compatibility with Protocol contracts

### Key Methods

#### `visit_IROperation()`
Generates a complete async method for an API operation by delegating to `EndpointMethodGenerator`.

#### `emit_endpoint_client_class()`
Combines Protocol and implementation into a complete endpoint client class:
- Generates Protocol definition if operations provided
- Creates implementation class that inherits from Protocol
- Ensures mypy validates implementation correctness

#### `generate_endpoint_protocol()`
Creates Protocol definition from operations:
- Extracts method signatures from generated code
- Handles `@overload` decorated methods
- Converts AsyncIterator methods to non-async signatures
- Formats multi-line signatures for readability

#### `generate_endpoint_mock_class()`
Creates mock helper class for testing:
- Generates NotImplementedError stubs for all methods
- Includes helpful error messages with override examples
- Supports inheritance-based test customization

### Type Resolution Integration

Uses `UnifiedTypeService` for all type conversions:
- Parameter types from `IRParameter` schemas
- Return types from `IRResponse` schemas
- Request body types from `IRRequestBody` schemas

### Code Generation Pattern

```python
# 1. Visit operation → generate method code
method_code = endpoint_visitor.visit_IROperation(operation, context)

# 2. Generate Protocol → structural contract
protocol_code = endpoint_visitor.generate_endpoint_protocol(tag, operations, context)

# 3. Generate implementation → concrete class
impl_code = endpoint_visitor.emit_endpoint_client_class(tag, method_codes, context, operations)

# 4. Generate mock helper → test double
mock_code = endpoint_visitor.generate_endpoint_mock_class(tag, operations, context)
```

## Supporting Components

- **`EndpointMethodGenerator`**: Handles individual method generation
- **`MockGenerator`**: Generates mock method stubs with NotImplementedError
- **`ProtocolGenerator`**: Creates Protocol helper methods (from `visit/protocol_helpers.py`)
- **`CodeWriter`**: Code formatting and indentation utilities

## Generated Structure

For each OpenAPI tag (e.g., "Users"), the EndpointVisitor generates:

```python
# Protocol definition
@runtime_checkable
class UsersClientProtocol(Protocol):
    async def get_user(self, user_id: int) -> User: ...
    async def create_user(self, user: User) -> User: ...

# Implementation
class UsersClient(UsersClientProtocol):
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url = base_url

    async def get_user(self, user_id: int) -> User:
        # Full implementation with HTTP calls
        ...

    async def create_user(self, user: User) -> User:
        # Full implementation with HTTP calls
        ...

# Mock helper
class MockUsersClient:
    async def get_user(self, user_id: int) -> User:
        raise NotImplementedError("Override in your test")

    async def create_user(self, user: User) -> User:
        raise NotImplementedError("Override in your test")
```

## Testing Benefits

The three-layer approach (Protocol + Implementation + Mock) enables:
1. **Compile-Time Safety**: Protocol violations caught by mypy
2. **Easy Testing**: Inherit from mock helpers, override what you need
3. **Dependency Injection**: Accept Protocol types in business logic
4. **Refactoring Safety**: API changes break tests at compile time 