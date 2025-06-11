"""
Tests for the EndpointDocstringGenerator class.
"""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.ir import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema
from pyopenapi_gen.types.strategies.response_strategy import ResponseStrategy
from pyopenapi_gen.visit.endpoint.generators.docstring_generator import EndpointDocstringGenerator


@pytest.fixture
def op_for_docstring() -> IROperation:
    return IROperation(
        path="/doc_test",
        method=HTTPMethod.POST,
        operation_id="test_docstring_op",
        summary="This is the summary.",
        description="This is a longer description that might span multiple lines and explain details.",
        parameters=[
            IRParameter(
                name="path_id",
                param_in="path",
                required=True,
                schema=IRSchema(type="integer", is_nullable=False),
                description="The ID in the path.",
            ),
            IRParameter(
                name="query_opt",
                param_in="query",
                required=False,
                schema=IRSchema(type="string", is_nullable=True),
                description="An optional query param.",
            ),
        ],
        request_body=IRRequestBody(
            content={"application/json": IRSchema(type="object", name="MyInputBody")},
            required=True,
            description="The request body payload.",
        ),
        responses=[
            IRResponse(
                status_code="200",
                description="Successful operation.",
                content={"application/json": IRSchema(name="MySuccessOutput", type="object")},
            ),
            IRResponse(status_code="400", description="Invalid input provided.", content={}),
            IRResponse(status_code="404", description="Resource not found.", content={}),
        ],
        tags=["pets"],
    )


@pytest.fixture
def render_context_mock_for_docstring() -> MagicMock:
    mock = MagicMock(spec=RenderContext)
    mock.name_sanitizer = MagicMock()
    mock.name_sanitizer.sanitize_class_name.side_effect = lambda name: name
    mock.name_sanitizer.sanitize_method_name.side_effect = lambda name: name
    mock.add_typing_imports_for_type = MagicMock()
    mock.add_model_import = MagicMock()
    mock.add_exception_import = MagicMock()
    mock.core_package_name = "test_client.core"
    return mock


@pytest.fixture
def code_writer_mock_for_docstring() -> MagicMock:
    return MagicMock(spec=CodeWriter)


@pytest.fixture
def schemas_for_docstring() -> Dict[str, Any]:
    return {
        "MyInputBody": IRSchema(type="object", name="MyInputBody"),
        "MySuccessOutput": IRSchema(
            type="object", name="MySuccessOutput", properties={"data": IRSchema(type="string")}
        ),
    }


