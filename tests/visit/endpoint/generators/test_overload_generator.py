"""
Tests for the OverloadMethodGenerator class.
"""

from unittest.mock import MagicMock, patch

import pytest

from pyopenapi_gen import IROperation, IRRequestBody, IRResponse
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy
from pyopenapi_gen.visit.endpoint.generators.overload_generator import OverloadMethodGenerator


@pytest.fixture
def op_single_content() -> IROperation:
    """Operation with single JSON content type."""
    return IROperation(
        path="/upload",
        method=HTTPMethod.POST,
        operation_id="upload_file",
        summary="Upload a file",
        description="Upload operation",
        parameters=[],
        request_body=IRRequestBody(
            description="File upload",
            required=True,
            content={"application/json": IRSchema(type="object", name="UploadRequest")},
        ),
        responses=[
            IRResponse(status_code="200", description="Success", content={"application/json": IRSchema(type="object")})
        ],
    )


@pytest.fixture
def op_multiple_content() -> IROperation:
    """Operation with multiple content types (JSON and multipart)."""
    return IROperation(
        path="/upload",
        method=HTTPMethod.POST,
        operation_id="upload_file",
        summary="Upload a file",
        description="Upload operation with multiple content types",
        parameters=[],
        request_body=IRRequestBody(
            description="File upload",
            required=True,
            content={
                "application/json": IRSchema(type="object", name="UploadRequest"),
                "multipart/form-data": IRSchema(type="object", name="FileUpload"),
            },
        ),
        responses=[
            IRResponse(status_code="200", description="Success", content={"application/json": IRSchema(type="object")})
        ],
    )


@pytest.fixture
def op_no_request_body() -> IROperation:
    """Operation without request body."""
    return IROperation(
        path="/get",
        method=HTTPMethod.GET,
        operation_id="get_data",
        summary="Get data",
        description="Get operation",
        parameters=[],
        request_body=None,
        responses=[
            IRResponse(status_code="200", description="Success", content={"application/json": IRSchema(type="object")})
        ],
    )


@pytest.fixture
def mock_render_context() -> RenderContext:
    """Provides a RenderContext mock."""
    mock = MagicMock(spec=RenderContext)
    mock.core_package_name = "test_core_pkg"
    mock.import_collector = MagicMock()
    mock.add_import = MagicMock()
    mock.add_plain_import = MagicMock()
    mock.add_typing_imports_for_type = MagicMock()
    return mock


@pytest.fixture
def mock_response_strategy() -> ResponseStrategy:
    """Provides a mock ResponseStrategy."""
    response_ir = IRResponse(
        status_code="200", description="Success", content={"application/json": IRSchema(type="object")}
    )
    return ResponseStrategy(
        return_type="UploadResponse",
        response_schema=IRSchema(type="object", name="UploadResponse"),
        is_streaming=False,
        response_ir=response_ir,
    )


@pytest.fixture
def schemas() -> dict[str, IRSchema]:
    """Basic schemas dictionary."""
    return {}


