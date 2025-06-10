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

        expected_result = ResolvedType(python_type="Dict[str, Any]")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "Dict[str, Any]"
        mock_schema_resolver.resolve_schema.assert_called_once_with(schema, mock_context, required=True)

    def test_resolve_specific_response__data_unwrapping__returns_unwrapped_type(
        self, resolver, mock_context, mock_schema_resolver
    ) -> None:
        """
        Scenario: Resolving response with data wrapper property
        Expected Outcome: Returns unwrapped type
        """
        # Arrange
        data_schema = IRSchema(type="string")
        wrapper_schema = IRSchema(type="object", properties={"data": data_schema})
        response = IRResponse(status_code="200", description="Success", content={"application/json": wrapper_schema})

        # First call returns wrapper, second call returns unwrapped data
        mock_schema_resolver.resolve_schema.side_effect = [
            ResolvedType(python_type="WrapperType"),  # First call for wrapper
            ResolvedType(python_type="str"),  # Second call for data property
        ]

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "str"
        # Should be called twice: once for wrapper, once for data property
        assert mock_schema_resolver.resolve_schema.call_count == 2

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

        expected_result = ResolvedType(python_type="Dict[str, Any]")
        mock_schema_resolver.resolve_schema.return_value = expected_result

        # Act
        result = resolver.resolve_specific_response(response, mock_context)

        # Assert
        assert result.python_type == "Dict[str, Any]"
        # Should resolve the JSON schema, not XML or plain text
        mock_schema_resolver.resolve_schema.assert_called_once_with(json_schema, mock_context, required=True)
