"""Tests for reference resolver."""

from pyopenapi_gen import IRResponse, IRSchema
from pyopenapi_gen.types.resolvers.reference_resolver import OpenAPIReferenceResolver


class TestOpenAPIReferenceResolver:
    """Test the reference resolver."""

    def test_resolve_schema_ref__valid_ref__returns_schema(self) -> None:
        """
        Scenario: Resolving a valid schema reference
        Expected Outcome: Returns the target schema
        """
        # Arrange
        schema = IRSchema(name="User", type="object")
        resolver = OpenAPIReferenceResolver({"User": schema})

        # Act
        result = resolver.resolve_ref("#/components/schemas/User")

        # Assert
        assert result is schema

    def test_resolve_schema_ref__missing_schema__returns_none(self) -> None:
        """
        Scenario: Resolving a reference to non-existent schema
        Expected Outcome: Returns None and logs warning
        """
        # Arrange
        resolver = OpenAPIReferenceResolver({})

        # Act
        result = resolver.resolve_ref("#/components/schemas/MissingUser")

        # Assert
        assert result is None

    def test_resolve_schema_ref__invalid_format__returns_none(self) -> None:
        """
        Scenario: Resolving a malformed reference
        Expected Outcome: Returns None and logs warning
        """
        # Arrange
        resolver = OpenAPIReferenceResolver({})

        # Act
        result = resolver.resolve_ref("invalid-ref")

        # Assert
        assert result is None

    def test_resolve_response_ref__valid_ref__returns_response(self) -> None:
        """
        Scenario: Resolving a valid response reference
        Expected Outcome: Returns the target response
        """
        # Arrange
        response = IRResponse(status_code="200", description="Success", content={})
        resolver = OpenAPIReferenceResolver({}, {"UserResponse": response})

        # Act
        result = resolver.resolve_response_ref("#/components/responses/UserResponse")

        # Assert
        assert result is response

    def test_resolve_response_ref__missing_response__returns_none(self) -> None:
        """
        Scenario: Resolving a reference to non-existent response
        Expected Outcome: Returns None and logs warning
        """
        # Arrange
        resolver = OpenAPIReferenceResolver({}, {})

        # Act
        result = resolver.resolve_response_ref("#/components/responses/MissingResponse")

        # Assert
        assert result is None

    def test_resolve_response_ref__invalid_format__returns_none(self) -> None:
        """
        Scenario: Resolving a malformed response reference
        Expected Outcome: Returns None and logs warning
        """
        # Arrange
        resolver = OpenAPIReferenceResolver({}, {})

        # Act
        result = resolver.resolve_response_ref("invalid-ref")

        # Assert
        assert result is None