class TestHasMultipleContentTypes:
    def test_has_multiple_content_types__single_content__returns_false(
        self, op_single_content: IROperation, schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario: Operation with single JSON content type.
        Expected Outcome: Returns False, indicating no overloads needed.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.has_multiple_content_types(op_single_content)

        # Assert
        assert result is False

    def test_has_multiple_content_types__multiple_content__returns_true(
        self, op_multiple_content: IROperation, schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario: Operation with JSON and multipart content types.
        Expected Outcome: Returns True, indicating overloads should be generated.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.has_multiple_content_types(op_multiple_content)

        # Assert
        assert result is True

    def test_has_multiple_content_types__no_request_body__returns_false(
        self, op_no_request_body: IROperation, schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario: Operation without request body.
        Expected Outcome: Returns False, as there's no content type to overload.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.has_multiple_content_types(op_no_request_body)

        # Assert
        assert result is False


class TestGenerateOverloadSignatures:
    def test_generate_overload_signatures__single_content__returns_empty_list(
        self,
        op_single_content: IROperation,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation with single content type.
        Expected Outcome: Returns empty list, no overloads needed.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.generate_overload_signatures(op_single_content, mock_render_context, mock_response_strategy)

        # Assert
        assert result == []

    @patch(
        "pyopenapi_gen.visit.endpoint.generators.overload_generator.OverloadMethodGenerator._generate_single_overload"
    )
    def test_generate_overload_signatures__two_content_types__creates_two_overloads(
        self,
        mock_generate_single: MagicMock,
        op_multiple_content: IROperation,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation with JSON and multipart request body.
        Expected Outcome: Generates 2 @overload signatures with correct types.
        """
        # Arrange
        mock_generate_single.side_effect = [
            '@overload\nasync def upload_file(\n    self,\n    *,\n    body: UploadRequest,\n    content_type: Literal["application/json"] = "application/json"\n) -> UploadResponse: ...',
            '@overload\nasync def upload_file(\n    self,\n    *,\n    files: dict[str, IO[Any]],\n    content_type: Literal["multipart/form-data"] = "multipart/form-data"\n) -> UploadResponse: ...',
        ]

        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.generate_overload_signatures(
            op_multiple_content, mock_render_context, mock_response_strategy
        )

        # Assert
        assert len(result) == 2
        # Verify @overload decorator present in both
        assert "@overload" in result[0]
        assert "@overload" in result[1]
        # Verify async def present
        assert "async def upload_file(" in result[0]
        assert "async def upload_file(" in result[1]
        # Verify return type present
        assert "-> UploadResponse:" in result[0]
        assert "-> UploadResponse:" in result[1]

    @patch(
        "pyopenapi_gen.visit.endpoint.generators.overload_generator.OverloadMethodGenerator._generate_single_overload"
    )
    def test_generate_overload_signatures__imports_typing_modules(
        self,
        mock_generate_single: MagicMock,
        op_multiple_content: IROperation,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Generating overload signatures.
        Expected Outcome: Registers necessary typing imports (overload, Literal, IO, Any).
        """
        # Arrange
        mock_generate_single.return_value = "@overload\nasync def upload_file(...) -> UploadResponse: ..."

        generator = OverloadMethodGenerator(schemas)

        # Act
        generator.generate_overload_signatures(op_multiple_content, mock_render_context, mock_response_strategy)

        # Assert
        mock_render_context.add_import.assert_any_call("typing", "overload")
        mock_render_context.add_import.assert_any_call("typing", "Literal")
        mock_render_context.add_import.assert_any_call("typing", "IO")
        mock_render_context.add_import.assert_any_call("typing", "Any")

    def test_generate_overload_signatures__no_request_body__returns_empty_list(
        self,
        op_no_request_body: IROperation,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation without request body.
        Expected Outcome: Returns empty list, no overloads to generate.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.generate_overload_signatures(op_no_request_body, mock_render_context, mock_response_strategy)

        # Assert
        assert result == []


class TestGetContentTypeParamInfo:
    @patch("pyopenapi_gen.types.services.type_service.UnifiedTypeService.resolve_schema_type")
    def test_get_content_type_param_info__json_content__returns_body_param(
        self, mock_resolve_schema_type: MagicMock, mock_render_context: RenderContext, schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario: Content type is application/json.
        Expected Outcome: Returns parameter info with name='body' and resolved type from schema.
        """
        # Arrange
        mock_resolve_schema_type.return_value = "UploadRequest"

        generator = OverloadMethodGenerator(schemas)
        schema = IRSchema(type="object", name="UploadRequest")

        # Act
        result = generator._get_content_type_param_info("application/json", schema, mock_render_context)

        # Assert
        assert result["name"] == "body"
        assert result["type"] == "UploadRequest"
        mock_resolve_schema_type.assert_called_once_with(schema, mock_render_context, required=True)

    def test_get_content_type_param_info__multipart_content__returns_files_param(
        self, mock_render_context: RenderContext, schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario: Content type is multipart/form-data.
        Expected Outcome: Returns parameter info with name='files' and type='dict[str, IO[Any]]'.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)
        schema = IRSchema(type="object", name="FileUpload")

        # Act
        result = generator._get_content_type_param_info("multipart/form-data", schema, mock_render_context)

        # Assert
        assert result["name"] == "files"
        assert result["type"] == "dict[str, IO[Any]]"

    def test_get_content_type_param_info__form_urlencoded__returns_data_param(
        self, mock_render_context: RenderContext, schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario: Content type is application/x-www-form-urlencoded.
        Expected Outcome: Returns parameter info with name='data' and type='dict[str, str]'.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)
        schema = IRSchema(type="object", name="FormData")

        # Act
        result = generator._get_content_type_param_info(
            "application/x-www-form-urlencoded", schema, mock_render_context
        )

        # Assert
        assert result["name"] == "data"
        assert result["type"] == "dict[str, str]"

    def test_get_content_type_param_info__unknown_content__returns_body_with_any(
        self, mock_render_context: RenderContext, schemas: dict[str, IRSchema]
    ) -> None:
        """
        Scenario: Content type is unknown/unsupported.
        Expected Outcome: Returns parameter info with name='body' and type='Any', logs warning.
        """
        # Arrange
        generator = OverloadMethodGenerator(schemas)
        schema = IRSchema(type="object", name="UnknownData")

        # Act
        with patch("pyopenapi_gen.visit.endpoint.generators.overload_generator.logger") as mock_logger:
            result = generator._get_content_type_param_info("application/xml", schema, mock_render_context)

            # Assert
            assert result["name"] == "body"
            assert result["type"] == "Any"
            mock_logger.warning.assert_called_once()
            assert "Unknown content type" in str(mock_logger.warning.call_args)


class TestGenerateImplementationSignature:
    @patch("pyopenapi_gen.types.services.type_service.UnifiedTypeService.resolve_schema_type")
    def test_generate_implementation_signature__multiple_content__all_params_optional(
        self,
        mock_resolve_schema_type: MagicMock,
        op_multiple_content: IROperation,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation with JSON and multipart content types.
        Expected Outcome: Implementation signature has all content-type parameters as optional.
        """
        # Arrange
        mock_resolve_schema_type.return_value = "UploadRequest"

        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.generate_implementation_signature(
            op_multiple_content, mock_render_context, mock_response_strategy
        )

        # Assert
        # Verify async def present
        assert "async def upload_file(" in result
        # Verify return type
        assert "-> UploadResponse:" in result
        # Verify optional parameters (both body and files should have "| None = None")
        assert "body: UploadRequest | None = None" in result
        assert "files: dict[str, IO[Any]] | None = None" in result
        # Verify content_type parameter (no Literal, just str)
        assert 'content_type: str = "application/json"' in result

    @patch("pyopenapi_gen.types.services.type_service.UnifiedTypeService.resolve_schema_type")
    def test_generate_implementation_signature__no_duplicate_params(
        self,
        mock_resolve_schema_type: MagicMock,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation with multiple JSON content types (e.g., different schemas).
        Expected Outcome: Implementation signature avoids duplicate 'body' parameters.
        """
        # Arrange
        mock_resolve_schema_type.side_effect = ["UploadRequest", "AlternateRequest"]

        # Create operation with two JSON content types (different schemas)
        op = IROperation(
            path="/upload",
            method=HTTPMethod.POST,
            operation_id="upload_file",
            summary="Upload a file",
            description="Upload operation",
            parameters=[],
            request_body=IRRequestBody(
                description="File upload",
                required=True,
                content={
                    "application/json": IRSchema(type="object", name="UploadRequest"),
                    "application/json; charset=utf-8": IRSchema(type="object", name="AlternateRequest"),
                },
            ),
            responses=[
                IRResponse(
                    status_code="200", description="Success", content={"application/json": IRSchema(type="object")}
                )
            ],
        )

        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.generate_implementation_signature(op, mock_render_context, mock_response_strategy)

        # Assert
        # Count occurrences of 'body' parameter - should only appear once
        body_param_count = result.count("body:")
        assert body_param_count == 1


class TestGenerateSingleOverload:
    @patch("pyopenapi_gen.types.services.type_service.UnifiedTypeService.resolve_schema_type")
    def test_generate_single_overload__json_content__correct_signature(
        self,
        mock_resolve_schema_type: MagicMock,
        op_single_content: IROperation,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Generating single overload for JSON content type.
        Expected Outcome: @overload signature with body parameter and Literal content_type.
        """
        # Arrange
        mock_resolve_schema_type.return_value = "UploadRequest"

        generator = OverloadMethodGenerator(schemas)
        schema = IRSchema(type="object", name="UploadRequest")

        # Act
        result = generator._generate_single_overload(
            op_single_content, "application/json", schema, mock_render_context, mock_response_strategy
        )

        # Assert
        assert "@overload" in result
        assert "async def upload_file(" in result
        assert "body: UploadRequest" in result
        assert 'content_type: Literal["application/json"] = "application/json"' in result
        assert "-> UploadResponse: ..." in result

    def test_generate_single_overload__multipart_content__correct_signature(
        self,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Generating single overload for multipart content type.
        Expected Outcome: @overload signature with files parameter and Literal content_type.
        """
        # Arrange
        op = IROperation(
            path="/upload",
            method=HTTPMethod.POST,
            operation_id="upload_file",
            summary="Upload a file",
            description="Upload operation",
            parameters=[],
            request_body=IRRequestBody(
                description="File upload",
                required=True,
                content={"multipart/form-data": IRSchema(type="object", name="FileUpload")},
            ),
            responses=[
                IRResponse(
                    status_code="200", description="Success", content={"application/json": IRSchema(type="object")}
                )
            ],
        )

        generator = OverloadMethodGenerator(schemas)
        schema = IRSchema(type="object", name="FileUpload")

        # Act
        result = generator._generate_single_overload(
            op, "multipart/form-data", schema, mock_render_context, mock_response_strategy
        )

        # Assert
        assert "@overload" in result
        assert "async def upload_file(" in result
        assert "files: dict[str, IO[Any]]" in result
        assert 'content_type: Literal["multipart/form-data"] = "multipart/form-data"' in result
        assert "-> UploadResponse: ..." in result

    def test_generate_single_overload__camelcase_operation_id__converts_to_snake_case(
        self,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Operation ID is in camelCase (e.g., updateDocument)
        Expected Outcome: Generated method name should be snake_case (update_document)
        """
        # Arrange
        op = IROperation(
            path="/documents/{id}",
            method=HTTPMethod.PUT,
            operation_id="updateDocument",  # camelCase
            summary="Update a document",
            description="Update operation",
            parameters=[],
            request_body=IRRequestBody(
                description="Document update",
                required=True,
                content={"application/json": IRSchema(type="object", name="DocumentUpdate")},
            ),
            responses=[
                IRResponse(
                    status_code="200", description="Success", content={"application/json": IRSchema(type="object")}
                )
            ],
        )

        generator = OverloadMethodGenerator(schemas)
        schema = IRSchema(type="object", name="DocumentUpdate")

        # Act
        result = generator._generate_single_overload(
            op, "application/json", schema, mock_render_context, mock_response_strategy
        )

        # Assert - Method name should be converted to snake_case
        assert "async def update_document(" in result
        assert "async def updateDocument(" not in result

    def test_generate_implementation_signature__camelcase_operation_id__converts_to_snake_case(
        self,
        mock_render_context: RenderContext,
        mock_response_strategy: ResponseStrategy,
        schemas: dict[str, IRSchema],
    ) -> None:
        """
        Scenario: Implementation signature with camelCase operation ID
        Expected Outcome: Generated method name should be snake_case
        """
        # Arrange
        op = IROperation(
            path="/documents",
            method=HTTPMethod.POST,
            operation_id="createDocument",  # camelCase
            summary="Create a document",
            description="Create operation",
            parameters=[],
            request_body=IRRequestBody(
                description="Document creation",
                required=True,
                content={
                    "application/json": IRSchema(type="object", name="DocumentCreate"),
                    "multipart/form-data": IRSchema(type="object", name="FileUpload"),
                },
            ),
            responses=[
                IRResponse(
                    status_code="201", description="Created", content={"application/json": IRSchema(type="object")}
                )
            ],
        )

        generator = OverloadMethodGenerator(schemas)

        # Act
        result = generator.generate_implementation_signature(op, mock_render_context, mock_response_strategy)

        # Assert - Method name should be converted to snake_case
        assert "async def create_document(" in result
        assert "async def createDocument(" not in result
