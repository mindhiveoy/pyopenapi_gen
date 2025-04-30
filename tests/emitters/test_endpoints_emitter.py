from pathlib import Path

from pyopenapi_gen import (
    HTTPMethod,
    IROperation,
    IRParameter,
    IRRequestBody,
    IRResponse,
    IRSchema,
    IRSpec,
)
from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter


def test_endpoints_emitter_basic(tmp_path: Path) -> None:
    """Test the basic functionality of the EndpointsEmitter.

    Scenario:
        - Create an IRSpec with operations organized by tags
        - Use the emitter to generate endpoint modules

    Expected outcome:
        - A module should be created for each tag
        - Each module should contain appropriate endpoint methods
    """
    # Create sample operations with tags
    operations = [
        IROperation(
            operation_id="list_pets",
            method=HTTPMethod.GET,
            path="/pets",
            summary="List all pets",
            description="Returns all pets from the system",
            tags=["pets"],
        ),
        IROperation(
            operation_id="create_pet",
            method=HTTPMethod.POST,
            path="/pets",
            summary="Create a pet",
            description="Creates a new pet in the store",
            tags=["pets"],
        ),
        IROperation(
            operation_id="list_users",
            method=HTTPMethod.GET,
            path="/users",
            summary="List all users",
            description="Returns all users",
            tags=["users"],
        ),
    ]

    spec = IRSpec(
        title="Test API",
        version="1.0.0",
        operations=operations,
        schemas={},
        servers=["https://api.example.com"],
    )

    out_dir: Path = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))

    # Check that files were created for each tag
    pets_file: Path = out_dir / "endpoints" / "pets.py"
    users_file: Path = out_dir / "endpoints" / "users.py"

    assert pets_file.exists()
    assert users_file.exists()

    # Check content of pets file
    pets_content = pets_file.read_text()
    assert "class PetsClient:" in pets_content
    assert "async def list_pets" in pets_content
    assert "async def create_pet" in pets_content

    # Check content of users file
    users_content = users_file.read_text()
    assert "class UsersClient:" in users_content
    assert "async def list_users" in users_content


def test_endpoints_emitter_json_body(tmp_path: Path) -> None:
    """Test JSON body parameter support in EndpointsEmitter."""
    # Define a JSON schema for the request body
    schema = IRSchema(name=None, type="object")
    request_body = IRRequestBody(required=True, content={"application/json": schema})
    op = IROperation(
        operation_id="create_pet_with_body",
        method=HTTPMethod.POST,
        path="/pets",
        summary="Create a pet with JSON body",
        description="Creates a new pet",
        parameters=[],
        request_body=request_body,
        responses=[],
        tags=["pets"],
    )
    spec = IRSpec(
        title="Test API",
        version="1.0",
        operations=[op],
        schemas={},
        servers=["https://example.com"],
    )

    out_dir: Path = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))

    pets_file: Path = out_dir / "endpoints" / "pets.py"
    assert pets_file.exists()
    content = pets_file.read_text()
    # The method should include a body parameter and json=body in the request
    assert "body:" in content
    assert "json_body: Dict[str, Any] = body" in content


def test_endpoints_emitter_multipart(tmp_path: Path) -> None:
    """Test multipart/form-data file upload support in EndpointsEmitter."""
    # Define a simple schema for multipart/form-data (file upload)
    schema = IRSchema(name=None, type="string")
    request_body = IRRequestBody(required=True, content={"multipart/form-data": schema})
    op = IROperation(
        operation_id="upload_file",
        method=HTTPMethod.POST,
        path="/upload",
        summary="Upload a file",
        description="Uploads a file using multipart/form-data",
        parameters=[],
        request_body=request_body,
        responses=[],
        tags=["files"],
    )
    spec = IRSpec(
        title="Test API",
        version="1.0",
        operations=[op],
        schemas={},
        servers=["https://example.com"],
    )

    out_dir: Path = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))

    file_module: Path = out_dir / "endpoints" / "files.py"
    assert file_module.exists()
    content = file_module.read_text()
    # The method signature should include 'files: Dict[str, IO[Any]]'
    assert "files: Dict[str, IO[Any]]" in content
    # And the request should pass files via kwargs
    assert "files_data: Dict[str, IO[Any]] = files" in content


