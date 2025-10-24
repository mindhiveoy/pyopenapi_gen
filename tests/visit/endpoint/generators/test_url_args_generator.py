from typing import Any, List
from unittest.mock import MagicMock, call, patch

import pytest

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRParameter, IRSchema
from pyopenapi_gen.visit.endpoint.generators.url_args_generator import EndpointUrlArgsGenerator


@pytest.fixture
def render_context_mock() -> MagicMock:
    mock = MagicMock(spec=RenderContext)
    mock.core_package_name = "test_core"
    return mock


@pytest.fixture
def code_writer_mock() -> MagicMock:
    return MagicMock(spec=CodeWriter)


@pytest.fixture
def url_args_generator() -> EndpointUrlArgsGenerator:
    return EndpointUrlArgsGenerator()


class TestEndpointUrlArgsGenerator:
    def test_generate_url_and_args_basic_get(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test basic GET operation with no parameters."""
        operation = IROperation(
            operation_id="get_items",
            summary="Get all items",
            description="Retrieves a list of all items.",
            method=HTTPMethod.GET,
            path="/items",
            tags=["items"],
            parameters=[],
            request_body=None,
            responses=[],
        )
        ordered_parameters: List[dict[str, Any]] = []

        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            None,  # primary_content_type
            None,  # resolved_body_type
        )
        expected_calls = [
            call('url = f"{self.base_url}/items"'),
            call(""),
        ]
        code_writer_mock.write_line.assert_has_calls(expected_calls, any_order=False)

        # Check return value
        returned_value = url_args_generator.generate_url_and_args(
            code_writer_mock,  # Re-call to get return value, mock calls will be duplicated but assertions are specific
            operation,
            render_context_mock,
            ordered_parameters,
            None,
            None,
        )
        assert not returned_value, "generate_url_and_args should return False when no headers are written."

        calls = code_writer_mock.write_line.call_args_list
        params_written = any("params: dict[str, Any] = {" in c[0][0] for c in calls)
        headers_written = any("headers: dict[str, Any] = {" in c[0][0] for c in calls)

        assert not params_written, "Params dict should not have been written for a basic GET with no query params."
        assert not headers_written, "Headers dict should not have been written for a basic GET with no header params."

    def test_generate_url_and_args_with_path_params(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test operation with path parameters."""
        path_param_info: dict[str, Any] = {
            "name": "item_id",
            "param_in": "path",
            "required": True,
            "original_name": "item_id",
        }
        operation = IROperation(
            operation_id="get_item_by_id",
            summary="Get item by ID",
            description="Retrieves a specific item by its ID.",
            method=HTTPMethod.GET,
            path="/items/{item_id}",
            tags=["items"],
            parameters=[
                IRParameter(
                    name="item_id",
                    param_in="path",
                    required=True,
                    schema=IRSchema(type="integer", format="int64", is_nullable=False),
                    description="ID of the item",
                )
            ],
            request_body=None,
            responses=[],
        )

        with patch(
            "pyopenapi_gen.core.utils.NameSanitizer.sanitize_method_name", return_value="item_id_sanitized"
        ) as mock_sanitize:
            url_args_generator.generate_url_and_args(
                code_writer_mock, operation, render_context_mock, [path_param_info], None, None
            )
            code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/items/{{item_id_sanitized}}"')
            mock_sanitize.assert_called_with("item_id")

    def test_generate_url_and_args_with_query_params(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test operation with query parameters."""
        query_param_dict: dict[str, Any] = {
            "name": "filter_by",
            "param_in": "query",
            "required": False,
            "original_name": "filterBy",
            "schema": IRSchema(type="string", is_nullable=True),
        }
        operation = IROperation(
            operation_id="list_items_filtered",
            summary="List items with filter",
            description="Retrieves items based on a filter.",
            method=HTTPMethod.GET,
            path="/items",
            tags=["items"],
            parameters=[
                IRParameter(
                    name="filterBy",
                    param_in="query",
                    required=False,
                    schema=IRSchema(type="string", is_nullable=True),
                    description="Filter criteria",
                )
            ],
            request_body=None,
            responses=[],
        )

        with patch(
            "pyopenapi_gen.core.utils.NameSanitizer.sanitize_method_name", side_effect=lambda name: name
        ) as mock_sanitize_query:
            url_args_generator.generate_url_and_args(
                code_writer_mock, operation, render_context_mock, [query_param_dict], None, None
            )

            code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/items"')
            code_writer_mock.write_line.assert_any_call("params: dict[str, Any] = {")
            code_writer_mock.write_line.assert_any_call(
                '    **({"filterBy": DataclassSerializer.serialize(filter_by)} if filter_by is not None else {}),'
            )
            mock_sanitize_query.assert_any_call("filter_by")
            render_context_mock.add_import.assert_any_call("typing", "Any")

    def test_generate_url_and_args_with_header_params(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test operation with header parameters."""
        header_param_required_dict: dict[str, Any] = {
            "name": "x_request_id",
            "param_in": "header",
            "required": True,
            "original_name": "X-Request-ID",
            "schema": IRSchema(type="string", is_nullable=False),
        }
        header_param_optional_dict: dict[str, Any] = {
            "name": "x_client_version",
            "param_in": "header",
            "required": False,
            "original_name": "X-Client-Version",
            "schema": IRSchema(type="string", is_nullable=True),
        }
        operation = IROperation(
            operation_id="create_item_with_headers",
            summary="Create item with custom headers",
            description="Creates an item, expecting specific headers.",
            method=HTTPMethod.POST,
            path="/items_with_headers",
            tags=["items"],
            parameters=[
                IRParameter(
                    name="X-Request-ID",
                    param_in="header",
                    required=True,
                    schema=IRSchema(type="string", is_nullable=False),
                    description="Request ID",
                ),
                IRParameter(
                    name="X-Client-Version",
                    param_in="header",
                    required=False,
                    schema=IRSchema(type="string", is_nullable=True),
                    description="Client version",
                ),
            ],
            request_body=None,
            responses=[],
        )
        ordered_parameters = [header_param_required_dict, header_param_optional_dict]

        def mock_sanitize_name(name: str) -> str:
            if name == "x_request_id":
                return "x_request_id"
            if name == "x_client_version":
                return "x_client_version"
            return name

        with patch(
            "pyopenapi_gen.core.utils.NameSanitizer.sanitize_method_name", side_effect=mock_sanitize_name
        ) as mock_sanitize_header_method_name:
            # Capture return value
            returned_value = url_args_generator.generate_url_and_args(
                code_writer_mock, operation, render_context_mock, ordered_parameters, None, None
            )

        assert returned_value, "generate_url_and_args should return True when headers are written."

        code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/items_with_headers"')
        code_writer_mock.write_line.assert_any_call("headers: dict[str, Any] = {")
        code_writer_mock.write_line.assert_any_call('    "X-Request-ID": DataclassSerializer.serialize(x_request_id),')
        code_writer_mock.write_line.assert_any_call(
            '    **({"X-Client-Version": DataclassSerializer.serialize(x_client_version)} if x_client_version is not None else {}),'
        )
        code_writer_mock.write_line.assert_any_call("}")  # Closing brace for headers dict

        render_context_mock.add_import.assert_any_call("typing", "Any")
        # render_context_mock.add_import.assert_any_call("typing", "Dict") # This line should be removed or commented

    def test_generate_url_and_args_with_content_type_header(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test that Content-Type header is NOT added to a headers dict by this generator standalone."""
        operation = IROperation(
            operation_id="post_data",
            summary="Post some data",
            description="Posts data to the server.",
            method=HTTPMethod.POST,
            path="/data",
            tags=["data"],
            parameters=[],
            request_body=MagicMock(),
            responses=[],
        )
        ordered_parameters: List[dict[str, Any]] = []
        primary_content_type = (
            "application/json"  # This is passed but not used by current generator to make a headers dict
        )

        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            None,  # resolved_body_type
        )

        code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/data"')

        # Assert that "headers: dict[str, Any] = {" was NOT called
        for call_args, _ in code_writer_mock.write_line.call_args_list:
            assert "headers: dict[str, Any] = {" not in call_args[0]

        # It will write lines for json_body setup due to op.request_body and primary_content_type being json
        code_writer_mock.write_line.assert_any_call(
            "json_body: Any = DataclassSerializer.serialize(body)  # param not found"
        )
        # Should import DataclassSerializer
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")
        # self.render_context_mock.add_import.assert_any_call("typing", "Dict") # Dict is not explicitly imported here
        render_context_mock.add_import.assert_any_call("typing", "Any")  # Any is imported for json_body

    def test_generate_url_and_args_all_param_types_and_content_type(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test operation with path, query, header params, and Content-Type."""
        path_param_info: dict[str, Any] = {
            "name": "user_id",
            "param_in": "path",
            "required": True,
            "original_name": "user_id",
        }
        query_param_info: dict[str, Any] = {
            "name": "verbose_output",  # sanitized from verboseOutput
            "param_in": "query",
            "required": False,
            "original_name": "verboseOutput",
            "schema": IRSchema(type="boolean", is_nullable=True),
        }
        header_param_info: dict[str, Any] = {
            "name": "x_correlation_id",  # sanitized from X-Correlation-ID
            "param_in": "header",
            "required": True,
            "original_name": "X-Correlation-ID",
            "schema": IRSchema(type="string", is_nullable=False),
        }

        operation = IROperation(
            operation_id="update_user_profile",
            summary="Update user profile",
            description="Updates a user profile with various parameters.",
            method=HTTPMethod.PUT,
            path="/users/{user_id}/profile",
            tags=["users"],
            parameters=[
                IRParameter(
                    name="user_id",
                    param_in="path",
                    required=True,
                    schema=IRSchema(type="integer", format="int64", is_nullable=False),
                    description="ID of the user",
                ),
                IRParameter(
                    name="verboseOutput",
                    param_in="query",
                    required=False,
                    schema=IRSchema(type="boolean", is_nullable=True),
                    description="Enable verbose output",
                ),
                IRParameter(
                    name="X-Correlation-ID",
                    param_in="header",
                    required=True,
                    schema=IRSchema(type="string", is_nullable=False),
                    description="Correlation ID for the request",
                ),
            ],
            request_body=MagicMock(),  # Body details not crucial here
            responses=[],
        )
        ordered_parameters = [path_param_info, query_param_info, header_param_info]
        primary_content_type = "application/json"

        def mock_sanitize_name(name: str) -> str:
            if name == "user_id":
                return "user_id_sanitized"
            if name == "verbose_output":
                return "verbose_output_sanitized"
            if name == "x_correlation_id":
                return "x_correlation_id_sanitized"
            return name

        with patch(
            "pyopenapi_gen.core.utils.NameSanitizer.sanitize_method_name", side_effect=mock_sanitize_name
        ) as mock_sanitize_method_name:
            url_args_generator.generate_url_and_args(
                code_writer_mock,
                operation,
                render_context_mock,
                ordered_parameters,
                primary_content_type,
                None,  # resolved_body_type
            )

            # URL assertion (with path param)
            code_writer_mock.write_line.assert_any_call(
                f'url = f"{{self.base_url}}/users/{{user_id_sanitized}}/profile"'
            )
            mock_sanitize_method_name.assert_any_call("user_id")  # For path param in _build_url_with_path_vars

            # Query params assertions
            code_writer_mock.write_line.assert_any_call("params: dict[str, Any] = {")
            code_writer_mock.write_line.assert_any_call(
                '    **({"verboseOutput": DataclassSerializer.serialize(verbose_output_sanitized)} if verbose_output_sanitized is not None else {}),'
            )
            # _write_query_params calls sanitize_method_name on p["name"]
            mock_sanitize_method_name.assert_any_call(
                query_param_info["name"]
            )  # query_param_info["name"] is "verbose_output"

            # Header params assertions
            code_writer_mock.write_line.assert_any_call("headers: dict[str, Any] = {")
            # Content-Type is NOT added by this generator to the headers dict
            # self.code_writer_mock.write_line.assert_any_call(f'    "Content-Type": "{primary_content_type}",')
            code_writer_mock.write_line.assert_any_call(
                '    "X-Correlation-ID": DataclassSerializer.serialize(x_correlation_id_sanitized),'
            )

            # _write_header_params calls sanitize_method_name on p_info["name"]
            mock_sanitize_method_name.assert_any_call(
                header_param_info["name"]
            )  # header_param_info["name"] is "x_correlation_id"

            # Ensure closing braces for params and headers
            calls = [c[0][0] for c in code_writer_mock.write_line.call_args_list]
            param_block_closed = False
            header_block_closed = False
            in_param_block = False
            in_header_block = False
            for call_str in calls:
                if "params: dict[str, Any] = {" in call_str:
                    in_param_block = True
                if in_param_block and call_str == "}":
                    param_block_closed = True
                    in_param_block = False
                if "headers: dict[str, Any] = {" in call_str:
                    in_header_block = True
                if in_header_block and call_str == "}":
                    header_block_closed = True
                    in_header_block = False

            assert param_block_closed, "Params dict should be closed with '}'"
            assert header_block_closed, "Headers dict should be closed with '}'"

            # Assert body setup
            # With primary_content_type = "application/json" and no 'body' in ordered_parameters
            code_writer_mock.write_line.assert_any_call(
                "json_body: Any = DataclassSerializer.serialize(body)  # param not found"
            )
            render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")
            render_context_mock.add_import.assert_any_call("typing", "Any")
            # Dict is not explicitly imported by this section, but Any is for the dict[str, Any] and json_body: Any
            # self.render_context_mock.add_import.assert_any_call("typing", "Dict")

    def test_generate_url_and_args_multipart_with_files_param(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test multipart/form-data with 'files' parameter present in ordered_params."""
        files_param_info: dict[str, Any] = {
            "name": "files",  # Must be 'files' for the current generator logic
            "param_in": "formData",  # Not strictly checked by this part of generator, but typical
            "required": True,
            "original_name": "files",
            "type": "dict[str, IO[Any]]",  # Example type string
        }
        operation = IROperation(
            operation_id="upload_files_multipart",
            summary="Upload multiple files",
            description="Uploads files using multipart/form-data.",
            method=HTTPMethod.POST,
            path="/upload_multipart",
            tags=["files"],
            parameters=[],  # files usually part of requestBody mapping
            request_body=MagicMock(),  # Indicates a body is expected
            responses=[],
        )
        ordered_parameters = [files_param_info]
        primary_content_type = "multipart/form-data"

        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            None,  # resolved_body_type not directly used for multipart in this path
        )

        code_writer_mock.write_line.assert_any_call(
            f"files_data: {files_param_info['type']} = DataclassSerializer.serialize(files)"
        )
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")
        render_context_mock.add_typing_imports_for_type.assert_called_with(files_param_info["type"])

    def test_generate_url_and_args_multipart_no_files_param_fallback(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test multipart/form-data fallback when 'files' parameter is not in ordered_params."""
        operation = IROperation(
            operation_id="upload_files_multipart_fallback",
            summary="Upload multiple files fallback",
            description="Uploads files using multipart/form-data, testing fallback.",
            method=HTTPMethod.POST,
            path="/upload_multipart_fallback",
            tags=["files"],
            parameters=[],
            request_body=MagicMock(),  # Indicates a body is expected
            responses=[],
        )
        ordered_parameters: List[dict[str, Any]] = []  # No 'files' param info
        primary_content_type = "multipart/form-data"

        # Mock logger to check warning
        with patch("pyopenapi_gen.visit.endpoint.generators.url_args_generator.logger") as mock_logger:
            url_args_generator.generate_url_and_args(
                code_writer_mock,
                operation,
                render_context_mock,
                ordered_parameters,
                primary_content_type,
                None,
            )

        mock_logger.warning.assert_called_once()
        assert "Could not find 'files' parameter details" in mock_logger.warning.call_args[0][0]

        code_writer_mock.write_line.assert_any_call(
            "files_data: dict[str, IO[Any]] = DataclassSerializer.serialize(files)  # type failed"
        )
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")
        render_context_mock.add_import.assert_any_call("typing", "Dict")
        render_context_mock.add_import.assert_any_call("typing", "IO")
        render_context_mock.add_import.assert_any_call("typing", "Any")

    def test_generate_url_and_args_form_urlencoded_with_resolved_type(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test application/x-www-form-urlencoded with resolved_body_type."""
        operation = IROperation(
            operation_id="submit_form_data_typed",
            summary="Submit form data with type",
            description="Submits form data using application/x-www-form-urlencoded.",
            method=HTTPMethod.POST,
            path="/submit_form_typed",
            tags=["forms"],
            parameters=[],
            request_body=MagicMock(),
            responses=[],
        )
        ordered_parameters: List[dict[str, Any]] = []  # form_data param usually handled by EndpointParameterProcessor
        primary_content_type = "application/x-www-form-urlencoded"
        resolved_body_type = "dict[str, Union[str, int]]"  # Example resolved type

        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            resolved_body_type,
        )

        code_writer_mock.write_line.assert_any_call(
            f"form_data_body: {resolved_body_type} = DataclassSerializer.serialize(form_data)"
        )
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")
        # This specific path does not add imports itself, assumes type hint is valid

    def test_generate_url_and_args_form_urlencoded_no_resolved_type_fallback(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test application/x-www-form-urlencoded fallback when resolved_body_type is None."""
        operation = IROperation(
            operation_id="submit_form_data_fallback",
            summary="Submit form data fallback",
            description="Submits form data, testing fallback for no resolved_body_type.",
            method=HTTPMethod.POST,
            path="/submit_form_fallback",
            tags=["forms"],
            parameters=[],
            request_body=MagicMock(),
            responses=[],
        )
        ordered_parameters: List[dict[str, Any]] = []
        primary_content_type = "application/x-www-form-urlencoded"
        resolved_body_type = None

        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            resolved_body_type,
        )

        code_writer_mock.write_line.assert_any_call(
            "form_data_body: dict[str, Any] = DataclassSerializer.serialize(form_data)  # Fallback type"
        )
        render_context_mock.add_import.assert_any_call("test_core.utils", "DataclassSerializer")
        render_context_mock.add_import.assert_any_call("typing", "Dict")
        render_context_mock.add_import.assert_any_call("typing", "Any")

    def test_generate_url_and_args_bytes_body(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """Test body handling when resolved_body_type is 'bytes'."""
        operation = IROperation(
            operation_id="upload_binary_data",
            summary="Upload binary data",
            description="Uploads raw binary data.",
            method=HTTPMethod.POST,
            path="/upload_binary",
            tags=["binary"],
            parameters=[],
            request_body=MagicMock(),
            responses=[],
        )
        ordered_parameters: List[dict[str, Any]] = []
        # primary_content_type could be e.g. "application/octet-stream"
        # The logic specifically checks `elif resolved_body_type == "bytes":`
        primary_content_type = "application/octet-stream"
        resolved_body_type = "bytes"

        url_args_generator.generate_url_and_args(
            code_writer_mock,
            operation,
            render_context_mock,
            ordered_parameters,
            primary_content_type,
            resolved_body_type,
        )

        code_writer_mock.write_line.assert_any_call(f"bytes_body: bytes = bytes_content")
        # No specific imports added by this path in the generator

    # ========== ENUM SERIALIZATION TESTS (TDD - RED PHASE) ==========

    def test_write_query_params__required_enum_parameter__serializes_value(
        self, url_args_generator: EndpointUrlArgsGenerator, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Required query parameter is an enum type
        Expected Outcome: Generated code calls DataclassSerializer.serialize() to convert enum to string value

        This test follows TDD principles:
        - RED: Test will fail because current code doesn't call serialize()
        - GREEN: Will pass after implementing the fix
        - REFACTOR: Cleanup if needed
        """
        # Arrange
        writer = CodeWriter()
        operation = IROperation(
            operation_id="list_documents",
            summary="List documents",
            description="List documents with status filter",
            method=HTTPMethod.GET,
            path="/documents",
            tags=["documents"],
            parameters=[
                IRParameter(
                    name="status",
                    param_in="query",
                    required=True,
                    schema=IRSchema(type="string", is_nullable=False),
                    description="Document status filter",
                )
            ],
            request_body=None,
            responses=[],
        )
        ordered_params = [
            {
                "name": "status",
                "original_name": "status",
                "param_in": "query",
                "required": True,
            }
        ]

        # Act
        url_args_generator._write_query_params(writer, operation, ordered_params, render_context_mock)
        generated_code = writer.get_code()

        # Assert
        assert "DataclassSerializer.serialize(status)" in generated_code, (
            "Required query parameter should be serialized with DataclassSerializer.serialize() "
            "to handle enum→string conversion"
        )
        assert '"status": DataclassSerializer.serialize(status)' in generated_code

    def test_write_query_params__optional_enum_parameter__serializes_value(
        self, url_args_generator: EndpointUrlArgsGenerator, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Optional query parameter is an enum type
        Expected Outcome: Generated code calls DataclassSerializer.serialize() within None check

        This ensures enums are converted to string values before being passed to httpx,
        preventing enum objects from appearing in query strings.
        """
        # Arrange
        writer = CodeWriter()
        operation = IROperation(
            operation_id="list_documents",
            summary="List documents",
            description="List documents with optional status filter",
            method=HTTPMethod.GET,
            path="/documents",
            tags=["documents"],
            parameters=[
                IRParameter(
                    name="status",
                    param_in="query",
                    required=False,
                    schema=IRSchema(type="string", is_nullable=True),
                    description="Optional document status filter",
                )
            ],
            request_body=None,
            responses=[],
        )
        ordered_params = [
            {
                "name": "status",
                "original_name": "status",
                "param_in": "query",
                "required": False,
            }
        ]

        # Act
        url_args_generator._write_query_params(writer, operation, ordered_params, render_context_mock)
        generated_code = writer.get_code()

        # Assert
        assert "DataclassSerializer.serialize(status)" in generated_code, (
            "Optional query parameter should be serialized with DataclassSerializer.serialize() "
            "to handle enum→string conversion"
        )
        assert "if status is not None" in generated_code, "Optional parameter should have None check"
        # Verify serialization happens inside the conditional
        assert '{"status": DataclassSerializer.serialize(status)}' in generated_code

    def test_write_header_params__required_enum_parameter__serializes_value(
        self, url_args_generator: EndpointUrlArgsGenerator, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Required header parameter is an enum type
        Expected Outcome: Generated code calls DataclassSerializer.serialize() to convert enum to string value

        Headers must be strings. This test ensures enums are properly converted.
        """
        # Arrange
        writer = CodeWriter()
        operation = IROperation(
            operation_id="get_data",
            summary="Get data",
            description="Get data with API version header",
            method=HTTPMethod.GET,
            path="/data",
            tags=["data"],
            parameters=[
                IRParameter(
                    name="X-API-Version",
                    param_in="header",
                    required=True,
                    schema=IRSchema(type="string", is_nullable=False),
                    description="API version",
                )
            ],
            request_body=None,
            responses=[],
        )
        ordered_params = [
            {
                "name": "x_api_version",
                "original_name": "X-API-Version",
                "param_in": "header",
                "required": True,
            }
        ]

        # Act
        url_args_generator._write_header_params(writer, operation, ordered_params, render_context_mock)
        generated_code = writer.get_code()

        # Assert
        assert "DataclassSerializer.serialize(x_api_version)" in generated_code, (
            "Required header parameter should be serialized with DataclassSerializer.serialize() "
            "to handle enum→string conversion"
        )
        assert '"X-API-Version": DataclassSerializer.serialize(x_api_version)' in generated_code

    def test_write_header_params__optional_enum_parameter__serializes_value(
        self, url_args_generator: EndpointUrlArgsGenerator, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Optional header parameter is an enum type
        Expected Outcome: Generated code calls DataclassSerializer.serialize() within None check

        Ensures enum headers are properly converted to strings before being sent to httpx.
        """
        # Arrange
        writer = CodeWriter()
        operation = IROperation(
            operation_id="get_data",
            summary="Get data",
            description="Get data with optional API version header",
            method=HTTPMethod.GET,
            path="/data",
            tags=["data"],
            parameters=[
                IRParameter(
                    name="X-API-Version",
                    param_in="header",
                    required=False,
                    schema=IRSchema(type="string", is_nullable=True),
                    description="Optional API version",
                )
            ],
            request_body=None,
            responses=[],
        )
        ordered_params = [
            {
                "name": "x_api_version",
                "original_name": "X-API-Version",
                "param_in": "header",
                "required": False,
            }
        ]

        # Act
        url_args_generator._write_header_params(writer, operation, ordered_params, render_context_mock)
        generated_code = writer.get_code()

        # Assert
        assert "DataclassSerializer.serialize(x_api_version)" in generated_code, (
            "Optional header parameter should be serialized with DataclassSerializer.serialize() "
            "to handle enum→string conversion"
        )
        assert "if x_api_version is not None" in generated_code, "Optional parameter should have None check"
        assert '{"X-API-Version": DataclassSerializer.serialize(x_api_version)}' in generated_code

    def test_generate_url_and_args__path_enum_parameter__serializes_before_url(
        self, url_args_generator: EndpointUrlArgsGenerator, code_writer_mock: MagicMock, render_context_mock: MagicMock
    ) -> None:
        """
        Scenario: Path parameter is an enum type
        Expected Outcome: Generated code serializes path variable before URL construction

        Path parameters are interpolated into f-strings. Enums must be converted to strings
        first, otherwise f-string will produce "DocumentStatus.INDEXED" instead of "indexed".
        """
        # Arrange
        operation = IROperation(
            operation_id="get_document_by_status",
            summary="Get document by status",
            description="Get document using status path parameter",
            method=HTTPMethod.GET,
            path="/documents/{status}",
            tags=["documents"],
            parameters=[
                IRParameter(
                    name="status",
                    param_in="path",
                    required=True,
                    schema=IRSchema(type="string", is_nullable=False),
                    description="Document status",
                )
            ],
            request_body=None,
            responses=[],
        )
        ordered_params = [
            {
                "name": "status",
                "original_name": "status",
                "param_in": "path",
                "required": True,
            }
        ]

        # Act
        url_args_generator.generate_url_and_args(
            code_writer_mock, operation, render_context_mock, ordered_params, None, None
        )

        # Assert
        # Get all write_line calls
        calls = [c[0][0] for c in code_writer_mock.write_line.call_args_list]

        # Find serialization and URL lines
        serialize_line_idx = None
        url_line_idx = None

        for i, line in enumerate(calls):
            if "DataclassSerializer.serialize(status)" in line and "status = " in line:
                serialize_line_idx = i
            if 'url = f"{self.base_url}' in line:
                url_line_idx = i

        # Assert serialization happens before URL construction
        assert serialize_line_idx is not None, (
            "Path parameter must be serialized using DataclassSerializer.serialize() "
            "to convert enum to string before f-string interpolation"
        )
        assert url_line_idx is not None, "URL construction line should exist"
        assert serialize_line_idx < url_line_idx, (
            "Path parameter serialization must occur before URL construction "
            "to ensure f-string receives string value, not enum object"
        )
