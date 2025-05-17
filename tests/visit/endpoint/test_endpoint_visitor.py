"""
Tests for the EndpointVisitor class.
"""

from unittest.mock import MagicMock, patch

import pytest

from pyopenapi_gen import IROperation, IRResponse
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.visit.endpoint.endpoint_visitor import EndpointVisitor
from pyopenapi_gen.visit.endpoint.generators.endpoint_method_generator import EndpointMethodGenerator


@pytest.fixture
def mock_op_for_visitor() -> IROperation:
    """Provides a basic IROperation for visitor tests."""
    return IROperation(
        path="/visit_test",
        method=HTTPMethod.POST,
        operation_id="visit_test_op",
        summary="Visit Test Operation",
        description="A test operation for the visitor.",
        parameters=[],
        request_body=None,
        responses=[],
    )


@pytest.fixture
def mock_context_for_visitor() -> RenderContext:
    """Provides a RenderContext mock for visitor tests."""
    mock = MagicMock(spec=RenderContext)
    mock.core_package_name = "test_core_pkg"
    mock.import_collector = MagicMock()
    mock.add_import = MagicMock()
    return mock


class TestEndpointVisitor:
    @patch("pyopenapi_gen.visit.endpoint.endpoint_visitor.EndpointMethodGenerator")
    def test_visit_IROperation__delegates_to_EndpointMethodGenerator__returns_generated_code(
        self,
        MockEndpointMethodGenerator: MagicMock,  # Patched class
        mock_op_for_visitor: IROperation,
        mock_context_for_visitor: RenderContext,
    ) -> None:
        """
        Scenario:
            - visit_IROperation is called with an IROperation and RenderContext.
        Expected Outcome:
            - EndpointMethodGenerator is instantiated with the visitor's schemas.
            - The generate method of EndpointMethodGenerator is called with the op and context.
            - The result from EndpointMethodGenerator.generate is returned.
        """
        # Arrange
        schemas = {"TestSchema": MagicMock()}
        visitor = EndpointVisitor(schemas=schemas)

        mock_method_generator_instance = MagicMock(spec=EndpointMethodGenerator)
        expected_generated_code = "def visit_test_op(): pass"  # Mock generated code
        mock_method_generator_instance.generate.return_value = expected_generated_code
        MockEndpointMethodGenerator.return_value = mock_method_generator_instance

        # Act
        result_code = visitor.visit_IROperation(mock_op_for_visitor, mock_context_for_visitor)

        # Assert
        MockEndpointMethodGenerator.assert_called_once_with(schemas=schemas)
        mock_method_generator_instance.generate.assert_called_once_with(mock_op_for_visitor, mock_context_for_visitor)
        assert result_code == expected_generated_code

    @patch("pyopenapi_gen.visit.endpoint.endpoint_visitor.CodeWriter")
    @patch("pyopenapi_gen.visit.endpoint.endpoint_visitor.NameSanitizer.sanitize_class_name")
    def test_emit_endpoint_client_class__basic_case__generates_class_with_methods(
        self,
        mock_sanitize_class_name: MagicMock,
        mock_code_writer_class: MagicMock,
        mock_context_for_visitor: RenderContext,  # Use existing fixture
    ) -> None:
        """
        Scenario:
            - emit_endpoint_client_class is called with a tag, a list of method code strings,
              and a RenderContext.
        Expected Outcome:
            - A string representing a Python class is generated.
            - The class includes an __init__ method and the provided method codes.
            - Necessary imports are added to the context.
            - NameSanitizer is used for the class name.
            - CodeWriter is used to construct the code.
        """
        # Arrange
        tag = "User Operations"
        method_codes = [
            "def get_user(self, user_id: int) -> User:\n    pass",
            "def create_user(self, data: UserCreate) -> User:\n    pass",
        ]
        schemas = {"User": MagicMock(), "UserCreate": MagicMock()}  # Schemas for completeness if visitor used them
        visitor = EndpointVisitor(schemas=schemas)

        mock_writer_instance = MagicMock(spec=CodeWriter)
        mock_writer_instance.get_code.return_value = "class UserOperationsClient:\n    # ... (full mocked code)"
        mock_code_writer_class.return_value = mock_writer_instance

        sanitized_class_name_base = "UserOperations"
        mock_sanitize_class_name.return_value = sanitized_class_name_base

        # Act
        generated_class_code = visitor.emit_endpoint_client_class(tag, method_codes, mock_context_for_visitor)

        # Assert
        # Check context imports
        mock_context_for_visitor.add_import.assert_any_call("typing", "cast")
        mock_context_for_visitor.add_import.assert_any_call(
            f"{mock_context_for_visitor.core_package_name}.http_transport", "HttpTransport"
        )
        mock_context_for_visitor.add_import.assert_any_call(
            f"{mock_context_for_visitor.core_package_name}.streaming_helpers", "iter_bytes"
        )
        mock_context_for_visitor.add_import.assert_any_call("typing", "Callable")
        mock_context_for_visitor.add_import.assert_any_call("typing", "Optional")

        # Check NameSanitizer call
        mock_sanitize_class_name.assert_called_once_with(tag)

        # Check CodeWriter calls (selected important calls)
        mock_writer_instance.write_line.assert_any_call(f"class {sanitized_class_name_base}Client:")
        mock_writer_instance.write_line.assert_any_call(
            "def __init__(self, transport: HttpTransport, base_url: str) -> None:"
        )
        mock_writer_instance.write_line.assert_any_call("self._transport = transport")
        mock_writer_instance.write_line.assert_any_call("self.base_url: str = base_url")

        # Check that each method code was written
        for method_code in method_codes:
            mock_writer_instance.write_block.assert_any_call(method_code)

        assert mock_writer_instance.indent.call_count >= 2  # For class and __init__
        assert mock_writer_instance.dedent.call_count >= 2  # For class and __init__

        # Check final returned code (can be a more specific check if needed)
        assert generated_class_code == "class UserOperationsClient:\n    # ... (full mocked code)"
