"""Tests for unified response strategy system."""

from unittest.mock import Mock, patch

import pytest

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy, ResponseStrategyResolver


class TestResponseStrategy:
    """Test the ResponseStrategy data class."""

    def test_response_strategy__basic_properties(self) -> None:
        """
        Scenario: Creating a basic ResponseStrategy
        Expected Outcome: All properties are accessible
        """
        # Arrange & Act
        strategy = ResponseStrategy(
            return_type="User",
            response_schema=Mock(spec=IRSchema),
            is_streaming=False,
            response_ir=Mock(spec=IRResponse)
        )

        # Assert
        assert strategy.return_type == "User"
        assert strategy.is_streaming is False
        assert strategy.response_schema is not None
        assert strategy.response_ir is not None

    def test_response_strategy__streaming_properties(self) -> None:
        """
        Scenario: Creating a streaming ResponseStrategy
        Expected Outcome: Streaming properties are set correctly
        """
        # Arrange & Act
        strategy = ResponseStrategy(
            return_type="AsyncIterator[Dict[str, Any]]",
            response_schema=None,
            is_streaming=True,
            response_ir=Mock(spec=IRResponse)
        )

        # Assert
        assert strategy.return_type == "AsyncIterator[Dict[str, Any]]"
        assert strategy.is_streaming is True
        assert strategy.response_schema is None
        assert strategy.response_ir is not None


