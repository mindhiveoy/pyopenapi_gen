"""
Real Contract Tests for Protocol and Mock Generation (No Mock Theatre).

These tests validate actual Protocol and Mock generation behavior using real
IROperation objects and real code generation without mocking internal components.
"""

from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.visit.endpoint.endpoint_visitor import EndpointVisitor


class TestProtocolGeneration:
    """Real contract tests for Protocol generation."""

    def test_generate_endpoint_protocol__single_operation__creates_protocol_with_runtime_checkable(self) -> None:
        """
        Scenario: Generate Protocol from single operation
        Expected Outcome: Protocol class with @runtime_checkable decorator and method stub
        """
        # Arrange
        operation = IROperation(
            path="/users/{user_id}",
            method=HTTPMethod.GET,
            operation_id="get_user",
            summary="Get user by ID",
            description="Retrieves a user",
            parameters=[
                IRParameter(
                    name="user_id",
                    param_in="path",
                    required=True,
                    schema=IRSchema(type="integer"),
                )
            ],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="Success",
                    content={"application/json": IRSchema(type="User")},
                )
            ],
            tags=["users"],
        )
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()

        # Act
        protocol_code = visitor.generate_endpoint_protocol("users", [operation], context)

        # Assert - Validate actual generated code structure
        assert "@runtime_checkable" in protocol_code
        assert "class UsersClientProtocol(Protocol):" in protocol_code
        assert '"""Protocol defining the interface of UsersClient' in protocol_code
        # Protocol method should end with : ...
        assert ": ..." in protocol_code
        # Should be async method
        assert "async def get_user" in protocol_code

    def test_generate_endpoint_protocol__multiple_operations__includes_all_methods(self) -> None:
        """
        Scenario: Generate Protocol from multiple operations
        Expected Outcome: Protocol class with all operation method stubs
        """
        # Arrange
        operations = [
            IROperation(
                path="/users/{user_id}",
                method=HTTPMethod.GET,
                operation_id="get_user",
                summary="Get user",
                description="Get user by ID",
                parameters=[
                    IRParameter(
                        name="user_id",
                        param_in="path",
                        required=True,
                        schema=IRSchema(type="integer"),
                    )
                ],
                request_body=None,
                responses=[
                    IRResponse(
                        status_code="200",
                        description="Success",
                        content={"application/json": IRSchema(type="User")},
                    )
                ],
                tags=["users"],
            ),
            IROperation(
                path="/users",
                method=HTTPMethod.POST,
                operation_id="create_user",
                summary="Create user",
                description="Create a new user",
                parameters=[],
                request_body=IRRequestBody(
                    required=True,
                    content={"application/json": IRSchema(type="UserCreate")},
                ),
                responses=[
                    IRResponse(
                        status_code="201",
                        description="Created",
                        content={"application/json": IRSchema(type="User")},
                    )
                ],
                tags=["users"],
            ),
        ]
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()

        # Act
        protocol_code = visitor.generate_endpoint_protocol("users", operations, context)

        # Assert - Both methods should be present
        assert "async def get_user" in protocol_code
        assert "async def create_user" in protocol_code
        # Both should have stub format
        assert protocol_code.count(": ...") >= 2

    def test_generate_endpoint_protocol__registers_protocol_imports(self) -> None:
        """
        Scenario: Generate Protocol and check import registration
        Expected Outcome: Protocol and runtime_checkable imports are registered
        """
        # Arrange
        operation = IROperation(
            path="/test",
            method=HTTPMethod.GET,
            operation_id="test_op",
            summary="Test",
            description="Test operation",
            parameters=[],
            request_body=None,
            responses=[],
            tags=["test"],
        )
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()

        # Act
        _ = visitor.generate_endpoint_protocol("test", [operation], context)

        # Assert - Check imports were registered
        imports = context.render_imports()
        assert "Protocol" in imports
        assert "runtime_checkable" in imports


