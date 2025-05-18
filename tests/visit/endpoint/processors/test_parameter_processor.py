"""
Tests for the EndpointParameterProcessor class.
"""

from typing import Dict
from unittest.mock import MagicMock
from unittest.mock import patch
from pathlib import Path

import pytest

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRParameter, IRRequestBody, IRSchema
from pyopenapi_gen.visit.endpoint.processors.parameter_processor import EndpointParameterProcessor
from pyopenapi_gen.context.import_collector import ImportCollector


@pytest.fixture
def minimal_op_for_params() -> IROperation:
    return IROperation(
        path="/test/{path_param}",
        method=HTTPMethod.POST,
        operation_id="test_op_params",
        summary="Test Summary",
        description="Test Description",
        parameters=[
            IRParameter(name="query_param", param_in="query", required=True, schema=IRSchema(type="string")),
            IRParameter(name="path_param", param_in="path", required=True, schema=IRSchema(type="integer")),
        ],
        request_body=IRRequestBody(content={"application/json": IRSchema(type="object", name="MyBody")}, required=True),
        responses=[],
    )


@pytest.fixture
def render_context_mock_for_params(tmp_path: Path) -> MagicMock:
    mock_context = MagicMock(spec=RenderContext)
    # For NamedTypeResolver and TypeHelper to work when resolving requestBody schema
    # Provide dummy string paths for these, as their exact values are not critical
    # for testing the parameter processing logic itself, but their presence is.
    mock_context.overall_project_root = str(tmp_path)
    mock_context.package_root_for_generated_code = str(tmp_path / "test_pkg")  # e.g. /tmp/pytest.../test_pkg
    mock_context.core_package_name = "test_pkg.core"

    # If ImportCollector is accessed directly via context.import_collector
    # or through methods like add_import that use it.
    mock_context.import_collector = MagicMock(spec=ImportCollector)
    mock_context.import_collector._current_file_module_dot_path = (
        "some.dummy.path"  # Ensure this attribute exists for logging
    )

    # Mock methods of RenderContext if their full behavior isn't needed
    mock_context.add_import = MagicMock()
    # Ensure a plausible module path for current file if calculate_relative_path is involved
    mock_context.get_current_module_dot_path = MagicMock(return_value="test_pkg.endpoints.some_endpoint")
    mock_context.calculate_relative_path_for_internal_module = MagicMock(
        return_value=None
    )  # Simplifies if we don't test relative import generation here

    return mock_context


@pytest.fixture
def schemas_for_params() -> Dict[str, IRSchema]:
    return {
        "MyBody": IRSchema(type="object", name="MyBody", properties={"id": IRSchema(type="integer")}),
        "StringSchema": IRSchema(type="string"),  # For direct reference if needed
    }


