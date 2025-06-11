"""Tests for simplified unified response strategy system."""

from unittest.mock import Mock, patch

import pytest

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy, ResponseStrategyResolver


class TestResponseStrategy:
    """Test the simplified ResponseStrategy data class."""

    def test_response_strategy__basic_properties(self) -> None:
        """
        Scenario: Creating a basic ResponseStrategy with simplified fields
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
        assert strategy.response_schema is not None
        assert strategy.is_streaming is False
        assert strategy.response_ir is not None


class TestResponseStrategyResolver:
    """Test the simplified ResponseStrategyResolver."""

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
            summary="test",
            description="test",
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
            summary="delete user",
            description="delete user",
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

    def test_resolve__direct_schema_response__returns_schema_as_is(self, resolver, mock_context) -> None:
        """
        Scenario: Response has schema - should use it as-is without unwrapping
        Expected Outcome: Strategy uses the OpenAPI schema exactly as defined
        """
        # Arrange
        user_response_schema = IRSchema(
            name="UserResponse",
            type="object",
            properties={
                "data": IRSchema(name="User", type="object"),
                "meta": IRSchema(type="object")
            }
        )
        
        operation = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary="get user",
            description="get user",
            responses=[
                IRResponse(
                    status_code="200",
                    description="User response",
                    content={"application/json": user_response_schema}
                )
            ]
        )

        with patch.object(resolver.type_service, 'resolve_schema_type') as mock_resolve:
            mock_resolve.return_value = "UserResponse"

            # Act
            strategy = resolver.resolve(operation, mock_context)

            # Assert
            assert strategy.return_type == "UserResponse"
            assert strategy.response_schema == user_response_schema
            assert strategy.is_streaming is False

    def test_resolve__simple_object_response__returns_simple_type(self, resolver, mock_context) -> None:
        """
        Scenario: Response has simple object schema
        Expected Outcome: Strategy with simple return type
        """
        # Arrange
        user_schema = IRSchema(
            name="User",
            type="object",
            properties={
                "id": IRSchema(type="string"),
                "name": IRSchema(type="string")
            }
        )
        
        operation = IROperation(
            operation_id="get_user_direct",
            method=HTTPMethod.GET,
            path="/user-direct/{id}",
            summary="get user direct",
            description="get user direct",
            responses=[
                IRResponse(
                    status_code="200",
                    description="Direct user response",
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
            summary="stream events",
            description="stream events",
            responses=[response]
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.is_streaming is True
        assert "AsyncIterator" in strategy.return_type
        # For event-stream, it also imports Dict and Any
        mock_context.add_import.assert_any_call("typing", "AsyncIterator")
        mock_context.add_import.assert_any_call("typing", "Dict")
        mock_context.add_import.assert_any_call("typing", "Any")

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
            summary="download file",
            description="download file",
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
            summary="listen events",
            description="listen events",
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
            summary="get user with errors",
            description="get user with errors",
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
            summary="create user",
            description="create user",
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