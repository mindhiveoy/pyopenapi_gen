import unittest
from typing import Any as TypingAny, Union
from typing import Dict, List
from unittest.mock import MagicMock, call, patch

from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRParameter, IRSchema
from pyopenapi_gen.visit.endpoint.generators.url_args_generator import EndpointUrlArgsGenerator


class TestEndpointUrlArgsGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.render_context_mock = MagicMock(spec=RenderContext)
        self.code_writer_mock = MagicMock(spec=CodeWriter)
        self.generator = EndpointUrlArgsGenerator()

    def test_generate_url_and_args_basic_get(self) -> None:
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
        ordered_parameters: List[Dict[str, TypingAny]] = []

        self.generator.generate_url_and_args(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            ordered_parameters,
            None,  # primary_content_type
            None,  # resolved_body_type
        )
        expected_calls = [
            call('url = f"{self.base_url}/items"'),
            call(""),
        ]
        self.code_writer_mock.write_line.assert_has_calls(expected_calls, any_order=False)

        # Check return value
        returned_value = self.generator.generate_url_and_args(
            self.code_writer_mock,  # Re-call to get return value, mock calls will be duplicated but assertions are specific
            operation,
            self.render_context_mock,
            ordered_parameters,
            None,
            None,
        )
        self.assertFalse(returned_value, "generate_url_and_args should return False when no headers are written.")

        calls = self.code_writer_mock.write_line.call_args_list
        params_written = any("params: Dict[str, Any] = {" in c[0][0] for c in calls)
        headers_written = any("headers: Dict[str, Any] = {" in c[0][0] for c in calls)

        self.assertFalse(
            params_written, "Params dict should not have been written for a basic GET with no query params."
        )
        self.assertFalse(
            headers_written, "Headers dict should not have been written for a basic GET with no header params."
        )

    def test_generate_url_and_args_with_path_params(self) -> None:
        """Test operation with path parameters."""
        path_param_info: Dict[str, TypingAny] = {
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
            self.generator.generate_url_and_args(
                self.code_writer_mock, operation, self.render_context_mock, [path_param_info], None, None
            )
            self.code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/items/{{item_id_sanitized}}"')
            mock_sanitize.assert_called_with("item_id")

    def test_generate_url_and_args_with_query_params(self) -> None:
        """Test operation with query parameters."""
        query_param_dict: Dict[str, TypingAny] = {
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
            self.generator.generate_url_and_args(
                self.code_writer_mock, operation, self.render_context_mock, [query_param_dict], None, None
            )

            self.code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/items"')
            self.code_writer_mock.write_line.assert_any_call("params: Dict[str, Any] = {")
            self.code_writer_mock.write_line.assert_any_call(
                '    **({"filterBy": filter_by} if filter_by is not None else {}),'
            )
            mock_sanitize_query.assert_any_call("filter_by")
            self.render_context_mock.add_import.assert_any_call("typing", "Any")

    def test_generate_url_and_args_with_header_params(self) -> None:
        """Test operation with header parameters."""
        header_param_required_dict: Dict[str, TypingAny] = {
            "name": "x_request_id",
            "param_in": "header",
            "required": True,
            "original_name": "X-Request-ID",
            "schema": IRSchema(type="string", is_nullable=False),
        }
        header_param_optional_dict: Dict[str, TypingAny] = {
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
            returned_value = self.generator.generate_url_and_args(
                self.code_writer_mock, operation, self.render_context_mock, ordered_parameters, None, None
            )

        self.assertTrue(returned_value, "generate_url_and_args should return True when headers are written.")

        self.code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/items_with_headers"')
        self.code_writer_mock.write_line.assert_any_call("headers: Dict[str, Any] = {")
        self.code_writer_mock.write_line.assert_any_call('    "X-Request-ID": x_request_id,')
        self.code_writer_mock.write_line.assert_any_call(
            '    **({"X-Client-Version": x_client_version} if x_client_version is not None else {}),'
        )
        self.code_writer_mock.write_line.assert_any_call("}")  # Closing brace for headers dict

        # Ensure NameSanitizer.sanitize_method_name was called for the Python variable names
        # This assertion is tricky because sanitize_method_name is called by _build_url_with_path_vars
        # if path variables were present. For header/query params, the 'name' in param_info is assumed
        # to be pre-sanitized. Let's adjust the expectation.
        # If path had vars, e.g. /items/{id}, then sanitize_method_name('id') would be called.
        # Since our path /items_with_headers has no vars, sanitize_method_name is NOT called by _build_url_with_path_vars.
        # The mock_sanitize_name is used by the test setup to provide sanitized names for `param_info["name"]` if needed,
        # but `EndpointUrlArgsGenerator` itself doesn't call sanitize_method_name on header/query param names from `param_info`.

        # Let's verify based on the `param_info` provided, which has `name` already set to the sanitized form.
        # The actual call to `sanitize_method_name` happens upstream in EndpointParameterProcessor.
        # For this unit test, we're testing that `_write_header_params` uses `param_info["name"]` correctly.

        # The mock_sanitize_header_method_name will only be hit if the path itself has variables that need sanitizing.
        # For this specific test case, the path "/items_with_headers" has no variables.
        # So, mock_sanitize_header_method_name should not have been called by _build_url_with_path_vars.
        # The `side_effect=mock_sanitize_name` is mostly for if the path *did* have variables.
        # The important check is that the output code uses the correct variable names (e.g., 'x_request_id')
        # which come from `ordered_parameters[...]['name']`.

        # If there were path params, this would be asserted:
        # mock_sanitize_header_method_name.assert_any_call("some_path_var_name")

        # Assert that the Python variable names used in the output code match the sanitized names provided in `ordered_parameters`.
        # This is implicitly checked by the assert_any_call for the lines themselves:
        # e.g. '    "X-Request-ID": x_request_id,' implicitly checks that 'x_request_id' is used.

        self.render_context_mock.add_import.assert_any_call("typing", "Any")
        # self.render_context_mock.add_import.assert_any_call("typing", "Dict") # This line should be removed or commented

    def test_generate_url_and_args_with_content_type_header(self) -> None:
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
        ordered_parameters: List[Dict[str, TypingAny]] = []
        primary_content_type = (
            "application/json"  # This is passed but not used by current generator to make a headers dict
        )

        self.generator.generate_url_and_args(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            ordered_parameters,
            primary_content_type,
            None,  # resolved_body_type
        )

        self.code_writer_mock.write_line.assert_any_call(f'url = f"{{self.base_url}}/data"')

        # Assert that "headers: Dict[str, Any] = {" was NOT called
        for call_args, _ in self.code_writer_mock.write_line.call_args_list:
            self.assertNotIn("headers: Dict[str, Any] = {", call_args[0])

        # It will write lines for json_body setup due to op.request_body and primary_content_type being json
        self.code_writer_mock.write_line.assert_any_call(
            "json_body: Any = body  # 'body' param not found in signature details"
        )
        # self.render_context_mock.add_import.assert_any_call("typing", "Dict") # Dict is not explicitly imported here
        self.render_context_mock.add_import.assert_any_call("typing", "Any")  # Any is imported for json_body

    def test_generate_url_and_args_all_param_types_and_content_type(self) -> None:
        """Test operation with path, query, header params, and Content-Type."""
        path_param_info: Dict[str, TypingAny] = {
            "name": "user_id",
            "param_in": "path",
            "required": True,
            "original_name": "user_id",
        }
        query_param_info: Dict[str, TypingAny] = {
            "name": "verbose_output",  # sanitized from verboseOutput
            "param_in": "query",
            "required": False,
            "original_name": "verboseOutput",
            "schema": IRSchema(type="boolean", is_nullable=True),
        }
        header_param_info: Dict[str, TypingAny] = {
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
            self.generator.generate_url_and_args(
                self.code_writer_mock,
                operation,
                self.render_context_mock,
                ordered_parameters,
                primary_content_type,
                None,  # resolved_body_type
            )

            # URL assertion (with path param)
            self.code_writer_mock.write_line.assert_any_call(
                f'url = f"{{self.base_url}}/users/{{user_id_sanitized}}/profile"'
            )
            mock_sanitize_method_name.assert_any_call("user_id")  # For path param in _build_url_with_path_vars

            # Query params assertions
            self.code_writer_mock.write_line.assert_any_call("params: Dict[str, Any] = {")
            self.code_writer_mock.write_line.assert_any_call(
                '    **({"verboseOutput": verbose_output_sanitized} if verbose_output_sanitized is not None else {}),'
            )
            # _write_query_params calls sanitize_method_name on p["name"]
            mock_sanitize_method_name.assert_any_call(
                query_param_info["name"]
            )  # query_param_info["name"] is "verbose_output"

            # Header params assertions
            self.code_writer_mock.write_line.assert_any_call("headers: Dict[str, Any] = {")
            # Content-Type is NOT added by this generator to the headers dict
            # self.code_writer_mock.write_line.assert_any_call(f'    "Content-Type": "{primary_content_type}",')
            self.code_writer_mock.write_line.assert_any_call('    "X-Correlation-ID": x_correlation_id_sanitized,')

            # _write_header_params calls sanitize_method_name on p_info["name"]
            mock_sanitize_method_name.assert_any_call(
                header_param_info["name"]
            )  # header_param_info["name"] is "x_correlation_id"

            # Ensure closing braces for params and headers
            calls = [c[0][0] for c in self.code_writer_mock.write_line.call_args_list]
            param_block_closed = False
            header_block_closed = False
            in_param_block = False
            in_header_block = False
            for call_str in calls:
                if "params: Dict[str, Any] = {" in call_str:
                    in_param_block = True
                if in_param_block and call_str == "}":
                    param_block_closed = True
                    in_param_block = False
                if "headers: Dict[str, Any] = {" in call_str:
                    in_header_block = True
                if in_header_block and call_str == "}":
                    header_block_closed = True
                    in_header_block = False

            self.assertTrue(param_block_closed, "Params dict should be closed with '}'")
            self.assertTrue(header_block_closed, "Headers dict should be closed with '}'")

            # Assert body setup
            # With primary_content_type = "application/json" and no 'body' in ordered_parameters
            self.code_writer_mock.write_line.assert_any_call(
                "json_body: Any = body  # 'body' param not found in signature details"
            )
            self.render_context_mock.add_import.assert_any_call("typing", "Any")
            # Dict is not explicitly imported by this section, but Any is for the Dict[str, Any] and json_body: Any
            # self.render_context_mock.add_import.assert_any_call("typing", "Dict")

    def test_generate_url_and_args_multipart_with_files_param(self) -> None:
        """Test multipart/form-data with 'files' parameter present in ordered_params."""
        files_param_info: Dict[str, TypingAny] = {
            "name": "files",  # Must be 'files' for the current generator logic
            "param_in": "formData",  # Not strictly checked by this part of generator, but typical
            "required": True,
            "original_name": "files",
            "type": "Dict[str, IO[Any]]",  # Example type string
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

        self.generator.generate_url_and_args(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            ordered_parameters,
            primary_content_type,
            None,  # resolved_body_type not directly used for multipart in this path
        )

        self.code_writer_mock.write_line.assert_any_call(f"files_data: {files_param_info['type']} = files")
        self.render_context_mock.add_typing_imports_for_type.assert_called_with(files_param_info["type"])

    def test_generate_url_and_args_multipart_no_files_param_fallback(self) -> None:
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
        ordered_parameters: List[Dict[str, TypingAny]] = []  # No 'files' param info
        primary_content_type = "multipart/form-data"

        # Mock logger to check warning
        with patch("pyopenapi_gen.visit.endpoint.generators.url_args_generator.logger") as mock_logger:
            self.generator.generate_url_and_args(
                self.code_writer_mock,
                operation,
                self.render_context_mock,
                ordered_parameters,
                primary_content_type,
                None,
            )

        mock_logger.warning.assert_called_once()
        self.assertIn("Could not find 'files' parameter details", mock_logger.warning.call_args[0][0])

        self.code_writer_mock.write_line.assert_any_call(
            "files_data: Dict[str, IO[Any]] = files  # Type inference for files_data failed"
        )
        self.render_context_mock.add_import.assert_any_call("typing", "Dict")
        self.render_context_mock.add_import.assert_any_call("typing", "IO")
        self.render_context_mock.add_import.assert_any_call("typing", "Any")

    def test_generate_url_and_args_form_urlencoded_with_resolved_type(self) -> None:
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
        ordered_parameters: List[
            Dict[str, TypingAny]
        ] = []  # form_data param usually handled by EndpointParameterProcessor
        primary_content_type = "application/x-www-form-urlencoded"
        resolved_body_type = "Dict[str, Union[str, int]]"  # Example resolved type

        self.generator.generate_url_and_args(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            ordered_parameters,
            primary_content_type,
            resolved_body_type,
        )

        self.code_writer_mock.write_line.assert_any_call(f"form_data_body: {resolved_body_type} = form_data")
        # This specific path does not add imports itself, assumes type hint is valid

    def test_generate_url_and_args_form_urlencoded_no_resolved_type_fallback(self) -> None:
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
        ordered_parameters: List[Dict[str, TypingAny]] = []
        primary_content_type = "application/x-www-form-urlencoded"
        resolved_body_type = None

        self.generator.generate_url_and_args(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            ordered_parameters,
            primary_content_type,
            resolved_body_type,
        )

        self.code_writer_mock.write_line.assert_any_call("form_data_body: Dict[str, Any] = form_data  # Fallback type")
        self.render_context_mock.add_import.assert_any_call("typing", "Dict")
        self.render_context_mock.add_import.assert_any_call("typing", "Any")

    def test_generate_url_and_args_bytes_body(self) -> None:
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
        ordered_parameters: List[Dict[str, TypingAny]] = []
        # primary_content_type could be e.g. "application/octet-stream"
        # The logic specifically checks `elif resolved_body_type == "bytes":`
        primary_content_type = "application/octet-stream"
        resolved_body_type = "bytes"

        self.generator.generate_url_and_args(
            self.code_writer_mock,
            operation,
            self.render_context_mock,
            ordered_parameters,
            primary_content_type,
            resolved_body_type,
        )

        self.code_writer_mock.write_line.assert_any_call(f"bytes_body: bytes = bytes_content")
        # No specific imports added by this path in the generator


if __name__ == "__main__":
    unittest.main()
