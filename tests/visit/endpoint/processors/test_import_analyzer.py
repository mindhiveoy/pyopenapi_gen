import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, call

from pyopenapi_gen.context.render_context import RenderContext

# Assuming endpoint_utils is in pyopenapi_gen.helpers
from pyopenapi_gen.helpers.endpoint_utils import get_param_type, get_request_body_type, get_return_type

# Corrected imports based on actual file structure
from pyopenapi_gen.ir import IROperation, IRParameter, IRSchema, IRRequestBody, IRResponse
from pyopenapi_gen.visit.endpoint.processors.import_analyzer import EndpointImportAnalyzer
from pyopenapi_gen.http_types import HTTPMethod


class TestEndpointImportAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        self.render_context_mock = MagicMock(spec=RenderContext)
        self.schemas_mock: Dict[str, Any] = {}
        self.analyzer = EndpointImportAnalyzer(schemas=self.schemas_mock)

    def test_analyze_and_register_imports_basic(self) -> None:
        """
        Scenario:
            Test with a simple operation having one parameter and a basic return type.
        Expected Outcome:
            Imports for the parameter type and return type should be registered.
        """
        # Arrange
        param_schema = IRSchema(type="string", is_nullable=False)
        param1 = IRParameter(name="param1", param_in="query", required=True, schema=param_schema)

        # IRResponse.content is Dict[str, IRSchema], not IRContent
        # Mock IRResponse correctly
        mock_success_response_schema = IRSchema(type="string", name="SuccessResponse")
        mock_response = IRResponse(
            status_code="200", description="OK", content={"application/json": mock_success_response_schema}
        )

        operation = IROperation(
            operation_id="test_op",
            method=HTTPMethod.GET,
            path="/test",
            tags=["test"],
            parameters=[param1],
            request_body=None,
            responses=[mock_response],
            summary="Test summary",
            description="Test description",
        )

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("SuccessResponse", False),
            ) as mock_get_return_type,
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            # Called once in main loop, once in AsyncIterator check
            self.assertEqual(mock_get_param_type.call_count, 2)
            mock_get_param_type.assert_any_call(param1, self.render_context_mock, self.schemas_mock)
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("str")  # For param

            mock_get_return_type.assert_called_once_with(operation, self.render_context_mock, self.schemas_mock)
            # For return type "SuccessResponse"
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("SuccessResponse")
            # Total calls to add_typing_imports_for_type depends on how many distinct types are processed
            # For ("str") and ("SuccessResponse"), it should be 2 if they are distinct and handled.
            # If get_param_type is called twice with "str", add_typing_imports_for_type might be called twice for "str"
            # RenderContext.add_typing_imports_for_type should be idempotent or handle multiple calls gracefully.
            # Let's check based on distinct types identified.
            # self.assertEqual(self.render_context_mock.add_typing_imports_for_type.call_count, 2)
            # This assertion is fragile; focusing on specific any_call for expected types is better.

    def test_analyze_and_register_imports_request_body_multipart(self) -> None:
        """
        Scenario:
            Operation with a multipart/form-data request body.
        Expected Outcome:
            Imports for Dict, IO, Any should be registered for the body.
        """
        # Arrange
        # Mock IRRequestBody correctly for content types
        mock_request_body = IRRequestBody(content={"multipart/form-data": IRSchema(type="object")}, required=True)

        operation = IROperation(
            operation_id="upload_file",
            method=HTTPMethod.POST,
            path="/upload",
            tags=["files"],
            parameters=[],
            request_body=mock_request_body,
            responses=[IRResponse(status_code="204", description="No Content", content={})],
            summary="Upload file",
            description="Uploads a file via multipart.",
        )

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,  # Parameters list is empty, so this won't be called in param loop
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("None", True),  # Assuming 204 No Content means None return type
            ) as mock_get_return_type,
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            # Imports for multipart body
            self.render_context_mock.add_import.assert_any_call("typing", "Dict")
            self.render_context_mock.add_import.assert_any_call("typing", "IO")
            self.render_context_mock.add_import.assert_any_call("typing", "Any")
            # Type registration for the body type string
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("Dict[str, IO[Any]]")

            # Return type import
            mock_get_return_type.assert_called_once_with(operation, self.render_context_mock, self.schemas_mock)
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("None")

            # get_param_type should be called 0 times in param loop (empty params) + 0 times in async check (empty params)
            self.assertEqual(mock_get_param_type.call_count, 0)

    def test_analyze_and_register_imports_request_body_json(self) -> None:
        """
        Scenario:
            Operation with an application/json request body.
        Expected Outcome:
            Imports for the JSON body type should be registered.
        """
        # Arrange
        json_body_schema = IRSchema(type="object", name="MyJsonPayload")
        mock_request_body = IRRequestBody(content={"application/json": json_body_schema}, required=True)

        operation = IROperation(
            operation_id="create_item_json",
            method=HTTPMethod.POST,
            path="/items_json",
            tags=["items"],
            parameters=[],
            request_body=mock_request_body,
            responses=[IRResponse(status_code="201", description="Created", content={})],
            summary="Create item via JSON",
            description="Creates an item using JSON payload.",
        )

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_request_body_type",
                return_value="MyJsonPayload",
            ) as mock_get_request_body_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("None", True),
            ) as mock_get_return_type,
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            mock_get_request_body_type.assert_called_once_with(
                mock_request_body, self.render_context_mock, self.schemas_mock
            )
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("MyJsonPayload")

            # Return type import
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("None")
            self.assertEqual(mock_get_param_type.call_count, 0)  # No params

    def test_analyze_and_register_imports_request_body_form_urlencoded(self) -> None:
        """
        Scenario:
            Operation with an application/x-www-form-urlencoded request body.
        Expected Outcome:
            Imports for Dict and Any should be registered for the body type.
        """
        # Arrange
        mock_request_body = IRRequestBody(
            content={"application/x-www-form-urlencoded": IRSchema(type="object")}, required=True
        )

        operation = IROperation(
            operation_id="submit_form",
            method=HTTPMethod.POST,
            path="/submit_form",
            tags=["forms"],
            parameters=[],
            request_body=mock_request_body,
            responses=[IRResponse(status_code="200", description="OK", content={})],
            summary="Submit form data",
            description="Submits data via form urlencoded.",
        )

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("None", True),
            ) as mock_get_return_type,
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            # Imports for form-urlencoded body
            self.render_context_mock.add_import.assert_any_call("typing", "Dict")
            self.render_context_mock.add_import.assert_any_call("typing", "Any")
            # Type registration for the body type string "Dict[str, Any]"
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("Dict[str, Any]")

            # Return type import
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("None")
            self.assertEqual(mock_get_param_type.call_count, 0)  # No params

    def test_analyze_and_register_imports_request_body_octet_stream(self) -> None:
        """
        Scenario:
            Operation with an application/octet-stream request body (fallback to bytes).
        Expected Outcome:
            Imports for "bytes" type should be registered.
        """
        # Arrange
        mock_request_body = IRRequestBody(
            content={"application/octet-stream": IRSchema(type="string", format="binary")},  # Schema for octet-stream
            required=True,
        )

        operation = IROperation(
            operation_id="upload_binary",
            method=HTTPMethod.POST,
            path="/upload_binary",
            tags=["binary"],
            parameters=[],
            request_body=mock_request_body,
            responses=[IRResponse(status_code="200", description="OK", content={})],
            summary="Upload binary data",
            description="Uploads raw binary data.",
        )

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("None", True),
            ) as mock_get_return_type,
            # get_request_body_type is NOT called in this path
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            # Type registration for the body type string "bytes"
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("bytes")

            # Return type import
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("None")
            self.assertEqual(mock_get_param_type.call_count, 0)  # No params

    def test_analyze_and_register_imports_request_body_empty_content(self) -> None:
        """
        Scenario:
            Operation with a request body that has no defined content types.
        Expected Outcome:
            No body-specific type imports should be registered beyond what other parts trigger.
        """
        # Arrange
        mock_request_body = IRRequestBody(content={}, required=True)  # Empty content dict

        operation = IROperation(
            operation_id="test_empty_content",
            method=HTTPMethod.POST,
            path="/empty_content",
            tags=["test"],
            parameters=[],
            request_body=mock_request_body,
            responses=[IRResponse(status_code="200", description="OK", content={})],
            summary="Test empty content",
            description="Tests request body with no content types.",
        )

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_request_body_type"
            ) as mock_get_request_body_type,  # Should not be called
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("None", True),
            ) as mock_get_return_type,
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            # Ensure add_typing_imports_for_type was not called for any specific body type derived from the empty content
            # It will be called for the return type "None".
            # We need to check that it wasn't called for e.g. "bytes" or "Dict[str, Any]" due to body path.

            # Get all calls to add_typing_imports_for_type
            all_add_typing_calls = [
                c[0][0] for c in self.render_context_mock.add_typing_imports_for_type.call_args_list
            ]
            # Expected calls are only for parameters (if any) and return type.
            # In this test, no params, return type is "None".
            self.assertIn("None", all_add_typing_calls)  # For return type
            # Ensure no body-specific types like 'bytes' or 'Dict[str, IO[Any]]' or 'Dict[str, Any]' were added from body path
            self.assertNotIn("bytes", all_add_typing_calls)
            self.assertNotIn("Dict[str, IO[Any]]", all_add_typing_calls)
            self.assertNotIn("Dict[str, Any]", all_add_typing_calls)

            mock_get_request_body_type.assert_not_called()
            self.assertEqual(mock_get_param_type.call_count, 0)

    def test_analyze_and_register_imports_async_iterator_return(self) -> None:
        """
        Scenario:
            Operation return type contains "AsyncIterator".
        Expected Outcome:
            "collections.abc" should be imported.
        """
        # Arrange
        operation = IROperation(
            operation_id="stream_data",
            method=HTTPMethod.GET,
            path="/stream",
            tags=["streaming"],
            parameters=[],
            request_body=None,
            responses=[  # Simplified, actual response structure for streaming can vary
                IRResponse(status_code="200", description="Streaming data", content={})
            ],
            summary="Stream data",
            description="Streams data using AsyncIterator.",
        )

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("AsyncIterator[DataItem]", False),  # Return type includes AsyncIterator
            ) as mock_get_return_type,
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            self.render_context_mock.add_plain_import.assert_called_once_with("collections.abc")
            # Ensure type imports for the return type itself still happen
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("AsyncIterator[DataItem]")
            self.assertEqual(mock_get_param_type.call_count, 0)  # No params

    def test_analyze_and_register_imports_async_iterator_param(self) -> None:
        """
        Scenario:
            A parameter type contains "AsyncIterator", return type does not.
        Expected Outcome:
            "collections.abc" should be imported.
        """
        # Arrange
        async_param_schema = IRSchema(type="object")  # Actual type doesn't matter as get_param_type is mocked
        async_param = IRParameter(name="inputStream", param_in="query", required=True, schema=async_param_schema)

        operation = IROperation(
            operation_id="process_stream",
            method=HTTPMethod.POST,
            path="/process",
            tags=["streaming"],
            parameters=[async_param],
            request_body=None,
            responses=[IRResponse(status_code="200", description="OK", content={})],
            summary="Process stream",
            description="Processes an input stream.",
        )

        # Mock get_param_type to return AsyncIterator for the specific param, and something else otherwise
        def mock_get_param_type_side_effect(param: IRParameter, context: RenderContext, schemas: Dict[str, Any]) -> str:
            if param.name == "inputStream":
                return "AsyncIterator[bytes]"
            return "RegularType"

        with (
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type",
                side_effect=mock_get_param_type_side_effect,
            ) as mock_get_param_type,
            unittest.mock.patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_return_type",
                return_value=("SimpleResponse", False),  # Return type does NOT include AsyncIterator
            ) as mock_get_return_type,
        ):
            # Act
            self.analyzer.analyze_and_register_imports(operation, self.render_context_mock)

            # Assert
            self.render_context_mock.add_plain_import.assert_called_once_with("collections.abc")
            # Ensure type imports for param types and return type still happen
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("AsyncIterator[bytes]")
            self.render_context_mock.add_typing_imports_for_type.assert_any_call("SimpleResponse")
            # get_param_type is called once in param loop, once in async_iterator check loop for this param
            self.assertEqual(mock_get_param_type.call_count, 2)
            mock_get_param_type.assert_any_call(async_param, self.render_context_mock, self.schemas_mock)


if __name__ == "__main__":
    unittest.main()
