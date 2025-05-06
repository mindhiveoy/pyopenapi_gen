from typing import Any
from unittest.mock import MagicMock, call  # For mocking context and writer

import pytest

from pyopenapi_gen import HTTPMethod, IROperation, IRSchema  # Corrected imports
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.visit.endpoint_method_generator import EndpointMethodGenerator


# A minimal IROperation fixture could be useful
@pytest.fixture
def minimal_op() -> IROperation:
    # This is a simplified IROperation. Adjust fields as necessary for actual tests.
    return IROperation(
        path="/test",
        method=HTTPMethod.GET,  # Corrected type
        operation_id="test_operation",
        summary="A test operation",
        description="Detailed description of test operation.",  # Added description
        tags=["test_tag"],
        parameters=[],
        request_body=None,
        responses=[],
    )


@pytest.fixture
def render_context_mock() -> MagicMock:
    mock = MagicMock(spec=RenderContext)
    mock.core_package_name = "test_core"
    # Mock any methods of RenderContext that are called by the generator
    mock.add_import = MagicMock()
    mock.add_plain_import = MagicMock()
    mock.add_typing_imports_for_type = MagicMock()
    return mock


@pytest.fixture
def schemas_mock() -> dict[str, Any]:  # Corrected type hint
    return {"SomeSchema": MagicMock(spec=IRSchema)}  # Example schema


class TestEndpointMethodGenerator:
    def test_generate_minimal_operation_returns_string(
        self, minimal_op: IROperation, render_context_mock: MagicMock, schemas_mock: dict[str, Any]
    ) -> None:  # Added type hints
        """
        Scenario:
            - A minimal IROperation is provided.
            - The EndpointMethodGenerator is invoked.
        Expected Outcome:
            - The generate method returns a non-empty string (the method code).
            - Core imports (HttpTransport, HTTPError) are added to context.
        """
        # Arrange
        generator = EndpointMethodGenerator(schemas=schemas_mock)

        # Act
        method_code = generator.generate(minimal_op, render_context_mock)

        # Assert
        assert isinstance(method_code, str)
        assert len(method_code) > 0  # Basic check that something was generated

        # Check for core imports that should always be added by generate()
        expected_transport_import = call(f"{render_context_mock.core_package_name}.http_transport", "HttpTransport")
        expected_error_import = call(f"{render_context_mock.core_package_name}.exceptions", "HTTPError")
        render_context_mock.add_import.assert_any_call(*expected_transport_import[1])
        render_context_mock.add_import.assert_any_call(*expected_error_import[1])

    def test_generate_with_updateAgentDataSource_op_id_generates_pass(
        self, render_context_mock: MagicMock, schemas_mock: dict[str, Any]
    ) -> None:  # Added type hints
        """
        Scenario:
            - An IROperation with operation_id 'updateAgentDataSource' is provided.
        Expected Outcome:
            - The generated method body should contain only 'pass'.
            - The signature should still be generated.
        """
        # Arrange
        op = IROperation(
            path="/update",
            method=HTTPMethod.POST,  # Corrected type
            operation_id="updateAgentDataSource",
            summary="Update agent data source",
            description="A description for updateAgentDataSource.",  # Added missing description
            parameters=[],
            request_body=None,
            responses=[],
        )
        generator = EndpointMethodGenerator(schemas=schemas_mock)

        # Act
        method_code = generator.generate(op, render_context_mock)

        # Assert
        # For the special 'updateAgentDataSource' case, the signature and body are hardcoded
        # by EndpointMethodGenerator. This test verifies that precise output.
        # Expected structure:
        # async def update_agent_data_source(
        #     self,
        # ) -> None:
        #     pass

        generated_code_lines = method_code.splitlines()

        # Precise check for the generated structure for this special case
        assert len(generated_code_lines) >= 4, (
            f"Expected at least 4 lines for updateAgentDataSource, got {len(generated_code_lines)}. "
            f"Code:\n{method_code}"
        )

        assert generated_code_lines[0].strip() == "async def update_agent_data_source(", (
            f"Expected 'async def update_agent_data_source(', got '{generated_code_lines[0].strip()}'"
        )
        assert generated_code_lines[1].strip() == "self,", f"Expected 'self,', got '{generated_code_lines[1].strip()}'"
        assert generated_code_lines[1].startswith("    "), (
            f"Expected 'self,' to be indented, got '{generated_code_lines[1]}'"
        )
        assert generated_code_lines[2].strip() == ") -> None:", (
            f"Expected ') -> None:', got '{generated_code_lines[2].strip()}'"
        )
        assert generated_code_lines[3].strip() == "pass", f"Expected 'pass', got '{generated_code_lines[3].strip()}'"
        assert generated_code_lines[3].startswith("    "), (
            f"Expected 'pass' to be indented, got '{generated_code_lines[3]}'"
        )

        # This general check for the indented 'pass' is also useful
        assert "    pass" in method_code

        # Assertions about helper methods not being called by checking substrings in the *single* generated output.
        # This indicates that the special 'pass' path was taken, bypassing normal generation logic.
        assert "_write_docstring" not in method_code
        assert "_write_request" not in method_code
        assert "url = f" not in method_code  # A key part of _write_url_and_args from the normal path

    # TODO: Add more tests:
    # - Test _prepare_parameters (mock dependencies, check output)
    # - Test _write_method_signature (check signature string for different param combinations)
    # - Test _write_docstring (check generated docstring content)
    # - Test _write_url_and_args (check url, params, headers assignments)
    # - Test _write_request (check transport call structure for different bodies)
    # - Test _write_response_handling (check different return types and unwrapping)
    # - Test _analyze_and_register_imports (verify context calls for various types)
    # - Test _ensure_path_variables_as_params
    # - Test _build_url_with_path_vars
    # - Test _get_extraction_code


# Removed </rewritten_file> marker