def test_endpoints_emitter_streaming(tmp_path: Path) -> None:
    """Test that streaming (binary) responses generate async iterators."""
    # Create a streaming response IR
    streaming_resp = IRResponse(
        status_code="200",
        description="Stream bytes",
        content={"application/octet-stream": IRSchema(name=None, type="string", format="binary")},
        stream=True,
    )
    op = IROperation(
        operation_id="download_stream",
        method=HTTPMethod.GET,
        path="/stream",
        summary="Stream download",
        description="Streams data",
        parameters=[],
        request_body=None,
        responses=[streaming_resp],
        tags=["stream"],
    )
    spec = IRSpec(
        title="Test API",
        version="1.0",
        operations=[op],
        schemas={},
        servers=["https://example.com"],
    )

    out_dir: Path = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))

    stream_file: Path = out_dir / "endpoints" / "stream.py"
    assert stream_file.exists()
    content = stream_file.read_text()
    # The return type should be AsyncIterator[bytes]
    assert "AsyncIterator[bytes]" in content
    # Should yield chunks from resp.aiter_bytes()
    assert "async for chunk in iter_bytes(response):" in content


def test_endpoints_emitter_imports(tmp_path: Path) -> None:
    """Test that the endpoint module has the correct import statements."""
    from pyopenapi_gen import (
        HTTPMethod,
        IROperation,
        IRRequestBody,
        IRResponse,
        IRSchema,
        IRSpec,
    )

    # Prepare IR pieces: path param, query param, JSON body, streaming response
    schema = IRSchema(name=None, type="string")
    rb = IRRequestBody(
        required=True,
        content={"application/json": schema, "multipart/form-data": schema},
    )
    resp = IRResponse(
        status_code="200",
        description="Stream or JSON",
        content={"application/json": schema, "application/octet-stream": schema},
        stream=True,
    )
    op = IROperation(
        operation_id="combined_op",
        method=HTTPMethod.POST,
        path="/items/{item_id}",
        summary="Combined operation",
        description=None,
        parameters=[
            IRParameter(name="item_id", in_="path", required=True, schema=schema),
            IRParameter(name="q", in_="query", required=False, schema=schema),
        ],
        request_body=rb,
        responses=[resp],
        tags=["combined"],
    )
    spec = IRSpec(
        title="Test API",
        version="1.0",
        operations=[op],
        schemas={},
        servers=["https://api.test"],
    )

    out_dir = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))

    mod = out_dir / "endpoints" / "combined.py"
    assert mod.exists()
    content = mod.read_text()
    # Accept any superset of the expected import line
    assert "from typing import Any" in content
    assert "AsyncIterator" in content
    assert "Dict" in content
    assert "IO" in content
    assert "Optional" in content


def create_simple_response_schema() -> IRSchema:
    # Helper to create a basic IRSchema for response bodies
    return IRSchema(name=None, type="object", format=None)


def create_simple_param_schema() -> IRSchema:
    # Helper to create a basic IRSchema for parameter schemas
    return IRSchema(name=None, type="string", format=None)


def test_endpoints_emitter__sanitize_tag_name__creates_sanitized_module_and_class(
    tmp_path: Path,
) -> None:
    """
    Scenario:
        Emit endpoints for a spec with a tag that contains spaces and special chars.
    Expected Outcome:
        A module file with a sanitized filename and a client class with a sanitized name
        is created.
    """
    # Arrange
    tag = "My Tag!"
    op = IROperation(
        operation_id="get_item",
        method=HTTPMethod.GET,
        path="/items/{itemId}",
        summary="Get item",
        description=None,
        parameters=[
            IRParameter(
                name="itemId",
                in_="path",
                required=True,
                schema=create_simple_param_schema(),
            )
        ],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="OK",
                content={"application/json": create_simple_response_schema()},
                stream=False,
            )
        ],
        tags=[tag],
    )
    spec = IRSpec(title="Test API", version="1.0.0", schemas={}, operations=[op])
    out_dir = tmp_path / "out"

    # Act
    EndpointsEmitter().emit(spec, str(out_dir))

    # Assert
    endpoints_dir = out_dir / "endpoints"
    # Sanitized filename should be 'my_tag.py'
    module_file = endpoints_dir / "my_tag.py"
    assert module_file.exists(), f"Expected module file {module_file} to exist"
    content = module_file.read_text()
    # Sanitized class name should be 'MyTagClient'
    assert "class MyTagClient" in content, "Client class name not sanitized correctly"