class TestResponseStrategyResolver:
    """Test the ResponseStrategyResolver."""

    @pytest.fixture
    def mock_context(self):
        """Mock render context."""
        context = Mock(spec=RenderContext)
        context.add_import = Mock()
        context.add_conditional_import = Mock()
        return context

    @pytest.fixture
    def mock_schemas(self):
        """Mock schemas dictionary."""
        return {
            "User": IRSchema(name="User", type="object"),
            "UserResponse": IRSchema(name="UserResponse", type="object"),
        }

    @pytest.fixture
    def resolver(self, mock_schemas):
        """ResponseStrategyResolver instance."""
        return ResponseStrategyResolver(mock_schemas)

    def test_resolve__no_responses__returns_none_strategy(self, resolver, mock_context) -> None:
        """
        Scenario: Operation has no responses
        Expected Outcome: Strategy with return_type=None
        """
        # Arrange
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test operation description",
            responses=[]
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.return_type == "None"
        assert strategy.response_schema is None
        assert strategy.is_streaming is False

    def test_resolve__no_content_response__returns_none_strategy(self, resolver, mock_context) -> None:
        """
        Scenario: Operation has 204 response with no content
        Expected Outcome: Strategy with return_type=None
        """
        # Arrange
        operation = IROperation(
            operation_id="delete_user",
            method=HTTPMethod.DELETE,
            path="/users/{id}",
            summary="Delete user",
            description="Delete a user by ID",
            responses=[
                IRResponse(status_code="204", description="No Content", content={})
            ]
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.return_type == "None"
        assert strategy.response_schema is None
        assert strategy.is_streaming is False

    def test_resolve__simple_schema__returns_direct_strategy(self, resolver, mock_context) -> None:
        """
        Scenario: Response schema is used directly (no unwrapping)
        Expected Outcome: Strategy uses schema type as-is
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        
        operation = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary="Get User",
            description="Get User operation",
            responses=[
                IRResponse(
                    status_code="200",
                    description="User response",
                    content={"application/json": user_schema}
                )
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "User"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "User"
            assert strategy.response_schema == user_schema
            assert strategy.is_streaming is False

    def test_resolve__wrapper_schema__returns_wrapper_strategy(self, resolver, mock_context) -> None:
        """
        Scenario: Response has wrapper schema with data property
        Expected Outcome: Strategy uses wrapper type as-is (no unwrapping)
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        wrapper_schema = IRSchema(
            name="UserResponse",
            type="object",
            properties={"data": user_schema}
        )
        
        operation = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary="Get User",
            description="Get User operation",
            responses=[
                IRResponse(
                    status_code="200",
                    description="User response",
                    content={"application/json": wrapper_schema}
                )
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "UserResponse"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "UserResponse"
            assert strategy.response_schema == wrapper_schema
            assert strategy.is_streaming is False

    def test_resolve__list_response__returns_list_strategy(self, resolver, mock_context) -> None:
        """
        Scenario: Response has list data with metadata
        Expected Outcome: Strategy uses wrapper type as-is (no list unwrapping)
        """
        # Arrange
        user_list_schema = IRSchema(name="UserList", type="array")
        wrapper_schema = IRSchema(
            name="UserListResponse",
            type="object",
            properties={
                "data": user_list_schema,
                "meta": IRSchema(type="object"),
                "pagination": IRSchema(type="object")
            }
        )
        
        operation = IROperation(
            operation_id="list_users",
            method=HTTPMethod.GET,
            path="/users",
            summary="List Users",
            description="List Users operation",
            responses=[
                IRResponse(
                    status_code="200",
                    description="User list response",
                    content={"application/json": wrapper_schema}
                )
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "UserListResponse"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "UserListResponse"
            assert strategy.response_schema == wrapper_schema

    def test_resolve__streaming_response__returns_streaming_strategy(self, resolver, mock_context) -> None:
        """
        Scenario: Response is marked as streaming
        Expected Outcome: Strategy with is_streaming=True
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Streaming response",
            content={"text/event-stream": IRSchema(type="object")},
            stream=True  # This marks it as streaming
        )
        
        operation = IROperation(
            operation_id="stream_events",
            method=HTTPMethod.GET,
            path="/events/stream",
            summary="Stream Events",
            description="Stream Events operation",
            responses=[response]
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.is_streaming is True
        assert "AsyncIterator" in strategy.return_type
        # Check that the correct imports were added
        mock_context.add_import.assert_any_call("typing", "AsyncIterator")

    def test_resolve__binary_streaming__returns_bytes_iterator(self, resolver, mock_context) -> None:
        """
        Scenario: Streaming response with binary content
        Expected Outcome: AsyncIterator[bytes] strategy
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Binary stream",
            content={"application/octet-stream": IRSchema(type="string", format="binary")},
            stream=True
        )
        
        operation = IROperation(
            operation_id="download_file",
            method=HTTPMethod.GET,
            path="/files/{id}/download",
            summary="Download File",
            description="Download File operation",
            responses=[response]
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.return_type == "AsyncIterator[bytes]"
        assert strategy.is_streaming is True

    def test_resolve__event_stream__returns_dict_iterator(self, resolver, mock_context) -> None:
        """
        Scenario: Event stream response
        Expected Outcome: AsyncIterator[Dict[str, Any]] strategy
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Event stream",
            content={"text/event-stream": IRSchema(type="object")},
            stream=True
        )
        
        operation = IROperation(
            operation_id="listen_events",
            method=HTTPMethod.GET,
            path="/events",
            summary="Listen Events",
            description="Listen Events operation",
            responses=[response]
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.return_type == "AsyncIterator[Dict[str, Any]]"
        assert strategy.is_streaming is True
        mock_context.add_import.assert_any_call("typing", "Dict")
        mock_context.add_import.assert_any_call("typing", "Any")

    def test_resolve__multiple_responses__prioritizes_correctly(self, resolver, mock_context) -> None:
        """
        Scenario: Operation has multiple responses (200, 404, 500)
        Expected Outcome: Strategy based on 200 response (primary success)
        """
        # Arrange
        success_schema = IRSchema(name="User", type="object")
        
        operation = IROperation(
            operation_id="get_user_with_errors",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary="Get User With Errors",
            description="Get User With Errors operation",
            responses=[
                IRResponse(status_code="404", description="Not Found", content={}),
                IRResponse(
                    status_code="200",
                    description="Success",
                    content={"application/json": success_schema}
                ),
                IRResponse(status_code="500", description="Server Error", content={})
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "User"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "User"
            assert strategy.response_ir.status_code == "200"

    def test_resolve__201_response__prioritizes_201_over_other_codes(self, resolver, mock_context) -> None:
        """
        Scenario: Operation has 201 response (creation endpoint)
        Expected Outcome: Strategy based on 201 response
        """
        # Arrange
        created_schema = IRSchema(name="CreatedUser", type="object")
        
        operation = IROperation(
            operation_id="create_user",
            method=HTTPMethod.POST,
            path="/users",
            summary="Create User",
            description="Create User operation",
            responses=[
                IRResponse(status_code="400", description="Bad Request", content={}),
                IRResponse(
                    status_code="201",
                    description="Created",
                    content={"application/json": created_schema}
                )
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "CreatedUser"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "CreatedUser"
            assert strategy.response_ir.status_code == "201"

    def test_resolve__complex_object__uses_schema_as_is(self, resolver, mock_context) -> None:
        """
        Scenario: Complex object schema used directly
        Expected Outcome: Schema type used as-is (no unwrapping analysis)
        """
        # Arrange
        schema = IRSchema(
            name="ComplexUser",
            type="object",
            properties={
                "profile": IRSchema(type="object"),
                "settings": IRSchema(type="object"),
                "permissions": IRSchema(type="array")
            }
        )
        
        operation = IROperation(
            operation_id="get_complex_user",
            method=HTTPMethod.GET,
            path="/users/{id}/complex",
            summary="Get Complex User",
            description="Get Complex User operation",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Complex user",
                    content={"application/json": schema}
                )
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "ComplexUser"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "ComplexUser"
            assert strategy.response_schema == schema
            assert strategy.is_streaming is False

    def test_resolve__data_field_ignored__uses_wrapper_as_is(self, resolver, mock_context) -> None:
        """
        Scenario: Object with 'data' field is used as-is (no special unwrapping)
        Expected Outcome: Wrapper type used directly
        """
        # Arrange
        schema = IRSchema(
            name="ApiWrapper",
            type="object",
            properties={
                "data": IRSchema(type="object"),
                "meta": IRSchema(type="object"),
                "pagination": IRSchema(type="object"),
                "extra1": IRSchema(type="string"),
                "extra2": IRSchema(type="string")
            }
        )
        
        operation = IROperation(
            operation_id="get_wrapped_data",
            method=HTTPMethod.GET,
            path="/data/wrapped",
            summary="Get Wrapped Data",
            description="Get Wrapped Data operation",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Wrapped data",
                    content={"application/json": schema}
                )
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "ApiWrapper"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "ApiWrapper"
            assert strategy.response_schema == schema
            assert strategy.is_streaming is False