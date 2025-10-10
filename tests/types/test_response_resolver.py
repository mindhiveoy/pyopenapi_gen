"""Tests for response resolver."""

from unittest.mock import Mock

import pytest

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.types.contracts.types import ResolvedType
from pyopenapi_gen.types.resolvers.response_resolver import OpenAPIResponseResolver


class TestOpenAPIResponseResolver:
    """Test the response resolver."""

    @pytest.fixture
    def mock_ref_resolver(self):
        """Mock reference resolver."""
        return Mock()

    @pytest.fixture
    def mock_schema_resolver(self):
        """Mock schema resolver."""
        return Mock()

    @pytest.fixture
    def mock_context(self):
        """Mock type context."""
        return Mock()

    @pytest.fixture
    def resolver(self, mock_ref_resolver, mock_schema_resolver):
        """Response resolver instance."""
        return OpenAPIResponseResolver(mock_ref_resolver, mock_schema_resolver)

    def test_resolve_operation_response__no_responses__returns_none(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving operation with no responses
        Expected Outcome: Returns None type
        """
        # Arrange
        operation = IROperation(
            operation_id="getUsers",
            method="GET",
            path="/users",
            summary="Get users",
            description="Get all users",
            responses=[],
        )

        # Act
        result = resolver.resolve_operation_response(operation, mock_context)

        # Assert
        assert result.python_type == "None"

    def test_resolve_operation_response__200_response__returns_resolved_type(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Resolving operation with 200 response
        Expected Outcome: Returns resolved response type
        """
        # Arrange
        schema = IRSchema(type="string")
        response = IRResponse(status_code="200", description="Success", content={"application/json": schema})
        operation = IROperation(
            operation_id="getUsers",
            method="GET",
            path="/users",
            summary="Get users",
            description="Get all users",
            responses=[response],
        )

        expected_result = ResolvedType(python_type="str")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_operation_response(operation, mock_context)

        # Assert
        assert result.python_type == "str"
        mock_schema_resolver.resolve_schema.assert_called_once_with(schema, mock_context, required=True)

    def test_resolve_operation_response__prefers_200_over_201(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Resolving operation with both 200 and 201 responses
        Expected Outcome: Prefers 200 response
        """
        # Arrange
        schema_200 = IRSchema(type="string")
        schema_201 = IRSchema(type="integer")
        response_200 = IRResponse(status_code="200", description="Success", content={"application/json": schema_200})
        response_201 = IRResponse(status_code="201", description="Created", content={"application/json": schema_201})
        operation = IROperation(
            operation_id="createUser",
            method="POST",
            path="/users",
            summary="Create user",
            description="Create a new user",
            responses=[response_201, response_200],  # 201 first, but 200 should be preferred
        )

        expected_result = ResolvedType(python_type="str")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_operation_response(operation, mock_context)

        # Assert
        assert result.python_type == "str"
        mock_schema_resolver.resolve_schema.assert_called_once_with(schema_200, mock_context, required=True)

    def test_resolve_specific_response__no_content__returns_none(self, resolver, mock_context) -> None:
        """
        Scenario: Resolving response with no content
        Expected Outcome: Returns None type
        """
        # Arrange
        response = IRResponse(status_code="204", description="No Content", content={})

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "None"

    def test_resolve_specific_response__with_content__returns_resolved_type(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Resolving response with JSON content
        Expected Outcome: Returns resolved schema type
        """
        # Arrange
        schema = IRSchema(type="object")
        response = IRResponse(status_code="200", description="Success", content={"application/json": schema})

        expected_result = ResolvedType(python_type="dict[str, Any]")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "dict[str, Any]"
        mock_schema_resolver.resolve_schema.assert_called_once_with(schema, mock_context, required=True)

    def test_resolve_specific_response__data_wrapper__returns_wrapper_type(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Resolving response with data wrapper property
        Expected Outcome: Returns wrapper type as-is (no unwrapping)
        """
        # Arrange
        data_schema = IRSchema(type="string")
        wrapper_schema = IRSchema(type="object", properties={"data": data_schema})
        response = IRResponse(status_code="200", description="Success", content={"application/json": wrapper_schema})

        # Mock returns wrapper type (no unwrapping behavior)
        expected_result = ResolvedType(python_type="WrapperType")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "WrapperType"
        # Should be called only once for the wrapper schema (no unwrapping)
        mock_schema_resolver.resolve_schema.assert_called_once_with(wrapper_schema, mock_context, required=True)

    def test_resolve_specific_response__response_reference__resolves_target(
        self, resolver, mock_context, mock_ref_resolver
    ) -> None:
        """
        Scenario: Resolving response with $ref
        Expected Outcome: Resolves target response
        """
        # Arrange
        target_schema = IRSchema(type="string")
        target_response = IRResponse(
            status_code="200", description="Success", content={"application/json": target_schema}
        )
        response = Mock()
        response.ref = "#/components/responses/UserResponse"

        mock_ref_resolver.resolve_response_ref.return_value = target_response

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        mock_ref_resolver.resolve_response_ref.assert_called_once_with("#/components/responses/UserResponse")

    def test_resolve_specific_response__prefers_application_json(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Resolving response with multiple content types
        Expected Outcome: Prefers application/json
        """
        # Arrange
        json_schema = IRSchema(type="object")
        xml_schema = IRSchema(type="string")
        response = IRResponse(
            status_code="200",
            description="Success",
            content={
                "application/xml": xml_schema,
                "application/json": json_schema,
                "text/plain": IRSchema(type="string"),
            },
        )

        expected_result = ResolvedType(python_type="dict[str, Any]")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "dict[str, Any]"
        # Should resolve the JSON schema, not XML or plain text
        mock_schema_resolver.resolve_schema.assert_called_once_with(json_schema, mock_context, required=True)

    def test_resolve_specific_response__prefers_json_variants(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Response with JSON variants but no application/json
        Expected Outcome: Prefers any content type containing 'json'
        """
        # Arrange
        json_api_schema = IRSchema(type="object")
        xml_schema = IRSchema(type="string")
        response = IRResponse(
            status_code="200",
            description="Success",
            content={
                "application/xml": xml_schema,
                "application/vnd.api+json": json_api_schema,
                "text/plain": IRSchema(type="string"),
            },
        )

        expected_result = ResolvedType(python_type="dict[str, Any]")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "dict[str, Any]"
        # Should resolve the JSON API schema
        mock_schema_resolver.resolve_schema.assert_called_once_with(json_api_schema, mock_context, required=True)

    def test_resolve_specific_response__fallback_to_first_content_type(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Response with no JSON content types
        Expected Outcome: Uses first available content type
        """
        # Arrange
        xml_schema = IRSchema(type="string")
        plain_schema = IRSchema(type="string")
        response = IRResponse(
            status_code="200",
            description="Success",
            content={
                "application/xml": xml_schema,
                "text/plain": plain_schema,
            },
        )

        expected_result = ResolvedType(python_type="str")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "str"
        # Should resolve the first content type (XML)
        mock_schema_resolver.resolve_schema.assert_called_once_with(xml_schema, mock_context, required=True)

    def test_resolve_specific_response__response_ref_not_found(self, resolver, mock_context, mock_ref_resolver) -> None:
        """
        Scenario: Response reference cannot be resolved
        Expected Outcome: Returns None type
        """
        # Arrange
        response = Mock()
        response.ref = "#/components/responses/NonExistentResponse"

        # Mock ref resolver to return None (not found)
        mock_ref_resolver.resolve_response_ref.return_value = None

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "None"
        mock_ref_resolver.resolve_response_ref.assert_called_once_with("#/components/responses/NonExistentResponse")

    def test_resolve_specific_response__streaming_binary_content(self, resolver, mock_context) -> None:
        """
        Scenario: Streaming response with binary content
        Expected Outcome: Returns AsyncIterator[bytes]
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Streaming binary",
            content={"application/octet-stream": IRSchema(type="string", format="binary")},
            stream=True,
        )

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "AsyncIterator[bytes]"
        mock_context.add_import.assert_called_with("typing", "AsyncIterator")

    def test_resolve_specific_response__streaming_event_stream(self, resolver, mock_context) -> None:
        """
        Scenario: Streaming response with event stream content
        Expected Outcome: Returns AsyncIterator[dict[str, Any]]
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Server-sent events",
            content={"text/event-stream": IRSchema(type="object")},
            stream=True,
        )

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "AsyncIterator[dict[str, Any]]"
        mock_context.add_import.assert_any_call("typing", "AsyncIterator")
        # Note: Modern dict[str, Any] doesn't require Dict import (Python 3.10+)
        mock_context.add_import.assert_any_call("typing", "Any")

    def test_resolve_specific_response__streaming_with_schema(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Streaming response with resolvable schema
        Expected Outcome: Returns AsyncIterator[ResolvedType]
        """
        # Arrange
        stream_schema = IRSchema(type="object", name="StreamItem")
        response = IRResponse(
            status_code="200", description="Streaming objects", content={"application/json": stream_schema}, stream=True
        )

        expected_result = ResolvedType(python_type="StreamItem")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "AsyncIterator[StreamItem]"
        mock_context.add_import.assert_called_with("typing", "AsyncIterator")
        mock_schema_resolver.resolve_schema.assert_called_once_with(stream_schema, mock_context, required=True)

    def test_resolve_specific_response__streaming_no_content(self, resolver, mock_context) -> None:
        """
        Scenario: Streaming response with no content
        Expected Outcome: Returns AsyncIterator[bytes]
        """
        # Arrange
        response = IRResponse(status_code="200", description="Empty stream", content={}, stream=True)

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "AsyncIterator[bytes]"
        mock_context.add_import.assert_called_with("typing", "AsyncIterator")