def test_endpoints_emitter__multiple_operations_same_tag__includes_all_methods(
    tmp_path: Path,
) -> None:
    """
    Scenario:
        Emit endpoints for a spec with multiple operations under the same tag.
    Expected Outcome:
        The generated client module contains all corresponding async method definitions.
    """
    # Arrange
    tag = "items"
    op1 = IROperation(
        operation_id="list_items",
        method=HTTPMethod.GET,
        path="/items",
        summary="List items",
        description=None,
        parameters=[],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="OK",
                content={"application/json": create_simple_response_schema()},
                stream=False,
            )
        ],
        tags=[tag],
    )
    op2 = IROperation(
        operation_id="get_item",
        method=HTTPMethod.GET,
        path="/items/{itemId}",
        summary="Get item",
        description=None,
        parameters=[
            IRParameter(
                name="itemId",
                in_="path",
                required=True,
                schema=create_simple_param_schema(),
            )
        ],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="OK",
                content={"application/json": create_simple_response_schema()},
                stream=False,
            )
        ],
        tags=[tag],
    )
    spec = IRSpec(title="Test API", version="1.0.0", schemas={}, operations=[op1, op2])
    out_dir = tmp_path / "out"

    # Act
    EndpointsEmitter().emit(spec, str(out_dir))

    # Assert
    endpoints_dir = out_dir / "endpoints"
    module_file = endpoints_dir / "items.py"
    assert module_file.exists(), "Expected items.py to exist"
    content = module_file.read_text()
    # Method definitions should include both list_items and get_item
    assert "async def list_items" in content, "list_items method missing"
    assert "async def get_item" in content, "get_item method missing"


def test_endpoints_emitter__init_file_contains_correct_import(tmp_path: Path) -> None:
    """
    Scenario:
        Emit endpoints for a spec and inspect the __init__.py file.
    Expected Outcome:
        The __init__.py contains correct __all__ entry and import statement for the
        sanitized client module.
    """
    # Arrange
    tag = "Test Tag"
    op = IROperation(
        operation_id="do_something",
        method=HTTPMethod.POST,
        path="/do",
        summary="Do something",
        description=None,
        parameters=[],
        request_body=IRRequestBody(required=False, content={}, description=None),
        responses=[
            IRResponse(
                status_code="200",
                description="OK",
                content={"application/json": create_simple_response_schema()},
                stream=False,
            )
        ],
        tags=[tag],
    )
    spec = IRSpec(title="Test API", version="1.0.0", schemas={}, operations=[op])
    out_dir = tmp_path / "out"

    # Act
    EndpointsEmitter().emit(spec, str(out_dir))

    # Assert
    init_file = out_dir / "endpoints" / "__init__.py"
    assert init_file.exists(), "__init__.py not generated in endpoints/"
    text = init_file.read_text()
    sanitized = "TestTagClient"
    module_name = "test_tag"
    # __all__ should include the sanitized client name
    assert f'"{sanitized}"' in text, "__all__ missing sanitized client name"
    # Should import from the sanitized module
    assert f"from .{module_name} import {sanitized}" in text, "Import statement missing or incorrect"


def test_endpoints_emitter__tag_deduplication__single_client_and_import(tmp_path: Path) -> None:
    """
    Scenario:
        Emit endpoints for a spec with multiple operations using tags that differ only
        by case or punctuation.
    Expected Outcome:
        Only one client module/class is generated for all tag variants.
        __init__.py contains only one entry in __all__ and one import statement for the
        deduplicated client.
    """
    # Arrange
    tag_variants = [
        "DataSources",
        "datasources",
        "data-sources",
        "DATA_SOURCES",
        "Data Sources",
    ]
    operations = []
    for i, tag in enumerate(tag_variants):
        operations.append(
            IROperation(
                operation_id=f"op_{i}",
                method=HTTPMethod.GET,
                path=f"/datasources/{i}",
                summary=f"Operation {i}",
                description=None,
                parameters=[],
                request_body=None,
                responses=[
                    IRResponse(
                        status_code="200",
                        description="OK",
                        content={"application/json": IRSchema(name=None, type="object")},
                        stream=False,
                    )
                ],
                tags=[tag],
            )
        )
    spec = IRSpec(title="Test API", version="1.0.0", schemas={}, operations=operations)
    out_dir = tmp_path / "out"

    # Act
    EndpointsEmitter().emit(spec, str(out_dir))

    # Assert
    endpoints_dir = out_dir / "endpoints"
    # Only one module file should exist for all tag variants
    expected_module = endpoints_dir / "data_sources.py"
    assert expected_module.exists(), "Expected data_sources.py to exist for deduplicated tags"
    content = expected_module.read_text()
    # The client class should be present (canonicalized, PascalCase)
    assert "class DataSourcesClient" in content, "Client class name not as expected"
    # __init__.py should only have one entry in __all__ and one import, using PascalCase
    #  for public API
    init_file = endpoints_dir / "__init__.py"
    assert init_file.exists(), "__init__.py not generated in endpoints/"
    text = init_file.read_text()
    # __all__ should reference DataSourcesClient (PascalCase)
    assert '"DataSourcesClient"' in text, "__all__ should reference DataSourcesClient"
    # Only one import from data_sources module should exist, importing DataSourcesClient
    assert (
        text.count("from .data_sources import DataSourcesClient") == 1
    ), "Only one import from data_sources module should exist"


