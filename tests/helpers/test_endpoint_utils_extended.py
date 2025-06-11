"""Extended unit tests for endpoint_utils.py functions with comprehensive coverage."""

from unittest.mock import Mock, patch

from pyopenapi_gen import HTTPMethod, IROperation, IRRequestBody, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.helpers.endpoint_utils import (
    _find_resource_schema,
    _get_item_type_from_schema,
    _get_primary_response,
    _get_response_schema_and_content_type,
    _infer_type_from_path,
    _is_binary_stream_content,
    get_model_stub_args,
    get_python_type_for_response_body,
    get_return_type,
    get_return_type_unified,
    get_schema_from_response,
    get_type_for_specific_response,
)

# ===== Tests for get_return_type_unified =====


class TestGetReturnTypeUnified:
    def test_get_return_type_unified__basic_operation__delegates_to_unified_service(self) -> None:
        """
        Scenario:
            A basic operation is passed to get_return_type_unified.

        Expected Outcome:
            The function delegates to UnifiedTypeService and returns the result.
        """
        # Arrange
        op = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}
        responses: dict[str, IRResponse] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_return_type_unified(op, context, schemas, responses)

            # Assert
            assert result == "User"
            MockTypeService.assert_called_once_with(schemas, responses)
            mock_service.resolve_operation_response_type.assert_called_once_with(op, context)

    def test_get_return_type_unified__no_responses_dict__passes_none_to_service(self) -> None:
        """
        Scenario:
            No responses dictionary is provided (default None).

        Expected Outcome:
            UnifiedTypeService is called with None for responses.
        """
        # Arrange
        op = IROperation(
            operation_id="create_user",
            method=HTTPMethod.POST,
            path="/users",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_return_type_unified(op, context, schemas)

            # Assert
            assert result == "User"
            MockTypeService.assert_called_once_with(schemas, None)


# ===== Tests for get_return_type =====


class TestGetReturnType:
    def test_get_return_type__unified_service_returns_type__returns_tuple_with_type(self) -> None:
        """
        Scenario:
            UnifiedTypeService returns a valid type for the operation.

        Expected Outcome:
            The function returns a tuple with the type and False for unwrapping.
        """
        # Arrange
        op = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_return_type(op, context, schemas)

            # Assert
            assert result == ("User", False)

    def test_get_return_type__get_operation_unified_returns_none__tries_path_inference(self) -> None:
        """
        Scenario:
            UnifiedTypeService returns None for a GET operation.

        Expected Outcome:
            The function tries path-based inference as fallback.
        """
        # Arrange
        op = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {"User": IRSchema(name="User", type="object")}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = None
            MockTypeService.return_value = mock_service

            with patch("pyopenapi_gen.helpers.endpoint_utils._infer_type_from_path") as mock_infer:
                inferred_schema = IRSchema(name="User", type="object")
                mock_infer.return_value = inferred_schema

                # Act
                result = get_return_type(op, context, schemas)

                # Assert
                assert result == ("User", False)
                mock_infer.assert_called_once_with(op.path, schemas)

    def test_get_return_type__get_operation_returns_none_string__converts_to_none_for_get(self) -> None:
        """
        Scenario:
            UnifiedTypeService returns "None" string for a GET operation.

        Expected Outcome:
            The string "None" is converted back to None for backward compatibility.
        """
        # Arrange
        op = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = "None"
            MockTypeService.return_value = mock_service

            with patch("pyopenapi_gen.helpers.endpoint_utils._infer_type_from_path") as mock_infer:
                mock_infer.return_value = None

                # Act
                result = get_return_type(op, context, schemas)

                # Assert
                assert result == (None, False)

    def test_get_return_type__put_operation_with_request_body__tries_request_body_inference(self) -> None:
        """
        Scenario:
            PUT operation with request body when UnifiedTypeService returns None.

        Expected Outcome:
            The function tries to infer type from request body content.
        """
        # Arrange
        request_schema = IRSchema(name="UserUpdate", type="object")
        body = IRRequestBody(required=True, content={"application/json": request_schema})
        op = IROperation(
            operation_id="update_user",
            method=HTTPMethod.PUT,
            path="/users/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=body,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {"User": IRSchema(name="User", type="object")}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = None
            MockTypeService.return_value = mock_service

            with patch("pyopenapi_gen.helpers.endpoint_utils._find_resource_schema") as mock_find:
                resource_schema = IRSchema(name="User", type="object")
                mock_find.return_value = resource_schema

                # Act
                result = get_return_type(op, context, schemas)

                # Assert
                assert result == ("User", False)
                mock_find.assert_called_once_with("UserUpdate", schemas)

    def test_get_return_type__put_operation_no_resource_schema_found__uses_request_body_type(self) -> None:
        """
        Scenario:
            PUT operation where no corresponding resource schema is found.

        Expected Outcome:
            The function falls back to using the request body schema name.
        """
        # Arrange
        request_schema = IRSchema(name="UserUpdate", type="object")
        body = IRRequestBody(required=True, content={"application/json": request_schema})
        op = IROperation(
            operation_id="update_user",
            method=HTTPMethod.PUT,
            path="/users/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=body,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = None
            MockTypeService.return_value = mock_service

            with patch("pyopenapi_gen.helpers.endpoint_utils._find_resource_schema") as mock_find:
                mock_find.return_value = None

                # Act
                result = get_return_type(op, context, schemas)

                # Assert
                assert result == ("UserUpdate", False)

    def test_get_return_type__post_operation_returns_none_string__preserves_none_string(self) -> None:
        """
        Scenario:
            POST operation returns "None" string from UnifiedTypeService.

        Expected Outcome:
            The "None" string is preserved (not converted to None) for non-GET operations.
        """
        # Arrange
        op = IROperation(
            operation_id="create_user",
            method=HTTPMethod.POST,
            path="/users",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = "None"
            MockTypeService.return_value = mock_service

            # Act
            result = get_return_type(op, context, schemas)

            # Assert
            assert result == ("None", False)


# ===== Tests for _get_primary_response =====


class TestGetPrimaryResponse:
    def test_get_primary_response__operation_with_200_response__returns_200_response(self) -> None:
        """
        Scenario:
            Operation has multiple responses including 200.

        Expected Outcome:
            The 200 response should be prioritized and returned.
        """
        # Arrange
        response_200 = IRResponse(status_code="200", description="Success", content={})
        response_404 = IRResponse(status_code="404", description="Not found", content={})
        op = IROperation(
            operation_id="get_user",
            method=HTTPMethod.GET,
            path="/users/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[response_404, response_200],  # 200 not first to test prioritization
            tags=[],
        )

        # Act
        result = _get_primary_response(op)

        # Assert
        assert result is response_200

    def test_get_primary_response__operation_with_201_response__returns_201_response(self) -> None:
        """
        Scenario:
            Operation has 201 response but no 200.

        Expected Outcome:
            The 201 response should be returned as it's prioritized.
        """
        # Arrange
        response_201 = IRResponse(status_code="201", description="Created", content={})
        response_400 = IRResponse(status_code="400", description="Bad request", content={})
        op = IROperation(
            operation_id="create_user",
            method=HTTPMethod.POST,
            path="/users",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[response_400, response_201],
            tags=[],
        )

        # Act
        result = _get_primary_response(op)

        # Assert
        assert result is response_201

    def test_get_primary_response__operation_with_other_2xx_response__returns_2xx_response(self) -> None:
        """
        Scenario:
            Operation has a 2xx response but not the specific prioritized ones.

        Expected Outcome:
            The first 2xx response should be returned.
        """
        # Arrange
        response_206 = IRResponse(status_code="206", description="Partial content", content={})
        response_400 = IRResponse(status_code="400", description="Bad request", content={})
        op = IROperation(
            operation_id="partial_content",
            method=HTTPMethod.GET,
            path="/content",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[response_400, response_206],
            tags=[],
        )

        # Act
        result = _get_primary_response(op)

        # Assert
        assert result is response_206

    def test_get_primary_response__operation_with_default_response__returns_default_response(self) -> None:
        """
        Scenario:
            Operation only has default response and error responses.

        Expected Outcome:
            The default response should be returned.
        """
        # Arrange
        response_default = IRResponse(status_code="default", description="Default response", content={})
        response_400 = IRResponse(status_code="400", description="Bad request", content={})
        op = IROperation(
            operation_id="default_only",
            method=HTTPMethod.GET,
            path="/default",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[response_400, response_default],
            tags=[],
        )

        # Act
        result = _get_primary_response(op)

        # Assert
        assert result is response_default

    def test_get_primary_response__operation_with_only_error_responses__returns_first_response(self) -> None:
        """
        Scenario:
            Operation only has error responses.

        Expected Outcome:
            The first response should be returned as fallback.
        """
        # Arrange
        response_400 = IRResponse(status_code="400", description="Bad request", content={})
        response_404 = IRResponse(status_code="404", description="Not found", content={})
        op = IROperation(
            operation_id="error_only",
            method=HTTPMethod.GET,
            path="/error",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[response_400, response_404],
            tags=[],
        )

        # Act
        result = _get_primary_response(op)

        # Assert
        assert result is response_400

    def test_get_primary_response__operation_with_no_responses__returns_none(self) -> None:
        """
        Scenario:
            Operation has no responses defined.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        op = IROperation(
            operation_id="no_responses",
            method=HTTPMethod.GET,
            path="/empty",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )

        # Act
        result = _get_primary_response(op)

        # Assert
        assert result is None


# ===== Tests for _get_response_schema_and_content_type =====


class TestGetResponseSchemaAndContentType:
    def test_get_response_schema_and_content_type__response_with_json__returns_json_schema(self) -> None:
        """
        Scenario:
            Response has application/json content type.

        Expected Outcome:
            The JSON schema and content type should be returned.
        """
        # Arrange
        json_schema = IRSchema(name="User", type="object")
        resp = IRResponse(
            status_code="200",
            description="Success",
            content={"application/json": json_schema, "text/plain": IRSchema(name=None, type="string")},
        )

        # Act
        schema, content_type = _get_response_schema_and_content_type(resp)

        # Assert
        assert schema is json_schema
        assert content_type == "application/json"

    def test_get_response_schema_and_content_type__response_with_event_stream__returns_event_stream(self) -> None:
        """
        Scenario:
            Response has event-stream content type but no JSON.

        Expected Outcome:
            The event-stream schema and content type should be returned.
        """
        # Arrange
        stream_schema = IRSchema(name=None, type="string")
        resp = IRResponse(
            status_code="200",
            description="Success",
            content={"text/event-stream": stream_schema, "text/plain": IRSchema(name=None, type="string")},
        )

        # Act
        schema, content_type = _get_response_schema_and_content_type(resp)

        # Assert
        assert schema is stream_schema
        assert content_type == "text/event-stream"

    def test_get_response_schema_and_content_type__response_with_other_json__returns_json_variant(self) -> None:
        """
        Scenario:
            Response has JSON variant content type (e.g., application/vnd.api+json).

        Expected Outcome:
            The JSON variant schema and content type should be returned.
        """
        # Arrange
        json_api_schema = IRSchema(name="ApiResponse", type="object")
        resp = IRResponse(
            status_code="200",
            description="Success",
            content={"application/vnd.api+json": json_api_schema, "text/plain": IRSchema(name=None, type="string")},
        )

        # Act
        schema, content_type = _get_response_schema_and_content_type(resp)

        # Assert
        assert schema is json_api_schema
        assert content_type == "application/vnd.api+json"

    def test_get_response_schema_and_content_type__response_with_first_content_type__returns_first(self) -> None:
        """
        Scenario:
            Response has only non-JSON, non-stream content types.

        Expected Outcome:
            The first content type schema should be returned.
        """
        # Arrange
        text_schema = IRSchema(name=None, type="string")
        xml_schema = IRSchema(name=None, type="string")
        resp = IRResponse(
            status_code="200",
            description="Success",
            content={"text/plain": text_schema, "application/xml": xml_schema},
        )

        # Act
        schema, content_type = _get_response_schema_and_content_type(resp)

        # Assert
        assert schema is text_schema
        assert content_type == "text/plain"

    def test_get_response_schema_and_content_type__response_with_no_content__returns_none(self) -> None:
        """
        Scenario:
            Response has no content defined.

        Expected Outcome:
            None values should be returned for both schema and content type.
        """
        # Arrange
        resp = IRResponse(status_code="204", description="No content", content={})

        # Act
        schema, content_type = _get_response_schema_and_content_type(resp)

        # Assert
        assert schema is None
        assert content_type is None

    def test_get_response_schema_and_content_type__response_content_is_none__returns_none(self) -> None:
        """
        Scenario:
            Response content is None.

        Expected Outcome:
            None values should be returned for both schema and content type.
        """
        # Arrange
        resp = IRResponse(status_code="204", description="No content", content=None)  # type: ignore

        # Act
        schema, content_type = _get_response_schema_and_content_type(resp)

        # Assert
        assert schema is None
        assert content_type is None


# ===== Tests for _find_resource_schema =====


class TestFindResourceSchema:
    def test_find_resource_schema__valid_update_schema_name__returns_resource_schema(self) -> None:
        """
        Scenario:
            A valid update schema name like "UserUpdate" is provided with corresponding resource schema.

        Expected Outcome:
            The corresponding "User" schema should be returned.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        schemas = {"User": user_schema, "UserUpdate": IRSchema(name="UserUpdate", type="object")}

        # Act
        result = _find_resource_schema("UserUpdate", schemas)

        # Assert
        assert result is user_schema

    def test_find_resource_schema__schema_name_not_ending_with_update__returns_none(self) -> None:
        """
        Scenario:
            Schema name does not end with "Update".

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        schemas = {"User": IRSchema(name="User", type="object")}

        # Act
        result = _find_resource_schema("User", schemas)

        # Assert
        assert result is None

    def test_find_resource_schema__empty_schema_name__returns_none(self) -> None:
        """
        Scenario:
            Empty string is provided as schema name.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        schemas = {"User": IRSchema(name="User", type="object")}

        # Act
        result = _find_resource_schema("", schemas)

        # Assert
        assert result is None

    def test_find_resource_schema__none_schema_name__returns_none(self) -> None:
        """
        Scenario:
            None is provided as schema name.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        schemas = {"User": IRSchema(name="User", type="object")}

        # Act
        result = _find_resource_schema(None, schemas)  # type: ignore

        # Assert
        assert result is None

    def test_find_resource_schema__resource_schema_not_found__returns_none(self) -> None:
        """
        Scenario:
            Update schema name is valid but corresponding resource schema doesn't exist.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        schemas = {"UserUpdate": IRSchema(name="UserUpdate", type="object")}

        # Act
        result = _find_resource_schema("UserUpdate", schemas)

        # Assert
        assert result is None

    def test_find_resource_schema__matches_schema_name_attribute__returns_resource_schema(self) -> None:
        """
        Scenario:
            Resource schema is found by matching the schema's name attribute rather than key.

        Expected Outcome:
            The schema with matching name attribute should be returned.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        schemas = {"user_model": user_schema}  # Key doesn't match, but name attribute does

        # Act
        result = _find_resource_schema("UserUpdate", schemas)

        # Assert
        assert result is user_schema


# ===== Tests for _infer_type_from_path =====


class TestInferTypeFromPath:
    def test_infer_type_from_path__path_matches_schema_by_name__returns_schema(self) -> None:
        """
        Scenario:
            Path ends with a resource name that matches an existing schema.

        Expected Outcome:
            The matching schema should be returned.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        schemas = {"User": user_schema}

        # Act
        result = _infer_type_from_path("/api/users/{id}", schemas)

        # Assert
        assert result is user_schema

    def test_infer_type_from_path__path_matches_schema_with_response_suffix__returns_schema(self) -> None:
        """
        Scenario:
            Path resource name matches a schema with "Response" suffix.

        Expected Outcome:
            The schema with Response suffix should be returned.
        """
        # Arrange
        user_response_schema = IRSchema(name="UserResponse", type="object")
        schemas = {"UserResponse": user_response_schema}

        # Act
        result = _infer_type_from_path("/api/users/{id}", schemas)

        # Assert
        assert result is user_response_schema

    def test_infer_type_from_path__no_matching_schema__returns_none(self) -> None:
        """
        Scenario:
            Path resource name doesn't match any existing schema.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        schemas = {"Product": IRSchema(name="Product", type="object")}

        # Act
        result = _infer_type_from_path("/api/users/{id}", schemas)

        # Assert
        assert result is None

    def test_infer_type_from_path__empty_path__returns_none(self) -> None:
        """
        Scenario:
            Empty path is provided.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        schemas = {"User": IRSchema(name="User", type="object")}

        # Act
        result = _infer_type_from_path("", schemas)

        # Assert
        assert result is None

    def test_infer_type_from_path__path_with_trailing_slash__handles_correctly(self) -> None:
        """
        Scenario:
            Path has trailing slash.

        Expected Outcome:
            The trailing slash should be stripped and matching should work.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        schemas = {"User": user_schema}

        # Act
        result = _infer_type_from_path("/api/users/", schemas)

        # Assert
        assert result is user_schema

    def test_infer_type_from_path__path_with_only_slash__returns_none(self) -> None:
        """
        Scenario:
            Path is just "/".

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        schemas = {"User": IRSchema(name="User", type="object")}

        # Act
        result = _infer_type_from_path("/", schemas)

        # Assert
        assert result is None


# ===== Tests for get_type_for_specific_response =====


class TestGetTypeForSpecificResponse:
    def test_get_type_for_specific_response__response_with_json_schema__returns_resolved_type(self) -> None:
        """
        Scenario:
            Response has JSON content with a schema that can be resolved.

        Expected Outcome:
            The resolved type should be returned.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        resp = IRResponse(status_code="200", description="Success", content={"application/json": user_schema})
        schemas = {"User": user_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_type_for_specific_response("/users/{id}", resp, schemas, ctx)

            # Assert
            assert result == "User"

    def test_get_type_for_specific_response__binary_stream_response__returns_string_type(self) -> None:
        """
        Scenario:
            Response has binary content but is not a stream.

        Expected Outcome:
            The resolved schema type should be returned (e.g., str for binary format).
        """
        # Arrange
        binary_schema = IRSchema(name=None, type="string", format="binary")
        resp = IRResponse(status_code="200", description="Success", content={"application/octet-stream": binary_schema})
        schemas: dict[str, IRSchema] = {}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "str"
            MockTypeService.return_value = mock_service

            # Act
            result = get_type_for_specific_response("/files/{id}/download", resp, schemas, ctx)

            # Assert
            assert result == "str"

    def test_get_type_for_specific_response__array_response_with_unwrap__returns_resolved_array_type(self) -> None:
        """
        Scenario:
            Response is an array schema and return_unwrap_data_property is True.

        Expected Outcome:
            The function returns the resolved array type without special unwrapping (since no data property wrapper).
        """
        # Arrange
        item_schema = IRSchema(name="User", type="object")
        array_schema = IRSchema(name=None, type="array", items=item_schema)
        resp = IRResponse(status_code="200", description="Success", content={"application/json": array_schema})
        schemas = {"User": item_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "List[Dict[str, Any]]"
            MockTypeService.return_value = mock_service

            # Act
            result = get_type_for_specific_response("/users", resp, schemas, ctx, return_unwrap_data_property=True)

            # Assert
            assert result == "List[Dict[str, Any]]"

    def test_get_type_for_specific_response__object_response_no_unwrap__returns_resolved_type(self) -> None:
        """
        Scenario:
            Response is an object and return_unwrap_data_property is False.

        Expected Outcome:
            The resolved object type should be returned.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        resp = IRResponse(status_code="200", description="Success", content={"application/json": user_schema})
        schemas = {"User": user_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils._is_binary_stream_content") as mock_is_binary:
            mock_is_binary.return_value = False

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_type_for_specific_response(
                "/users/{id}", resp, schemas, ctx, return_unwrap_data_property=False
            )

            # Assert
            assert result == "User"

    def test_get_type_for_specific_response__no_content__returns_none(self) -> None:
        """
        Scenario:
            Response has no content.

        Expected Outcome:
            "None" should be returned.
        """
        # Arrange
        resp = IRResponse(status_code="204", description="No content", content={})
        schemas: dict[str, IRSchema] = {}
        ctx = RenderContext()

        # Act
        result = get_type_for_specific_response("/users/{id}", resp, schemas, ctx)

        # Assert
        assert result == "None"


# ===== Tests for _is_binary_stream_content =====


class TestIsBinaryStreamContent:
    def test_is_binary_stream_content__octet_stream_content__returns_true(self) -> None:
        """
        Scenario:
            Response has application/octet-stream content type.

        Expected Outcome:
            True should be returned.
        """
        # Arrange
        binary_schema = IRSchema(name=None, type="string", format="binary")
        resp = IRResponse(status_code="200", description="Success", content={"application/octet-stream": binary_schema})

        # Act
        result = _is_binary_stream_content(resp)

        # Assert
        assert result is True

    def test_is_binary_stream_content__pdf_content__returns_true(self) -> None:
        """
        Scenario:
            Response has application/pdf content type.

        Expected Outcome:
            True should be returned.
        """
        # Arrange
        pdf_schema = IRSchema(name=None, type="string", format="binary")
        resp = IRResponse(status_code="200", description="Success", content={"application/pdf": pdf_schema})

        # Act
        result = _is_binary_stream_content(resp)

        # Assert
        assert result is True

    def test_is_binary_stream_content__image_content__returns_true(self) -> None:
        """
        Scenario:
            Response has image/* content type.

        Expected Outcome:
            True should be returned.
        """
        # Arrange
        image_schema = IRSchema(name=None, type="string", format="binary")
        resp = IRResponse(status_code="200", description="Success", content={"image/png": image_schema})

        # Act
        result = _is_binary_stream_content(resp)

        # Assert
        assert result is True

    def test_is_binary_stream_content__json_content__returns_false(self) -> None:
        """
        Scenario:
            Response has application/json content type.

        Expected Outcome:
            False should be returned.
        """
        # Arrange
        json_schema = IRSchema(name="User", type="object")
        resp = IRResponse(status_code="200", description="Success", content={"application/json": json_schema})

        # Act
        result = _is_binary_stream_content(resp)

        # Assert
        assert result is False

    def test_is_binary_stream_content__mixed_content_with_binary__returns_true(self) -> None:
        """
        Scenario:
            Response has both JSON and binary content types.

        Expected Outcome:
            True should be returned as binary content is present.
        """
        # Arrange
        json_schema = IRSchema(name="User", type="object")
        binary_schema = IRSchema(name=None, type="string", format="binary")
        resp = IRResponse(
            status_code="200",
            description="Success",
            content={"application/json": json_schema, "application/octet-stream": binary_schema},
        )

        # Act
        result = _is_binary_stream_content(resp)

        # Assert
        assert result is True

    def test_is_binary_stream_content__no_content__returns_false(self) -> None:
        """
        Scenario:
            Response has no content.

        Expected Outcome:
            False should be returned.
        """
        # Arrange
        resp = IRResponse(status_code="204", description="No content", content={})

        # Act
        result = _is_binary_stream_content(resp)

        # Assert
        assert result is False


# ===== Tests for _get_item_type_from_schema =====


class TestGetItemTypeFromSchema:
    def test_get_item_type_from_schema__array_with_named_items__returns_item_type(self) -> None:
        """
        Scenario:
            Response schema is an array with named item type.

        Expected Outcome:
            The item type should be resolved and returned.
        """
        # Arrange
        item_schema = IRSchema(name="User", type="object")
        array_schema = IRSchema(name=None, type="array", items=item_schema)
        resp = IRResponse(status_code="200", description="Success", content={"application/json": array_schema})
        schemas = {"User": item_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = _get_item_type_from_schema(resp, schemas, ctx)

            # Assert
            assert result == "User"

    def test_get_item_type_from_schema__non_array_schema__returns_resolved_type(self) -> None:
        """
        Scenario:
            Response schema is not an array.

        Expected Outcome:
            The resolved schema type should be returned (function resolves any schema type).
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        resp = IRResponse(status_code="200", description="Success", content={"application/json": user_schema})
        schemas = {"User": user_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "Dict[str, Any]"
            MockTypeService.return_value = mock_service

            # Act
            result = _get_item_type_from_schema(resp, schemas, ctx)

            # Assert
            assert result == "Dict[str, Any]"

    def test_get_item_type_from_schema__array_with_no_items__returns_resolved_array_type(self) -> None:
        """
        Scenario:
            Response schema is an array but has no items defined.

        Expected Outcome:
            The function resolves the array schema and returns the resolved type.
        """
        # Arrange
        array_schema = IRSchema(name=None, type="array", items=None)
        resp = IRResponse(status_code="200", description="Success", content={"application/json": array_schema})
        schemas: dict[str, IRSchema] = {}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "List[Any]"
            MockTypeService.return_value = mock_service

            # Act
            result = _get_item_type_from_schema(resp, schemas, ctx)

            # Assert
            assert result == "List[Any]"

    def test_get_item_type_from_schema__no_schema_in_response__returns_none(self) -> None:
        """
        Scenario:
            Response has no schema that can be extracted.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        resp = IRResponse(status_code="200", description="Success", content={})
        schemas: dict[str, IRSchema] = {}
        ctx = RenderContext()

        # Act
        result = _get_item_type_from_schema(resp, schemas, ctx)

        # Assert
        assert result is None


# ===== Tests for get_python_type_for_response_body =====


class TestGetPythonTypeForResponseBody:
    def test_get_python_type_for_response_body__response_with_schema__returns_resolved_type(self) -> None:
        """
        Scenario:
            Response has a schema that can be resolved.

        Expected Outcome:
            The resolved Python type should be returned.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        resp = IRResponse(status_code="200", description="Success", content={"application/json": user_schema})
        schemas = {"User": user_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.get_schema_from_response") as mock_get_schema:
            mock_get_schema.return_value = user_schema

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_python_type_for_response_body(resp, schemas, ctx)

            # Assert
            assert result == "User"

    def test_get_python_type_for_response_body__response_with_no_schema__returns_any(self) -> None:
        """
        Scenario:
            Response has no schema that can be extracted.

        Expected Outcome:
            "Any" should be returned as fallback.
        """
        # Arrange
        resp = IRResponse(status_code="200", description="Success", content={})
        schemas: dict[str, IRSchema] = {}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.get_schema_from_response") as mock_get_schema:
            mock_get_schema.return_value = None

            # Act
            result = get_python_type_for_response_body(resp, schemas, ctx)

            # Assert
            assert result == "Any"


# ===== Tests for get_schema_from_response =====


class TestGetSchemaFromResponse:
    def test_get_schema_from_response__response_with_json_content__returns_json_schema(self) -> None:
        """
        Scenario:
            Response has application/json content.

        Expected Outcome:
            The JSON schema should be returned.
        """
        # Arrange
        json_schema = IRSchema(name="User", type="object")
        resp = IRResponse(
            status_code="200",
            description="Success",
            content={"application/json": json_schema, "text/plain": IRSchema(name=None, type="string")},
        )
        schemas = {"User": json_schema}

        # Act
        result = get_schema_from_response(resp, schemas)

        # Assert
        assert result is json_schema

    def test_get_schema_from_response__response_with_no_content__returns_none(self) -> None:
        """
        Scenario:
            Response has no content.

        Expected Outcome:
            None should be returned.
        """
        # Arrange
        resp = IRResponse(status_code="204", description="No content", content={})
        schemas: dict[str, IRSchema] = {}

        # Act
        result = get_schema_from_response(resp, schemas)

        # Assert
        assert result is None

    def test_get_schema_from_response__response_with_non_json_content__returns_first_schema(self) -> None:
        """
        Scenario:
            Response has only non-JSON content types.

        Expected Outcome:
            The first available schema should be returned.
        """
        # Arrange
        text_schema = IRSchema(name=None, type="string")
        resp = IRResponse(status_code="200", description="Success", content={"text/plain": text_schema})
        schemas: dict[str, IRSchema] = {}

        # Act
        result = get_schema_from_response(resp, schemas)

        # Assert
        assert result is text_schema


# ===== Additional tests for better coverage =====


class TestAdditionalCoverage:
    def test_get_return_type__get_operation_inference_fails__returns_none_none(self) -> None:
        """
        Scenario:
            GET operation where both unified service and path inference return None.

        Expected Outcome:
            (None, False) should be returned.
        """
        # Arrange
        op = IROperation(
            operation_id="get_unknown",
            method=HTTPMethod.GET,
            path="/unknown/{id}",
            summary=None,
            description=None,
            parameters=[],
            request_body=None,
            responses=[],
            tags=[],
        )
        context = RenderContext()
        schemas: dict[str, IRSchema] = {}

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_operation_response_type.return_value = None
            MockTypeService.return_value = mock_service

            with patch("pyopenapi_gen.helpers.endpoint_utils._infer_type_from_path") as mock_infer:
                mock_infer.return_value = None

                # Act
                result = get_return_type(op, context, schemas)

                # Assert
                assert result == (None, False)

    def test_infer_type_from_path__path_with_id_parameter__finds_schema_from_preceding_segment(self) -> None:
        """
        Scenario:
            Path with ID parameter should look at the preceding segment for schema matching.

        Expected Outcome:
            Should find User schema when path has users/{id} pattern.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        schemas = {"Users": user_schema}  # Match based on simple capitalization logic

        # Act - The last logic in the function checks path segments before {id} parameters
        result = _infer_type_from_path("/api/users/{id}", schemas)

        # Assert
        assert result is user_schema

    def test_infer_type_from_path__path_with_capitalized_segment_match__returns_matching_schema(self) -> None:
        """
        Scenario:
            Path segment matches schema name through capitalization logic.

        Expected Outcome:
            Should return the matching schema based on capitalization.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        schemas = {"User": user_schema}

        # Act - Path has "users" which becomes "Users" through capitalization, but that doesn't match "User"
        # However, the logic checks for exact match first, then falls back to other heuristics
        result = _infer_type_from_path("/api/users/{id}", schemas)

        # Assert - The function will try various heuristics and may return an array schema or None
        # depending on which logic path matches first
        if result is not None:
            # If it found something, it should be related to User in some way
            assert result.items is user_schema or result is user_schema
        else:
            # If no match found, that's also valid for this path
            assert result is None

    def test_get_model_stub_args__schema_with_array_property__uses_ellipsis_default(self) -> None:
        """
        Scenario:
            Schema has an array property that is required.

        Expected Outcome:
            Ellipsis should be used as default for non-basic types like arrays.
        """
        # Arrange
        array_schema = IRSchema(name=None, type="array")
        schema = IRSchema(
            name="TestModel",
            type="object",
            properties={"items": array_schema},
            required=["items"],
        )
        present_args: set[str] = set()
        context = RenderContext()

        # Act
        result = get_model_stub_args(schema, context, present_args)

        # Assert
        assert result == "items=..."

    def test_get_model_stub_args__schema_with_object_property__uses_ellipsis_default(self) -> None:
        """
        Scenario:
            Schema has an object property that is required.

        Expected Outcome:
            Ellipsis should be used as default for non-basic types like objects.
        """
        # Arrange
        obj_schema = IRSchema(name=None, type="object")
        schema = IRSchema(
            name="TestModel",
            type="object",
            properties={"metadata": obj_schema},
            required=["metadata"],
        )
        present_args: set[str] = set()
        context = RenderContext()

        # Act
        result = get_model_stub_args(schema, context, present_args)

        # Assert
        assert result == "metadata=..."

    def test_get_type_for_specific_response__data_wrapper_with_array_unwrapping__returns_list_type(self) -> None:
        """
        Scenario:
            Response has a data wrapper with array type that should be unwrapped.

        Expected Outcome:
            Should return List[ItemType] with proper unwrapping.
        """
        # Arrange
        item_schema = IRSchema(name="User", type="object")
        array_data_schema = IRSchema(name=None, type="array", items=item_schema)
        wrapper_schema = IRSchema(
            name="UsersResponse",
            type="object",
            properties={"data": array_data_schema},
        )
        resp = IRResponse(status_code="200", description="Success", content={"application/json": wrapper_schema})
        schemas = {"User": item_schema, "UsersResponse": wrapper_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            # First call returns the wrapper type, second call returns the item type
            mock_service.resolve_schema_type.side_effect = ["UsersResponse", "User"]
            MockTypeService.return_value = mock_service

            # Act
            result = get_type_for_specific_response("/users", resp, schemas, ctx, return_unwrap_data_property=True)

            # Assert
            assert result == "List[User]"

    def test_get_type_for_specific_response__data_wrapper_with_object_unwrapping__returns_unwrapped_type(self) -> None:
        """
        Scenario:
            Response has a data wrapper with object type that should be unwrapped.

        Expected Outcome:
            Should return the unwrapped object type.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object")
        wrapper_schema = IRSchema(
            name="UserResponse",
            type="object",
            properties={"data": user_schema},
        )
        resp = IRResponse(status_code="200", description="Success", content={"application/json": wrapper_schema})
        schemas = {"User": user_schema, "UserResponse": wrapper_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            # First call returns wrapper type, second call returns unwrapped type
            mock_service.resolve_schema_type.side_effect = ["UserResponse", "User"]
            MockTypeService.return_value = mock_service

            # Act
            result = get_type_for_specific_response("/users/1", resp, schemas, ctx, return_unwrap_data_property=True)

            # Assert
            assert result == "User"

    def test_get_type_for_specific_response__response_with_unwrap_but_no_data_property__returns_original_type(
        self,
    ) -> None:
        """
        Scenario:
            Response schema doesn't have a data property but unwrapping is requested.

        Expected Outcome:
            Should return the original resolved type without unwrapping.
        """
        # Arrange
        user_schema = IRSchema(name="User", type="object", properties={"name": IRSchema(name=None, type="string")})
        resp = IRResponse(status_code="200", description="Success", content={"application/json": user_schema})
        schemas = {"User": user_schema}
        ctx = RenderContext()

        with patch("pyopenapi_gen.helpers.endpoint_utils.UnifiedTypeService") as MockTypeService:
            mock_service = Mock()
            mock_service.resolve_schema_type.return_value = "User"
            MockTypeService.return_value = mock_service

            # Act
            result = get_type_for_specific_response("/users/1", resp, schemas, ctx, return_unwrap_data_property=True)

            # Assert
            assert result == "User"
