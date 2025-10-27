"""
Tests for the ClientVisitor which generates the main API client class.
"""

import re

from pyopenapi_gen import IROperation, IRSpec
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod  # Import for method type
from pyopenapi_gen.visit.client_visitor import ClientVisitor


class TestClientVisitor:
    """Tests for the ClientVisitor class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.visitor = ClientVisitor()
        # Initialize with proper paths to resolve imports correctly
        self.context = RenderContext(
            core_package_name="test_app.core",
            package_root_for_generated_code="/tmp/test_app",
            overall_project_root="/tmp",
        )
        # Set a current file to collect imports properly
        self.context.set_current_file("/tmp/test_app/client.py")

    def test_visit__generates_api_client_class(self) -> None:
        """
        Scenario:
            Generate a client class with no operations
        Expected Outcome:
            A valid Python class is generated with required imports
        """
        # Create a minimal IRSpec with no operations
        spec = IRSpec(title="Test API", version="1.0.0", description="Test API description", operations=[])

        # Set a current file to collect imports properly
        self.context.set_current_file("/tmp/test_app/client.py")

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Verify Protocol structure
        assert "class APIClientProtocol(Protocol):" in result
        assert "@runtime_checkable" in result

        # Verify implementation class structure
        assert "class APIClient(APIClientProtocol):" in result
        assert "__init__" in result
        assert "self.config = config" in result
        assert "self.transport = transport" in result
        assert "async def close(self)" in result
        assert "async def __aenter__" in result
        assert "async def __aexit__" in result

        # Set a current file to collect imports properly
        self.context.set_current_file("/tmp/test_app/client.py")

        # Verify imports are added correctly
        # We'll just check that required classes are present in the generated code
        assert "HttpTransport" in result
        assert "ClientConfig" in result

    def test_visit__generates_properties_for_all_tags(self) -> None:
        """
        Scenario:
            Generate a client class with operations having different tags
        Expected Outcome:
            A property is generated for each unique tag
        """
        # Create operations with different tags
        operations = [
            IROperation(
                operation_id="getUserById",
                path="/users/{id}",
                method=HTTPMethod.GET,
                summary="Get a user by ID",
                description="Get a user by ID",
                tags=["Users"],
                parameters=[],
                request_body=None,
                responses=[],
            ),
            IROperation(
                operation_id="createOrder",
                path="/orders",
                method=HTTPMethod.POST,
                summary="Create a new order",
                description="Create a new order",
                tags=["Orders"],
                parameters=[],
                request_body=None,
                responses=[],
            ),
            IROperation(
                operation_id="getProducts",
                path="/products",
                method=HTTPMethod.GET,
                summary="List all products",
                description="List all products",
                tags=["Products"],
                parameters=[],
                request_body=None,
                responses=[],
            ),
        ]

        # Create a spec with these operations
        spec = IRSpec(title="Test API", version="1.0.0", description="Test API description", operations=operations)

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Verify property method for each tag
        assert "def users(self)" in result
        assert "def orders(self)" in result
        assert "def products(self)" in result

        # Verify lazy initialization for each client
        assert "self._users: UsersClient | None = None" in result
        assert "self._orders: OrdersClient | None = None" in result
        assert "self._products: ProductsClient | None = None" in result

        # Verify tag imports are present in the generated code
        assert "UsersClient" in result
        assert "OrdersClient" in result
        assert "ProductsClient" in result

    def test_visit__handles_operations_with_no_tags(self) -> None:
        """
        Scenario:
            Generate a client class with operations having no tags
        Expected Outcome:
            Operations without tags are assigned to a 'default' tag
        """
        # Create operations with no tags
        operations = [
            IROperation(
                operation_id="getStatus",
                path="/status",
                method=HTTPMethod.GET,
                summary="Get API status",
                description="Get API status",
                tags=None,  # No tags
                parameters=[],
                request_body=None,
                responses=[],
            ),
            IROperation(
                operation_id="getHealth",
                path="/health",
                method=HTTPMethod.GET,
                summary="Get API health",
                description="Get API health",
                tags=[],  # Empty tags list
                parameters=[],
                request_body=None,
                responses=[],
            ),
        ]

        # Create a spec with these operations
        spec = IRSpec(title="Test API", version="1.0.0", description="Test API description", operations=operations)

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Verify default tag property is generated
        assert "def default(self)" in result
        assert "self._default: DefaultClient | None = None" in result

        # Verify default tag import is present in the generated code
        assert "DefaultClient" in result

    def test_visit__handles_multiple_operations_with_same_tag(self) -> None:
        """
        Scenario:
            Generate a client class with multiple operations under the same tag
        Expected Outcome:
            Only one property is generated for the tag
        """
        # Create multiple operations with the same tag
        operations = [
            IROperation(
                operation_id="getUserById",
                path="/users/{id}",
                method=HTTPMethod.GET,
                summary="Get a user by ID",
                description="Get a user by ID",
                tags=["Users"],
                parameters=[],
                request_body=None,
                responses=[],
            ),
            IROperation(
                operation_id="createUser",
                path="/users",
                method=HTTPMethod.POST,
                summary="Create a new user",
                description="Create a new user",
                tags=["Users"],  # Same tag
                parameters=[],
                request_body=None,
                responses=[],
            ),
            IROperation(
                operation_id="updateUser",
                path="/users/{id}",
                method=HTTPMethod.PUT,
                summary="Update a user",
                description="Update a user",
                tags=["Users"],  # Same tag
                parameters=[],
                request_body=None,
                responses=[],
            ),
        ]

        # Create a spec with these operations
        spec = IRSpec(title="Test API", version="1.0.0", description="Test API description", operations=operations)

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Count occurrences of the 'users' property method
        # Should appear once in Protocol and once in implementation
        users_property_matches = re.findall(r"def\s+users\s*\(", result)
        assert len(users_property_matches) == 2  # Once in Protocol, once in implementation

        # Check for initialization in implementation - use more flexible pattern
        assert "self._users:" in result

        # Check Protocol includes users property
        assert "class APIClientProtocol(Protocol):" in result
        # Check implementation inherits from Protocol
        assert "class APIClient(APIClientProtocol):" in result

    def test_visit__normalizes_tag_names(self) -> None:
        """
        Scenario:
            Generate a client class with operations having unusual tag names
        Expected Outcome:
            Tag names are normalized to valid Python identifiers
        """
        # Create operations with unusual tag names
        operations = [
            IROperation(
                operation_id="op1",
                path="/path1",
                method=HTTPMethod.GET,
                summary="Operation 1",
                description="Operation 1",
                tags=["Tag-With-Hyphens"],
                parameters=[],
                request_body=None,
                responses=[],
            ),
            IROperation(
                operation_id="op2",
                path="/path2",
                method=HTTPMethod.GET,
                summary="Operation 2",
                description="Operation 2",
                tags=["Tag With Spaces"],
                parameters=[],
                request_body=None,
                responses=[],
            ),
            IROperation(
                operation_id="op3",
                path="/path3",
                method=HTTPMethod.GET,
                summary="Operation 3",
                description="Operation 3",
                tags=["123_numeric_prefix"],
                parameters=[],
                request_body=None,
                responses=[],
            ),
        ]

        # Create a spec with these operations
        spec = IRSpec(title="Test API", version="1.0.0", description="Test API description", operations=operations)

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Verify normalized property names
        assert "def tag_with_hyphens(self)" in result
        assert "def tag_with_spaces(self)" in result
        assert "_123_numeric_prefix" in result

        # Verify appropriate class names are in the generated code
        assert "TagWithHyphensClient" in result
        assert "TagWithSpacesClient" in result
        assert "_123NumericPrefixClient" in result

    def test_visit__generates_docstring_with_api_info(self) -> None:
        """
        Scenario:
            Generate a client class with API information
        Expected Outcome:
            Docstring includes API title, version, and description
        """
        # Create a spec with API information
        spec = IRSpec(
            title="Test API",
            version="2.1.0",
            description="This is a test API\nwith multiple lines\nof description.",
            operations=[],
        )

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Verify docstring contains API information
        assert '"""' in result  # Has docstring
        assert "Test API (version 2.1.0)" in result
        assert "This is a test API" in result
        assert "with multiple lines" in result
        assert "of description." in result

    def test_visit__generates_request_and_close_methods(self) -> None:
        """
        Scenario:
            Generate a client class with standard methods
        Expected Outcome:
            Class includes request() and close() methods
        """
        # Create a minimal spec
        spec = IRSpec(title="Test API", version="1.0.0", description="Test API", operations=[])

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Verify request method
        assert "async def request(self, method: str, url: str, **kwargs: Any) -> Any:" in result
        assert "return await self.transport.request(method, url, **kwargs)" in result

        # Verify close method
        assert "async def close(self) -> None:" in result
        assert "if hasattr(self.transport, 'close'):" in result
        assert "await self.transport.close()" in result

    def test_visit__generates_async_context_manager_methods(self) -> None:
        """
        Scenario:
            Generate a client class with async context manager support
        Expected Outcome:
            Class includes __aenter__ and __aexit__ methods
        """
        # Create a minimal spec
        spec = IRSpec(title="Test API", version="1.0.0", description="Test API", operations=[])

        # Visit the spec to generate the client code
        result = self.visitor.visit(spec, self.context)

        # Verify __aenter__ method
        assert "async def __aenter__(self) -> 'APIClient':" in result
        assert "if hasattr(self.transport, '__aenter__'):" in result
        assert "await self.transport.__aenter__()" in result
        assert "return self" in result

        # Verify __aexit__ method
        assert "async def __aexit__(" in result
        assert "exc_type: type[BaseException] | None" in result
        assert "exc_val: BaseException | None" in result
        assert "exc_tb: object | None" in result
        assert "if hasattr(self.transport, '__aexit__'):" in result
        assert "await self.transport.__aexit__(exc_type, exc_val, exc_tb)" in result
        assert "await self.close()" in result