class TestEndpointParameterProcessor:
    def test_process_parameters_basic(
        self,
        minimal_op_for_params: IROperation,
        render_context_mock_for_params: MagicMock,
        schemas_for_params: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario:
            - IROperation with path, query, and JSON body parameters.
        Expected Outcome:
            - Correctly ordered parameters (path, query, then body).
            - Correct types resolved (or mocked).
            - primary_content_type and resolved_body_type are correct for JSON.
        """
        processor = EndpointParameterProcessor(schemas=schemas_for_params)

        # Mock TypeHelper.get_python_type_for_schema behavior via context if needed or simplify
        # For this test, assume get_param_type and get_request_body_type return predictable strings
        # based on the simple IRSchema types provided.

        ordered_params, primary_content_type, resolved_body_type = processor.process_parameters(
            minimal_op_for_params, render_context_mock_for_params
        )

        assert len(ordered_params) == 3
        # Path param (path_param) should be present (TypeHelper would make it 'int')
        assert any(p["name"] == "path_param" and p["param_in"] == "path" for p in ordered_params)
        # Query param (query_param) (TypeHelper would make it 'str')
        assert any(p["name"] == "query_param" and p["param_in"] == "query" for p in ordered_params)
        # Body param (body)
        assert any(p["name"] == "body" and p["param_in"] == "body" for p in ordered_params)

        # Check specific types (assuming simple direct mapping or future mocking of TypeHelper)
        # This part might need adjustment based on actual TypeHelper behavior / mocking strategy
        path_param_info = next(p for p in ordered_params if p["name"] == "path_param")
        assert path_param_info["type"] == "int"  # Based on IRSchema(type="integer")

        query_param_info = next(p for p in ordered_params if p["name"] == "query_param")
        assert query_param_info["type"] == "str"  # Based on IRSchema(type="string")

        body_param_info = next(p for p in ordered_params if p["name"] == "body")
        assert body_param_info["type"] == "MyBody"  # Based on IRSchema(type="object", name="MyBody")

        assert primary_content_type == "application/json"
        assert resolved_body_type == "MyBody"

        # Check that path variables not in op.parameters are added
        op_missing_path_var = IROperation(
            path="/test/{path_param}/{another_path_var}",
            method=HTTPMethod.GET,
            operation_id="op_missing_path",
            summary="Missing Path Var Summary",
            description="Missing Path Var Description",
            parameters=[
                IRParameter(name="path_param", param_in="path", required=True, schema=IRSchema(type="integer")),
            ],
            responses=[],
        )
        ordered_params_missing, _, _ = processor.process_parameters(op_missing_path_var, render_context_mock_for_params)
        assert any(
            p["name"] == "another_path_var" and p["param_in"] == "path" and p["type"] == "str"
            for p in ordered_params_missing
        )
        assert len(ordered_params_missing) == 2

    def test_process_parameters__request_body_multipart_form_data__correct_types_and_imports(
        self,
        render_context_mock_for_params: MagicMock,
        schemas_for_params: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario:
            - IROperation with a multipart/form-data request body.
        Expected Outcome:
            - primary_content_type is "multipart/form-data".
            - resolved_body_type is "Dict[str, IO[Any]]".
            - A parameter named "files" with type "Dict[str, IO[Any]]" is generated.
            - Imports for "typing.Dict" and "typing.IO" are added.
        """
        op_multipart = IROperation(
            path="/upload",
            method=HTTPMethod.POST,
            operation_id="upload_file",
            summary="Upload a file",
            description="Uploads a file using multipart/form-data.",
            parameters=[],
            request_body=IRRequestBody(
                content={"multipart/form-data": IRSchema(type="object")},  # Schema details don't matter much here
                required=True,
            ),
            responses=[],
        )

        processor = EndpointParameterProcessor(schemas=schemas_for_params)
        ordered_params, primary_content_type, resolved_body_type = processor.process_parameters(
            op_multipart, render_context_mock_for_params
        )

        assert primary_content_type == "multipart/form-data"
        assert resolved_body_type == "Dict[str, IO[Any]]"

        files_param_info = next((p for p in ordered_params if p["name"] == "files"), None)
        assert files_param_info is not None
        assert files_param_info["type"] == "Dict[str, IO[Any]]"
        assert files_param_info["param_in"] == "body"
        assert files_param_info["required"] is True  # from op.request_body.required

        render_context_mock_for_params.add_import.assert_any_call("typing", "Dict")
        render_context_mock_for_params.add_import.assert_any_call("typing", "IO")
        # Check Any was also likely called for the default body type before specific one found
        render_context_mock_for_params.add_import.assert_any_call("typing", "Any")

    def test_process_parameters__with_header_parameter__processed_correctly(
        self,
        render_context_mock_for_params: MagicMock,
        schemas_for_params: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario:
            - IROperation with a header parameter.
        Expected Outcome:
            - The header parameter is included in ordered_params.
            - Its type is resolved, and other details are correct.
            - No special filtering occurs for generic headers.
        """
        op_with_header = IROperation(
            path="/test_headers",
            method=HTTPMethod.GET,
            operation_id="test_header_op",
            summary="Test Header Op",
            description="Operation with a header parameter.",
            parameters=[
                IRParameter(
                    name="X-Custom-Header",
                    param_in="header",
                    required=False,
                    schema=IRSchema(type="string", default="default_value"),
                ),
            ],
            responses=[],
        )

        processor = EndpointParameterProcessor(schemas=schemas_for_params)
        ordered_params, _, _ = processor.process_parameters(op_with_header, render_context_mock_for_params)

        assert len(ordered_params) == 1
        header_param_info = ordered_params[0]

        assert header_param_info["name"] == "x_custom_header"  # Sanitized
        assert header_param_info["original_name"] == "X-Custom-Header"
        assert header_param_info["param_in"] == "header"
        assert header_param_info["required"] is False
        # Assuming get_param_type for a string schema returns "str"
        # and handles default correctly if it were to be used by get_param_type mock directly.
        # For now, the mock setup for get_param_type is indirect via RenderContext.
        # We are testing that the attributes from IRParameter are passed to get_param_type implicitly.
        assert header_param_info["type"] == "Optional[str]"  # required=False makes it Optional
        assert header_param_info["default"] == "default_value"

        # Ensure get_param_type was called for this parameter
        # This is a bit tricky as get_param_type is not directly mocked on the processor instance.
        # It's called internally. We rely on the output (type, default) being correct.
        # If direct mocking of get_param_type was added to fixture, we could assert call.

    def test_process_parameters__with_cookie_parameter__processed_correctly(
        self,
        render_context_mock_for_params: MagicMock,
        schemas_for_params: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario:
            - IROperation with a cookie parameter.
        Expected Outcome:
            - The cookie parameter is included in ordered_params.
            - Its type is resolved, and other details (name, required, default) are correct.
        """
        op_with_cookie = IROperation(
            path="/test_cookies",
            method=HTTPMethod.GET,
            operation_id="test_cookie_op",
            summary="Test Cookie Op",
            description="Operation with a cookie parameter.",
            parameters=[
                IRParameter(name="Session-ID", param_in="cookie", required=True, schema=IRSchema(type="string")),
                IRParameter(
                    name="Theme-Preference",
                    param_in="cookie",
                    required=False,
                    schema=IRSchema(type="string", default="dark"),
                ),
            ],
            responses=[],
        )

        processor = EndpointParameterProcessor(schemas=schemas_for_params)
        ordered_params, _, _ = processor.process_parameters(op_with_cookie, render_context_mock_for_params)

        assert len(ordered_params) == 2

        session_id_param_info = next(p for p in ordered_params if p["original_name"] == "Session-ID")
        theme_param_info = next(p for p in ordered_params if p["original_name"] == "Theme-Preference")

        assert session_id_param_info["name"] == "session_id"  # Sanitized
        assert session_id_param_info["param_in"] == "cookie"
        assert session_id_param_info["required"] is True
        assert session_id_param_info["type"] == "str"  # Assuming get_param_type resolves this
        assert session_id_param_info["default"] is None  # No default in schema

        assert theme_param_info["name"] == "theme_preference"  # Sanitized
        assert theme_param_info["param_in"] == "cookie"
        assert theme_param_info["required"] is False
        assert theme_param_info["type"] == "Optional[str]"  # Assuming get_param_type resolves this
        assert theme_param_info["default"] == "dark"

    def test_process_parameters__request_body_form_urlencoded__correct_types_and_imports(
        self,
        render_context_mock_for_params: MagicMock,
        schemas_for_params: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario:
            - IROperation with an application/x-www-form-urlencoded request body.
        Expected Outcome:
            - primary_content_type is "application/x-www-form-urlencoded".
            - resolved_body_type is "Dict[str, Any]".
            - A parameter named "form_data" with type "Dict[str, Any]" is generated.
            - Imports for "typing.Dict" and "typing.Any" are added.
        """
        op_form_urlencoded = IROperation(
            path="/submit_form",
            method=HTTPMethod.POST,
            operation_id="submit_form_data",
            summary="Submit form data",
            description="Submits data using application/x-www-form-urlencoded.",
            parameters=[],
            request_body=IRRequestBody(
                content={"application/x-www-form-urlencoded": IRSchema(type="object")}, required=True
            ),
            responses=[],
        )

        processor = EndpointParameterProcessor(schemas=schemas_for_params)
        ordered_params, primary_content_type, resolved_body_type = processor.process_parameters(
            op_form_urlencoded, render_context_mock_for_params
        )

        assert primary_content_type == "application/x-www-form-urlencoded"
        assert resolved_body_type == "Dict[str, Any]"

        form_data_param_info = next((p for p in ordered_params if p["name"] == "form_data"), None)
        assert form_data_param_info is not None
        assert form_data_param_info["type"] == "Dict[str, Any]"
        assert form_data_param_info["param_in"] == "body"
        assert form_data_param_info["required"] is True

        render_context_mock_for_params.add_import.assert_any_call("typing", "Dict")
        # Any is added by default at the start of body processing, and also for Dict[str, Any]
        assert render_context_mock_for_params.add_import.call_count >= 1
        render_context_mock_for_params.add_import.assert_any_call("typing", "Any")

    def test_process_parameters__request_body_fallback_content_type__correct_types_and_imports(
        self,
        render_context_mock_for_params: MagicMock,
        schemas_for_params: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario:
            - IROperation with a fallback request body content type (e.g., application/octet-stream).
        Expected Outcome:
            - primary_content_type is the specified fallback type.
            - resolved_body_type is "bytes".
            - A parameter named "bytes_content" with type "bytes" is generated.
        """
        op_fallback_body = IROperation(
            path="/upload_binary",
            method=HTTPMethod.POST,
            operation_id="upload_binary_data",
            summary="Upload binary data",
            description="Uploads data using a generic content type.",
            parameters=[],
            request_body=IRRequestBody(
                content={
                    "application/octet-stream": IRSchema(type="string", format="binary")
                },  # Schema type/format here is illustrative
                required=True,
            ),
            responses=[],
        )

        processor = EndpointParameterProcessor(schemas=schemas_for_params)
        ordered_params, primary_content_type, resolved_body_type = processor.process_parameters(
            op_fallback_body, render_context_mock_for_params
        )

        assert primary_content_type == "application/octet-stream"
        assert resolved_body_type == "bytes"

        bytes_content_param_info = next((p for p in ordered_params if p["name"] == "bytes_content"), None)
        assert bytes_content_param_info is not None
        assert bytes_content_param_info["type"] == "bytes"
        assert bytes_content_param_info["param_in"] == "body"
        assert bytes_content_param_info["required"] is True

        # `typing.Any` would have been added at the start of body processing.
        render_context_mock_for_params.add_import.assert_any_call("typing", "Any")

    def test_process_parameters__body_param_name_collision__logs_warning(
        self,
        render_context_mock_for_params: MagicMock,
        schemas_for_params: Dict[str, IRSchema],
    ) -> None:
        """
        Scenario:
            - IROperation where a processed request body parameter name (e.g., "body")
              collides with an existing path, query, or header parameter name.
        Expected Outcome:
            - A warning is logged about the collision.
            - The original parameter is kept, and the colliding body parameter is not re-added.
        """
        op_colliding = IROperation(
            path="/test_collision",
            method=HTTPMethod.POST,
            operation_id="test_collision_op",
            summary="Test Collision Op",
            description="Test operation for parameter collision.",
            parameters=[IRParameter(name="body", param_in="query", required=True, schema=IRSchema(type="string"))],
            request_body=IRRequestBody(
                content={"application/json": IRSchema(type="object", name="MyRequestBody")}, required=True
            ),  # This will also try to generate a param named "body"
            responses=[],
        )

        processor = EndpointParameterProcessor(schemas=schemas_for_params)

        with patch("pyopenapi_gen.visit.endpoint.processors.parameter_processor.logger") as mock_logger:
            ordered_params, _, _ = processor.process_parameters(op_colliding, render_context_mock_for_params)

        mock_logger.warning.assert_called_once()
        # Check that the logged message contains key parts of the expected warning
        args, _ = mock_logger.warning.call_args
        assert "Request body parameter name 'body'" in args[0]
        assert "collides with an existing path/query/header parameter" in args[0]
        assert "test_collision_op" in args[0]

        # Ensure the original query param "body" is present
        assert len(ordered_params) == 1
        query_param_info = ordered_params[0]
        assert query_param_info["name"] == "body"
        assert query_param_info["param_in"] == "query"
        # The body parameter from request_body should not have been added again