class TestMockGeneration:
    """Real contract tests for Mock generation."""

    def test_generate_endpoint_mock_class__single_operation__creates_stub_with_not_implemented_error(self) -> None:
        """
        Scenario: Generate mock class from single operation
        Expected Outcome: Mock class with NotImplementedError stub and helpful message
        """
        # Arrange
        operation = IROperation(
            path="/users/{user_id}",
            method=HTTPMethod.GET,
            operation_id="get_user",
            summary="Get user",
            description="Get user by ID",
            parameters=[
                IRParameter(
                    name="user_id",
                    param_in="path",
                    required=True,
                    schema=IRSchema(type="integer"),
                )
            ],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="Success",
                    content={"application/json": IRSchema(type="User")},
                )
            ],
            tags=["users"],
        )
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()

        # Act
        mock_code = visitor.generate_endpoint_mock_class("users", [operation], context)

        # Assert - Validate mock class structure
        assert "class MockUsersClient:" in mock_code
        assert '"""' in mock_code  # Has docstring
        assert "Mock implementation of UsersClient for testing" in mock_code
        # Should have the method signature
        assert "async def get_user" in mock_code
        # Should have NotImplementedError
        assert "NotImplementedError" in mock_code
        # Should have helpful override guidance
        assert "Override this method in your test" in mock_code or "not implemented" in mock_code

    def test_generate_endpoint_mock_class__multiple_operations__all_stubs_present(self) -> None:
        """
        Scenario: Generate mock class from multiple operations
        Expected Outcome: Mock class with all operation stubs
        """
        # Arrange
        operations = [
            IROperation(
                path="/users/{user_id}",
                method=HTTPMethod.GET,
                operation_id="get_user",
                summary="Get user",
                description="Get user",
                parameters=[
                    IRParameter(
                        name="user_id",
                        param_in="path",
                        required=True,
                        schema=IRSchema(type="integer"),
                    )
                ],
                request_body=None,
                responses=[],
                tags=["users"],
            ),
            IROperation(
                path="/users",
                method=HTTPMethod.POST,
                operation_id="create_user",
                summary="Create user",
                description="Create user",
                parameters=[],
                request_body=IRRequestBody(
                    required=True,
                    content={"application/json": IRSchema(type="object")},
                ),
                responses=[],
                tags=["users"],
            ),
        ]
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()

        # Act
        mock_code = visitor.generate_endpoint_mock_class("users", operations, context)

        # Assert - Both method stubs should be present
        assert "async def get_user" in mock_code
        assert "async def create_user" in mock_code
        # Both should have NotImplementedError
        assert mock_code.count("NotImplementedError") >= 2

    def test_generate_endpoint_mock_class__includes_helpful_docstring(self) -> None:
        """
        Scenario: Generate mock class and check docstring
        Expected Outcome: Mock class has comprehensive docstring with usage example
        """
        # Arrange
        operation = IROperation(
            path="/test",
            method=HTTPMethod.GET,
            operation_id="test_op",
            summary="Test",
            description="Test",
            parameters=[],
            request_body=None,
            responses=[],
            tags=["test"],
        )
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()

        # Act
        mock_code = visitor.generate_endpoint_mock_class("test", [operation], context)

        # Assert - Check docstring content
        assert '"""' in mock_code
        assert "Mock implementation" in mock_code
        assert "testing" in mock_code
        # Should mention NotImplementedError pattern
        assert "NotImplementedError" in mock_code or "Override" in mock_code


class TestProtocolAndImplementationIntegration:
    """Real contract tests for Protocol + Implementation integration."""

    def test_emit_endpoint_client_class__with_operations__generates_protocol_and_implementation(self) -> None:
        """
        Scenario: Generate complete endpoint client with operations
        Expected Outcome: Both Protocol and Implementation classes are generated
        """
        # Arrange
        operation = IROperation(
            path="/users/{user_id}",
            method=HTTPMethod.GET,
            operation_id="get_user",
            summary="Get user",
            description="Get user",
            parameters=[
                IRParameter(
                    name="user_id",
                    param_in="path",
                    required=True,
                    schema=IRSchema(type="integer"),
                )
            ],
            request_body=None,
            responses=[
                IRResponse(
                    status_code="200",
                    description="Success",
                    content={"application/json": IRSchema(type="User")},
                )
            ],
            tags=["users"],
        )
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()

        # Generate method code first (required by emit_endpoint_client_class)
        method_code = visitor.visit_IROperation(operation, context)

        # Act
        complete_code = visitor.emit_endpoint_client_class(
            "users",
            [method_code],
            context,
            operations=[operation],  # Triggers Protocol generation
        )

        # Assert - Both Protocol and Implementation should be present
        assert "class UsersClientProtocol(Protocol):" in complete_code
        assert "@runtime_checkable" in complete_code
        assert "class UsersClient(UsersClientProtocol):" in complete_code
        # Implementation should inherit from Protocol
        assert "UsersClient(UsersClientProtocol)" in complete_code

    def test_emit_endpoint_client_class__implementation_has_init__(self) -> None:
        """
        Scenario: Generate implementation class
        Expected Outcome: Implementation has __init__ with transport and base_url
        """
        # Arrange
        operation = IROperation(
            path="/test",
            method=HTTPMethod.GET,
            operation_id="test_op",
            summary="Test",
            description="Test",
            parameters=[],
            request_body=None,
            responses=[],
            tags=["test"],
        )
        context = RenderContext(core_package_name="test_core")
        visitor = EndpointVisitor()
        method_code = visitor.visit_IROperation(operation, context)

        # Act
        complete_code = visitor.emit_endpoint_client_class(
            "test",
            [method_code],
            context,
            operations=[operation],
        )

        # Assert - Check __init__ method
        assert "def __init__(self, transport: HttpTransport, base_url: str)" in complete_code
        assert "self._transport = transport" in complete_code
        assert "self.base_url: str = base_url" in complete_code