class TestEndpointDocstringGenerator:
    """
    Tests for the EndpointDocstringGenerator.
    Ensures docstrings are generated correctly based on IROperation details.
    """

    def test_generate_docstring__full_op__writes_expected_docstring_parts(
        self,
        op_for_docstring: IROperation,
        render_context_mock_for_docstring: MagicMock,
        code_writer_mock_for_docstring: MagicMock,
        schemas_for_docstring: Dict[str, Any],
    ) -> None:
        """
        Scenario:
            An IROperation with summary, description, parameters, request body, and responses is provided.
            The EndpointDocstringGenerator is invoked.
        Expected Outcome:
            The CodeWriter receives lines forming a complete Python docstring.
            Docstring includes summary, description, args (path, query, body), returns, and raises sections.
            Imports for parameter types, return types, and exception types are registered with the context.
        """
        # Arrange
        generator = EndpointDocstringGenerator(schemas=schemas_for_docstring)
        primary_content_type = "application/json"

        # Mock helper functions used by generate_docstring internally
        def mock_get_param_type(param_ir: IRParameter, context: RenderContext, schemas: Dict[str, Any]) -> str:
            if param_ir.name == "path_id":
                return "int"
            if param_ir.name == "query_opt":
                return "Optional[str]"
            return "Any"

        def mock_get_request_body_type(
            req_body_ir: IRRequestBody, context: RenderContext, schemas: Dict[str, Any]
        ) -> str:
            if req_body_ir.content and "application/json" in req_body_ir.content:
                schema_name = req_body_ir.content["application/json"].name
                if schema_name == "MyInputBody":
                    return "MyInputBody"
            return "Any"

        # Create ResponseStrategy for the test
        success_response = op_for_docstring.responses[0]  # 200 response
        response_strategy = ResponseStrategy(
            return_type="MySuccessOutput",
            response_schema=success_response.content["application/json"],
            is_streaming=False,
            response_ir=success_response,
        )

        with (
            patch(
                "pyopenapi_gen.visit.endpoint.generators.docstring_generator.get_param_type",
                side_effect=mock_get_param_type,
            ) as patched_get_param_type,
            patch(
                "pyopenapi_gen.visit.endpoint.generators.docstring_generator.get_request_body_type",
                side_effect=mock_get_request_body_type,
            ) as patched_get_req_body_type,
        ):
            # Act
            generator.generate_docstring(
                code_writer_mock_for_docstring,
                op_for_docstring,
                render_context_mock_for_docstring,
                primary_content_type,
                response_strategy,
            )

        # Assert
        assert code_writer_mock_for_docstring.write_line.call_count > 5
        written_lines = "\n".join([
            call_args[0][0] for call_args in code_writer_mock_for_docstring.write_line.call_args_list
        ])

        if op_for_docstring.summary:
            assert op_for_docstring.summary in written_lines
        if op_for_docstring.description:
            assert op_for_docstring.description in written_lines

        assert "Args:" in written_lines
        assert "path_id" in written_lines
        assert "(int)" in written_lines
        assert "The ID in the path." in written_lines

        assert "query_opt" in written_lines
        assert "(Optional[str])" in written_lines
        assert "An optional query param." in written_lines

        assert "body" in written_lines
        assert "(MyInputBody)" in written_lines
        assert "The request body payload." in written_lines
        assert "(json)" in written_lines

        assert "Returns:" in written_lines
        assert "MySuccessOutput" in written_lines
        assert "Successful operation." in written_lines

        assert "Raises:" in written_lines
        assert "HTTPError" in written_lines
        assert "400: Invalid input provided." in written_lines
        assert "404: Resource not found." in written_lines

        patched_get_param_type.assert_any_call(
            op_for_docstring.parameters[0], render_context_mock_for_docstring, schemas_for_docstring
        )
        patched_get_param_type.assert_any_call(
            op_for_docstring.parameters[1], render_context_mock_for_docstring, schemas_for_docstring
        )
        if op_for_docstring.request_body:
            patched_get_req_body_type.assert_called_once_with(
                op_for_docstring.request_body, render_context_mock_for_docstring, schemas_for_docstring
            )
        # Uses ResponseStrategy directly instead of computing return type

        # These assertions are removed because the helper functions that would make these calls
        # (get_param_type, get_request_body_type, get_return_type) are mocked in this test.
        # The responsibility for these calls lies with the actual helper functions, which should
        # be tested separately.
        # render_context_mock_for_docstring.add_typing_imports_for_type.assert_any_call("int")
        # render_context_mock_for_docstring.add_typing_imports_for_type.assert_any_call("Optional[str]")
        # render_context_mock_for_docstring.add_typing_imports_for_type.assert_any_call("MyInputBody")
        # render_context_mock_for_docstring.add_typing_imports_for_type.assert_any_call("MySuccessOutput")

        # This import is for Optional itself if it appears in a type string,
        # and add_typing_imports_for_type should handle it if it sees Optional[...].
        # However, if get_param_type directly returns "Optional[str]", the context needs to see "Optional"
        # to import it. This test relies on the mock returning "Optional[str]".
        # Let's assume that add_typing_imports_for_type, if called with "Optional[str]" by the *actual* get_param_type,
        # would then trigger context.add_import("typing", "Optional"). Since get_param_type is mocked,
        # we cannot directly test that chain here. The EndpointImportAnalyzer tests this more directly.
        # For now, let's remove this too, as it depends on unmocked behavior of a mocked dependency.
        # render_context_mock_for_docstring.add_import.assert_any_call("typing", "Optional")