def test_endpoints_emitter__streaming_inline_object_schema__yields_model(tmp_path: Path) -> None:
    """
    Scenario:
        Generate an endpoint for a streaming (event-stream) response where the schema is
        an inline object (not a named model). This matches the /listen endpoint in the
        business_swagger.json spec.

    Expected Outcome:
        - The generated method has return type AsyncIterator[Dict[str, Any]]
        - The method yields json.loads(chunk)
        - The file does NOT import or reference ListenEventsResponse
    """
    from pyopenapi_gen import (
        HTTPMethod,
        IROperation,
        IRParameter,
        IRResponse,
        IRSchema,
        IRSpec,
    )
    from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter

    # Inline object schema for event-stream
    event_schema = IRSchema(
        name=None,
        type="object",
        properties={
            "data": IRSchema(name=None, type="object"),
            "event": IRSchema(name=None, type="string"),
            "id": IRSchema(name=None, type="string"),
        },
        required=["data", "event", "id"],
    )
    streaming_resp = IRResponse(
        status_code="200",
        description="Server-Sent Events stream established",
        content={"text/event-stream": event_schema},
        stream=True,
        stream_format="event-stream",
    )
    op = IROperation(
        operation_id="listen_events",
        method=HTTPMethod.GET,
        path="/listen",
        summary="Establish a Server-Sent Events connection",
        description="Establishes a Server-Sent Events connection with optional filters.",
        parameters=[
            IRParameter(
                name="filters",
                in_="query",
                required=True,
                schema=IRSchema(name=None, type="object"),
                description="JSON object defining filters for the events",
            )
        ],
        request_body=None,
        responses=[streaming_resp],
        tags=["listen"],
    )
    spec = IRSpec(
        title="Test API",
        version="1.0.0",
        operations=[op],
        schemas={},
        servers=["https://api.example.com"],
    )
    out_dir = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))
    listen_file = out_dir / "endpoints" / "listen.py"
    assert listen_file.exists()
    content = listen_file.read_text()
    # The return type should be AsyncIterator[Dict[str, Any]]
    assert "AsyncIterator[Dict[str, Any]]" in content
    # Should yield json.loads(chunk)
    assert "json.loads(chunk)" in content
    # Should NOT import or reference ListenEventsResponse
    assert "ListenEventsResponse" not in content
    assert "from ..models" not in content or "ListenEventsResponse" not in content


def test_endpoints_emitter__streaming_inline_object_schema_not_in_schemas__yields_dict(
    tmp_path: Path,
) -> None:
    """
    Scenario:
        Generate an endpoint for a streaming (event-stream) response where the schema is an inline object (not a named
        model and not present in IRSpec.schemas). This matches the /listen endpoint in the business_swagger.json spec,
        but the schema is not registered as a model.

    Expected Outcome:
        - The generated method has return type AsyncIterator[Dict[str, Any]]
        - The method yields json.loads(chunk) (not a fabricated model class)
        - No import or reference to a fabricated model class is present
    """

    from pyopenapi_gen import (
        HTTPMethod,
        IROperation,
        IRResponse,
        IRSchema,
        IRSpec,
    )
    from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter

    # Inline schema (not in IRSpec.schemas)
    inline_schema = IRSchema(
        name=None,  # No name, not a model
        type="object",
        properties={"foo": IRSchema(name=None, type="string")},
        required=["foo"],
    )
    op = IROperation(
        path="/listen",
        method=HTTPMethod.GET,
        operation_id="listenEvents",
        parameters=[],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="stream",
                content={"text/event-stream": inline_schema},
                stream=True,
            )
        ],
        tags=["Listen"],
        summary="Listen SSE",
        description="",
    )
    spec = IRSpec(
        title="Test API",
        version="1.0.0",
        schemas={},  # No schemas registered
        operations=[op],
        servers=[],
    )
    out_dir = tmp_path / "out"
    emitter = EndpointsEmitter()
    emitter.emit(spec, str(out_dir))
    listen_file = out_dir / "endpoints" / "listen.py"
    assert listen_file.exists(), "listen.py not generated"
    content = listen_file.read_text()
    # Should use AsyncIterator[Dict[str, Any]]
    assert "AsyncIterator[Dict[str, Any]]" in content
    # Should yield json.loads(chunk)
    assert "json.loads(chunk)" in content
    # Should NOT import or reference a fabricated model class
    assert "ListenEventsResponse" not in content
    assert "from ..models" not in content or "ListenEventsResponse" not in content


