from typing import Any, Dict
from unittest.mock import (
    MagicMock,
)

# Alias to avoid conflict if pytest.patch is used elsewhere, though not in this file
from unittest.mock import (
    patch as unittest_patch,
)

import pytest
from pyopenapi_gen.context.render_context import RenderContext

# Assuming endpoint_utils is in pyopenapi_gen.helpers
from pyopenapi_gen.http_types import HTTPMethod

# Corrected imports based on actual file structure
from pyopenapi_gen.ir import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy
from pyopenapi_gen.visit.endpoint.processors.import_analyzer import EndpointImportAnalyzer


@pytest.fixture
def render_context_mock() -> MagicMock:
    return MagicMock(spec=RenderContext)


@pytest.fixture
def schemas_mock() -> Dict[str, Any]:
    return {}


@pytest.fixture
def import_analyzer(schemas_mock: Dict[str, Any]) -> EndpointImportAnalyzer:
    return EndpointImportAnalyzer(schemas=schemas_mock)


class TestEndpointImportAnalyzer:
    def test_analyze_and_register_imports_basic(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
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

        # Create ResponseStrategy for the test
        response_strategy = ResponseStrategy(
            return_type="SuccessResponse",
            response_schema=mock_success_response_schema,
            is_streaming=False,
            response_ir=mock_response,
        )

        with unittest_patch(
            "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
        ) as mock_get_param_type:
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            # Called once in main loop, once in AsyncIterator check
            assert mock_get_param_type.call_count == 2
            mock_get_param_type.assert_any_call(param1, render_context_mock, schemas_mock)
            render_context_mock.add_typing_imports_for_type.assert_any_call("str")  # For param

            # Should register imports for the response strategy's return type
            render_context_mock.add_typing_imports_for_type.assert_any_call("SuccessResponse")

    def test_analyze_and_register_imports_request_body_multipart(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
        """
        Scenario:
            Operation with a multipart/form-data request body.
        Expected Outcome:
            Imports for Dict, IO, Any should be registered for the body.
        """
        # Arrange
        # Mock IRRequestBody correctly for content types
        mock_request_body = IRRequestBody(content={"multipart/form-data": IRSchema(type="object")}, required=True)

        no_content_response = IRResponse(status_code="204", description="No Content", content={})
        operation = IROperation(
            operation_id="upload_file",
            method=HTTPMethod.POST,
            path="/upload",
            tags=["files"],
            parameters=[],
            request_body=mock_request_body,
            responses=[no_content_response],
            summary="Upload file",
            description="Uploads a file via multipart.",
        )

        # Create ResponseStrategy for 204 No Content
        response_strategy = ResponseStrategy(
            return_type="None", response_schema=None, is_streaming=False, response_ir=no_content_response
        )

        with unittest_patch(
            "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
        ) as mock_get_param_type:  # Parameters list is empty, so this won't be called in param loop
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            # Imports for multipart body
            render_context_mock.add_import.assert_any_call("typing", "Dict")
            render_context_mock.add_import.assert_any_call("typing", "IO")
            render_context_mock.add_import.assert_any_call("typing", "Any")
            # Type registration for the body type string
            render_context_mock.add_typing_imports_for_type.assert_any_call("Dict[str, IO[Any]]")

            # Return type import using ResponseStrategy
            render_context_mock.add_typing_imports_for_type.assert_any_call("None")

            # get_param_type should be called 0 times in param loop (empty params) + 0 times in async check (empty params)
            assert mock_get_param_type.call_count == 0

    def test_analyze_and_register_imports_request_body_json(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
        """
        Scenario:
            Operation with an application/json request body.
        Expected Outcome:
            Imports for the JSON body type should be registered.
        """
        # Arrange
        json_body_schema = IRSchema(type="object", name="MyJsonPayload")
        mock_request_body = IRRequestBody(content={"application/json": json_body_schema}, required=True)

        created_response = IRResponse(status_code="201", description="Created", content={})
        operation = IROperation(
            operation_id="create_item_json",
            method=HTTPMethod.POST,
            path="/items_json",
            tags=["items"],
            parameters=[],
            request_body=mock_request_body,
            responses=[created_response],
            summary="Create item via JSON",
            description="Creates an item using JSON payload.",
        )

        # Create ResponseStrategy for 201 Created
        response_strategy = ResponseStrategy(
            return_type="None", response_schema=None, is_streaming=False, response_ir=created_response
        )

        with (
            unittest_patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest_patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_request_body_type",
                return_value="MyJsonPayload",
            ) as mock_get_request_body_type,
        ):
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            mock_get_request_body_type.assert_called_once_with(mock_request_body, render_context_mock, schemas_mock)
            render_context_mock.add_typing_imports_for_type.assert_any_call("MyJsonPayload")

            # Return type import
            render_context_mock.add_typing_imports_for_type.assert_any_call("None")
            assert mock_get_param_type.call_count == 0  # No params

    def test_analyze_and_register_imports_request_body_form_urlencoded(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
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

        ok_response = IRResponse(status_code="200", description="OK", content={})
        operation = IROperation(
            operation_id="submit_form",
            method=HTTPMethod.POST,
            path="/submit_form",
            tags=["forms"],
            parameters=[],
            request_body=mock_request_body,
            responses=[ok_response],
            summary="Submit form data",
            description="Submits data via form urlencoded.",
        )

        # Create ResponseStrategy for 200 OK
        response_strategy = ResponseStrategy(
            return_type="None", response_schema=None, is_streaming=False, response_ir=ok_response
        )

        with unittest_patch(
            "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
        ) as mock_get_param_type:
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            # Imports for form-urlencoded body
            render_context_mock.add_import.assert_any_call("typing", "Dict")
            render_context_mock.add_import.assert_any_call("typing", "Any")
            # Type registration for the body type string "Dict[str, Any]"
            render_context_mock.add_typing_imports_for_type.assert_any_call("Dict[str, Any]")

            # Return type import using ResponseStrategy
            render_context_mock.add_typing_imports_for_type.assert_any_call("None")
            assert mock_get_param_type.call_count == 0  # No params

    def test_analyze_and_register_imports_request_body_octet_stream(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
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

        ok_response = IRResponse(status_code="200", description="OK", content={})
        operation = IROperation(
            operation_id="upload_binary",
            method=HTTPMethod.POST,
            path="/upload_binary",
            tags=["binary"],
            parameters=[],
            request_body=mock_request_body,
            responses=[ok_response],
            summary="Upload binary data",
            description="Uploads raw binary data.",
        )

        # Create ResponseStrategy for 200 OK
        response_strategy = ResponseStrategy(
            return_type="None", response_schema=None, is_streaming=False, response_ir=ok_response
        )

        with unittest_patch(
            "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
        ) as mock_get_param_type:
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            # Type registration for the body type string "bytes"
            render_context_mock.add_typing_imports_for_type.assert_any_call("bytes")

            # Return type import using ResponseStrategy
            render_context_mock.add_typing_imports_for_type.assert_any_call("None")
            assert mock_get_param_type.call_count == 0  # No params

    def test_analyze_and_register_imports_request_body_empty_content(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
        """
        Scenario:
            Operation with a request body that has no defined content types.
        Expected Outcome:
            No body-specific type imports should be registered beyond what other parts trigger.
        """
        # Arrange
        mock_request_body = IRRequestBody(content={}, required=True)  # Empty content dict

        ok_response = IRResponse(status_code="200", description="OK", content={})
        operation = IROperation(
            operation_id="test_empty_content",
            method=HTTPMethod.POST,
            path="/empty_content",
            tags=["test"],
            parameters=[],
            request_body=mock_request_body,
            responses=[ok_response],
            summary="Test empty content",
            description="Tests request body with no content types.",
        )

        # Create ResponseStrategy for 200 OK
        response_strategy = ResponseStrategy(
            return_type="None", response_schema=None, is_streaming=False, response_ir=ok_response
        )

        with (
            unittest_patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
            ) as mock_get_param_type,
            unittest_patch(
                "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_request_body_type"
            ) as mock_get_request_body_type,  # Should not be called
        ):
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            # Ensure add_typing_imports_for_type was not called for any specific body type derived from the empty content
            # It will be called for the return type "None".
            # We need to check that it wasn't called for e.g. "bytes" or "Dict[str, Any]" due to body path.

            # Get all calls to add_typing_imports_for_type
            all_add_typing_calls = [c[0][0] for c in render_context_mock.add_typing_imports_for_type.call_args_list]
            # Expected calls are only for parameters (if any) and return type.
            # In this test, no params, return type is "None".
            assert "None" in all_add_typing_calls
            # Ensure no body-specific types like 'bytes' or 'Dict[str, IO[Any]]' or 'Dict[str, Any]' were added from body path
            assert "bytes" not in all_add_typing_calls
            assert "Dict[str, IO[Any]]" not in all_add_typing_calls
            assert "Dict[str, Any]" not in all_add_typing_calls

            mock_get_request_body_type.assert_not_called()
            assert mock_get_param_type.call_count == 0

    def test_analyze_and_register_imports_async_iterator_return(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
        """
        Scenario:
            Operation return type contains "AsyncIterator".
        Expected Outcome:
            "collections.abc" should be imported.
        """
        # Arrange
        streaming_response = IRResponse(status_code="200", description="Streaming data", content={})
        operation = IROperation(
            operation_id="stream_data",
            method=HTTPMethod.GET,
            path="/stream",
            tags=["streaming"],
            parameters=[],
            request_body=None,
            responses=[streaming_response],
            summary="Stream data",
            description="Streams data using AsyncIterator.",
        )

        # Create ResponseStrategy with AsyncIterator return type
        response_strategy = ResponseStrategy(
            return_type="AsyncIterator[DataItem]",
            response_schema=None,
            is_streaming=True,
            response_ir=streaming_response,
        )

        with unittest_patch(
            "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type", return_value="str"
        ) as mock_get_param_type:
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            render_context_mock.add_plain_import.assert_called_once_with("collections.abc")
            # Ensure type imports for the return type itself still happen
            render_context_mock.add_typing_imports_for_type.assert_any_call("AsyncIterator[DataItem]")
            assert mock_get_param_type.call_count == 0  # No params

    def test_analyze_and_register_imports_async_iterator_param(
        self, import_analyzer: EndpointImportAnalyzer, render_context_mock: MagicMock, schemas_mock: Dict[str, Any]
    ) -> None:
        """
        Scenario:
            A parameter type contains "AsyncIterator", return type does not.
        Expected Outcome:
            "collections.abc" should be imported.
        """
        # Arrange
        async_param_schema = IRSchema(type="object")  # Actual type doesn't matter as get_param_type is mocked
        async_param = IRParameter(name="inputStream", param_in="query", required=True, schema=async_param_schema)

        ok_response = IRResponse(status_code="200", description="OK", content={})
        operation = IROperation(
            operation_id="process_stream",
            method=HTTPMethod.POST,
            path="/process",
            tags=["streaming"],
            parameters=[async_param],
            request_body=None,
            responses=[ok_response],
            summary="Process stream",
            description="Processes an input stream.",
        )

        # Create ResponseStrategy for simple response (non-AsyncIterator return type)
        response_strategy = ResponseStrategy(
            return_type="SimpleResponse", response_schema=None, is_streaming=False, response_ir=ok_response
        )

        # Mock get_param_type to return AsyncIterator for the specific param, and something else otherwise
        def mock_get_param_type_side_effect(param: IRParameter, context: RenderContext, schemas: Dict[str, Any]) -> str:
            if param.name == "inputStream":
                return "AsyncIterator[bytes]"
            return "RegularType"

        with unittest_patch(
            "pyopenapi_gen.visit.endpoint.processors.import_analyzer.get_param_type",
            side_effect=mock_get_param_type_side_effect,
        ) as mock_get_param_type:
            # Act
            import_analyzer.analyze_and_register_imports(operation, render_context_mock, response_strategy)

            # Assert
            render_context_mock.add_plain_import.assert_called_once_with("collections.abc")
            # Ensure type imports for param types and return type still happen
            render_context_mock.add_typing_imports_for_type.assert_any_call("AsyncIterator[bytes]")
            render_context_mock.add_typing_imports_for_type.assert_any_call("SimpleResponse")
            # get_param_type is called once in param loop, once in async_iterator check loop for this param
            assert mock_get_param_type.call_count == 2
            mock_get_param_type.assert_any_call(async_param, render_context_mock, schemas_mock)
