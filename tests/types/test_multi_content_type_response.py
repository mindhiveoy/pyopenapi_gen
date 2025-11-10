"""Tests for multi-content-type response handling."""

from unittest.mock import Mock

import pytest

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategyResolver


class TestMultiContentTypeResponses:
    """Test response strategy with multiple content types."""

    @pytest.fixture
    def mock_context(self):
        """Create a mock RenderContext."""
        context = Mock(spec=RenderContext)
        context.add_import = Mock()
        context.add_typing_imports_for_type = Mock()
        return context

    @pytest.fixture
    def resolver(self):
        """Create a ResponseStrategyResolver with mock schemas."""
        schemas = {
            "DocumentResponse": IRSchema(
                name="DocumentResponse",
                type="object",
                properties={
                    "id": IRSchema(type="string"),
                    "title": IRSchema(type="string"),
                },
                generation_name="DocumentResponse",
            )
        }
        return ResponseStrategyResolver(schemas)

    def test_resolve__single_content_type__no_union(self, resolver, mock_context) -> None:
        """
        Scenario: Response with single content type
        Expected Outcome: No Union type, normal handling
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": IRSchema(type="string"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.return_type == "str"
        assert strategy.content_type_mapping is None  # Single content type
        assert not strategy.is_streaming

    def test_resolve__multiple_content_types__creates_union(self, resolver, mock_context) -> None:
        """
        Scenario: Response with multiple content types (JSON and binary)
        Expected Outcome: Creates Union[DocumentResponse, bytes] with content_type_mapping
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "application/octet-stream": IRSchema(type="string", format="binary"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.return_type == "Union[DocumentResponse, bytes]"
        assert strategy.content_type_mapping is not None
        assert "application/json" in strategy.content_type_mapping
        assert "application/octet-stream" in strategy.content_type_mapping
        assert strategy.content_type_mapping["application/json"] == "DocumentResponse"
        assert strategy.content_type_mapping["application/octet-stream"] == "bytes"
        assert not strategy.is_streaming
        mock_context.add_import.assert_any_call("typing", "Union")

    def test_resolve__json_and_html__creates_union_with_bytes(self, resolver, mock_context) -> None:
        """
        Scenario: Response with JSON and HTML content types
        Expected Outcome: Creates Union[DocumentResponse, bytes]
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "text/html": IRSchema(type="string"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert "Union[" in strategy.return_type
        assert "DocumentResponse" in strategy.return_type
        assert "str" in strategy.return_type  # text/html with type=string maps to str
        assert strategy.content_type_mapping is not None

    def test_resolve__pdf_content__maps_to_bytes(self, resolver, mock_context) -> None:
        """
        Scenario: Response with application/pdf content type
        Expected Outcome: Maps to bytes type
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "application/pdf": IRSchema(type="string", format="binary"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.content_type_mapping is not None
        assert strategy.content_type_mapping["application/pdf"] == "bytes"

    def test_resolve__image_content__maps_to_bytes(self, resolver, mock_context) -> None:
        """
        Scenario: Response with image/* content types
        Expected Outcome: Maps to bytes type
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "image/png": IRSchema(type="string", format="binary"),
                "image/jpeg": IRSchema(type="string", format="binary"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.content_type_mapping is not None
        assert strategy.content_type_mapping["image/png"] == "bytes"
        assert strategy.content_type_mapping["image/jpeg"] == "bytes"
        # Should have Union with DocumentResponse and bytes (deduplicated)
        assert "Union[" in strategy.return_type
        assert "DocumentResponse" in strategy.return_type
        assert "bytes" in strategy.return_type

    def test_resolve__multiple_same_type__deduplicates_union(self, resolver, mock_context) -> None:
        """
        Scenario: Multiple content types mapping to the same Python type
        Expected Outcome: Union has no duplicates
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/octet-stream": IRSchema(type="string", format="binary"),
                "application/pdf": IRSchema(type="string", format="binary"),
                "image/png": IRSchema(type="string", format="binary"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        # All three content types map to bytes, so no Union needed
        assert strategy.return_type == "bytes"
        assert strategy.content_type_mapping is not None
        assert len(strategy.content_type_mapping) == 3

    def test_resolve__text_plain_with_string_schema__maps_to_str(self, resolver, mock_context) -> None:
        """
        Scenario: Response with text/plain and string schema
        Expected Outcome: Maps to str type
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "text/plain": IRSchema(type="string"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.content_type_mapping is not None
        assert strategy.content_type_mapping["text/plain"] == "str"
        assert "Union[" in strategy.return_type
        assert "DocumentResponse" in strategy.return_type
        assert "str" in strategy.return_type

    def test_resolve__text_html_with_binary_format__maps_to_bytes(self, resolver, mock_context) -> None:
        """
        Scenario: Response with text/html but binary format in schema
        Expected Outcome: Maps to bytes type
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "text/html": IRSchema(type="string", format="binary"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.content_type_mapping is not None
        assert strategy.content_type_mapping["text/html"] == "bytes"

    def test_resolve__no_schema_for_content_type__defaults_to_bytes(self, resolver, mock_context) -> None:
        """
        Scenario: Content type with no schema defined
        Expected Outcome: Defaults to bytes type with warning
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "application/custom": None,  # No schema
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.content_type_mapping is not None
        # Should default to bytes for unknown content type
        assert strategy.content_type_mapping["application/custom"] == "bytes"

    def test_resolve__text_plain_without_schema__maps_to_str(self, resolver, mock_context) -> None:
        """
        Scenario: Response with text/plain but no schema defined
        Expected Outcome: Maps to str type (not bytes) - text content is naturally string-based
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "text/plain": None,  # No schema
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        # text/* without schema should default to str, not bytes
        assert strategy.return_type == "str"

    def test_resolve__text_csv_without_schema__maps_to_str(self, resolver, mock_context) -> None:
        """
        Scenario: Response with text/csv but no schema
        Expected Outcome: Maps to str type - text content defaults to string
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/json": resolver.schemas["DocumentResponse"],
                "text/csv": None,  # No schema
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.content_type_mapping is not None
        assert strategy.content_type_mapping["text/csv"] == "str"

    def test_resolve__empty_content_types__returns_none(self, resolver, mock_context) -> None:
        """
        Scenario: Response with empty content dict
        Expected Outcome: Returns None strategy
        """
        # Arrange
        response = IRResponse(
            status_code="204",
            description="No content",
            content={},  # Empty content
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        assert strategy.return_type == "None"
        assert strategy.response_schema is None

    def test_resolve__all_content_types_resolve_to_none__returns_none(self, resolver, mock_context) -> None:
        """
        Scenario: Multiple JSON content types but all resolve to None (schema resolution fails)
        Expected Outcome: Returns None strategy
        """

        # Arrange - Using a custom resolver that returns None for everything
        class NoneTypeResolver:
            def resolve_schema_type(self, schema, context, required=True):
                return None

        none_resolver = ResponseStrategyResolver({})
        none_resolver.type_service = NoneTypeResolver()

        response = IRResponse(
            status_code="200",
            description="Success",
            content={
                # Use JSON content types which require schema resolution
                # (text/* and binary types have special handling and bypass schema resolution)
                "application/json": IRSchema(type="object"),
                "application/vnd.api+json": IRSchema(type="object"),
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = none_resolver.resolve(operation, mock_context)

        # Assert
        # When no types can be resolved (schema resolution returns None), should return None
        assert strategy.return_type == "None"

    def test_resolve__unknown_content_type_with_schema__uses_schema(self, resolver, mock_context) -> None:
        """
        Scenario: Unknown content type but has a schema
        Expected Outcome: Uses schema type resolution
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "application/vnd.custom+json": resolver.schemas["DocumentResponse"],
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        # Unknown content type with schema should use schema resolution
        assert strategy.return_type == "DocumentResponse"

    def test_resolve__content_type_mapping__normalizes_to_lowercase(self, resolver, mock_context) -> None:
        """
        Scenario: Response with multiple content types (mixed case)
        Expected Outcome: content_type_mapping keys are normalized to lowercase for case-insensitive comparison
        """
        # Arrange
        response = IRResponse(
            status_code="200",
            description="Success response",
            content={
                "Application/JSON": resolver.schemas["DocumentResponse"],  # Mixed case
                "APPLICATION/PDF": IRSchema(type="string", format="binary"),  # All caps
            },
        )
        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            summary="Test operation",
            description="Test",
            responses=[response],
        )

        # Act
        strategy = resolver.resolve(operation, mock_context)

        # Assert
        # Generated code will normalize content-type to lowercase for comparison
        # The mapping stores original case, but generated code compares lowercase versions
        assert strategy.content_type_mapping is not None
        assert "Application/JSON" in strategy.content_type_mapping
        assert "APPLICATION/PDF" in strategy.content_type_mapping
        # The generated code will use .lower() on both sides of comparison