def test_endpoints_emitter__query_params_included_in_params_dict(tmp_path: Path) -> None:
    """
    Scenario:
        Generate an endpoint with multiple query parameters.
    Expected Outcome:
        - All query parameters in the method signature are included in the params dictionary in the generated code.
    """
    import os

    from pyopenapi_gen import (
        HTTPMethod,
        IROperation,
        IRParameter,
        IRResponse,
        IRSchema,
        IRSpec,
    )
    from pyopenapi_gen.emitters.endpoints_emitter import EndpointsEmitter

    # Simulate an endpoint with query parameters
    op = IROperation(
        path="/tenants/{tenant_id}/analytics/chat-stats",
        method=HTTPMethod.GET,
        operation_id="getTenantChatStats",
        parameters=[
            IRParameter(
                name="tenant_id",
                in_="path",
                required=True,
                schema=IRSchema(name=None, type="string"),
            ),
            IRParameter(
                name="start_date",
                in_="query",
                required=False,
                schema=IRSchema(name=None, type="string"),
            ),
            IRParameter(
                name="end_date",
                in_="query",
                required=False,
                schema=IRSchema(name=None, type="string"),
            ),
        ],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="OK",
                content={"application/json": IRSchema(name=None, type="object")},
                stream=False,
            )
        ],
        tags=["Tenants"],
        summary="Get chat statistics for a tenant",
        description="",
    )
    spec = IRSpec(title="Test API", version="1.0.0", operations=[op], schemas={})
    out_dir = tmp_path / "out"
    emitter = EndpointsEmitter(spec.schemas)
    emitter.emit(spec, str(out_dir))
    # Read the generated code
    with open(os.path.join(out_dir, "endpoints", "tenants.py")) as f:
        content = f.read()
    # Assert that all query params are included in the params dict
    assert '"start_date": start_date' in content
    assert '"end_date": end_date' in content
    # Also check that tenant_id is not in params (it's a path param)
    assert '"tenant_id": tenant_id' not in content


def test_endpoints_emitter__post_with_body__only_body_param_and_path_query_args(tmp_path: Path) -> None:
    """
    Scenario:
        - A POST endpoint has path params and a JSON request body with multiple fields.
        - The code generator should only include path/query params and a single 'body' argument in the method signature.
        - The body fields should NOT appear as top-level method arguments.

    Expected Outcome:
        - The generated method signature contains only path/query params and 'body', not the body fields.
    """
    # Arrange: Create IR for a POST endpoint with path params and a JSON body
    from pyopenapi_gen import HTTPMethod, IROperation, IRParameter, IRRequestBody, IRSchema, IRSpec

    path_param = IRParameter(name="tenant_id", in_="path", required=True, schema=IRSchema(name=None, type="string"))
    body_schema = IRSchema(
        name="ElaborateSearchPhraseRequest",
        type="object",
        properties={
            "searchPhrase": IRSchema(name=None, type="string"),
            "instructions": IRSchema(name=None, type="string"),
        },
        required=["searchPhrase", "instructions"],
    )
    request_body = IRRequestBody(required=True, content={"application/json": body_schema})
    op = IROperation(
        operation_id="elaborate_search_phrase",
        method=HTTPMethod.POST,
        path="/tenants/{tenant_id}/search",
        summary="Elaborate search phrase",
        description="Elaborates a search phrase.",
        parameters=[path_param],
        request_body=request_body,
        responses=[],
        tags=["search"],
    )
    spec = IRSpec(
        title="Test API",
        version="1.0.0",
        operations=[op],
        schemas={"ElaborateSearchPhraseRequest": body_schema},
        servers=["https://api.example.com"],
    )
    out_dir: Path = tmp_path / "out"
    emitter = EndpointsEmitter()

    # Act: Generate the endpoints
    emitter.emit(spec, str(out_dir))
    search_file: Path = out_dir / "endpoints" / "search.py"
    assert search_file.exists()
    content = search_file.read_text()

    # Assert: The method signature should have only tenant_id and body, not searchPhrase/instructions
    # Accept multiline signature (indented)
    assert "async def elaborate_search_phrase(" in content
    assert "tenant_id: str," in content
    assert "body: ElaborateSearchPhraseRequest," in content
    # Ensure body fields are NOT present as top-level args
    assert "searchPhrase:" not in content
    assert "instructions:" not in content
