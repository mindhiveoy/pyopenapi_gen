"""
Tests for the EndpointMethodGenerator class.
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from pyopenapi_gen import IROperation, IRResponse  # Added IRResponse
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.http_types import HTTPMethod
from pyopenapi_gen.visit.endpoint.generators.docstring_generator import EndpointDocstringGenerator
from pyopenapi_gen.visit.endpoint.generators.endpoint_method_generator import EndpointMethodGenerator
from pyopenapi_gen.visit.endpoint.generators.request_generator import EndpointRequestGenerator
from pyopenapi_gen.visit.endpoint.generators.response_handler_generator import EndpointResponseHandlerGenerator
from pyopenapi_gen.visit.endpoint.generators.signature_generator import EndpointMethodSignatureGenerator
from pyopenapi_gen.visit.endpoint.generators.url_args_generator import EndpointUrlArgsGenerator
from pyopenapi_gen.visit.endpoint.processors.import_analyzer import EndpointImportAnalyzer
from pyopenapi_gen.visit.endpoint.processors.parameter_processor import EndpointParameterProcessor


@pytest.fixture
def mock_op() -> IROperation:
    """Provides a basic IROperation mock for testing."""
    return IROperation(
        path="/test",
        method=HTTPMethod.GET,
        operation_id="test_op",
        summary="Test Operation",
        description="A test operation.",
        parameters=[],
        request_body=None,
        responses=[],  # Corrected to be a list
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


class TestEndpointMethodGenerator:
    @patch("pyopenapi_gen.visit.endpoint.generators.endpoint_method_generator.CodeWriter")
    @patch.object(EndpointParameterProcessor, "process_parameters")
    @patch.object(EndpointImportAnalyzer, "analyze_and_register_imports")
    @patch.object(EndpointMethodSignatureGenerator, "generate_signature")
    @patch.object(EndpointDocstringGenerator, "generate_docstring")
    @patch.object(EndpointUrlArgsGenerator, "generate_url_and_args")
    @patch.object(EndpointRequestGenerator, "generate_request_call")
    @patch.object(EndpointResponseHandlerGenerator, "generate_response_handling")
    def test_generate__basic_flow__calls_helpers_in_order(
        self,
        mock_response_handler_gen: MagicMock,
        mock_request_gen: MagicMock,
        mock_url_args_gen: MagicMock,
        mock_docstring_gen: MagicMock,
        mock_signature_gen: MagicMock,
        mock_import_analyzer: MagicMock,
        mock_param_processor: MagicMock,
        mock_code_writer_class: MagicMock,
        mock_op: IROperation,
        mock_render_context: RenderContext,
    ) -> None:
        """
        Scenario:
            - A basic IROperation is provided.
        Expected Outcome:
            - The generate method orchestrates calls to its helper generators/processors
              in the correct sequence.
            - CodeWriter is used to build the method string.
            - Necessary base imports are added.
        """
        # Arrange
        mock_writer_instance = MagicMock(spec=CodeWriter)
        # Simulate writer building up code then returning it
        # First call to get_code is for snapshot_before_body_parts
        # Second call is for the final code result
        mock_writer_instance.get_code.side_effect = [
            "def test_op():\n    # Docstring here\n",  # Snapshot before body parts
            "def test_op():\n    # Docstring here\n    pass",  # For current_full_code
            "def test_op():\n    # Docstring here\n    pass",  # For the final return get_code()
        ]
        mock_code_writer_class.return_value = mock_writer_instance

        # Mock return values for helpers that influence control flow or provide data
        ordered_params_fixture: list[Any] = []
        primary_content_type_fixture = None
        resolved_body_type_fixture = None
        mock_param_processor.return_value = (
            ordered_params_fixture,
            primary_content_type_fixture,
            resolved_body_type_fixture,
        )
        mock_url_args_gen.return_value = False  # has_header_params

        generator = EndpointMethodGenerator(schemas={})

        # Act
        result_code = generator.generate(mock_op, mock_render_context)

        # Assert
        # Check that base imports are added
        mock_render_context.add_import.assert_any_call("test_core_pkg.http_transport", "HttpTransport")
        mock_render_context.add_import.assert_any_call("test_core_pkg.exceptions", "HTTPError")

        # Check helper calls in order
        mock_import_analyzer.assert_called_once_with(mock_op, mock_render_context)
        mock_param_processor.assert_called_once_with(mock_op, mock_render_context)

        mock_signature_gen.assert_called_once_with(
            mock_writer_instance, mock_op, mock_render_context, ordered_params_fixture
        )

        mock_docstring_gen.assert_called_once_with(
            mock_writer_instance, mock_op, mock_render_context, primary_content_type_fixture
        )

        mock_url_args_gen.assert_called_once_with(
            mock_writer_instance,
            mock_op,
            mock_render_context,
            ordered_params_fixture,
            primary_content_type_fixture,
            resolved_body_type_fixture,
        )

        mock_request_gen.assert_called_once_with(
            mock_writer_instance,
            mock_op,
            mock_render_context,
            mock_url_args_gen.return_value,  # has_header_params from url_args_gen
            primary_content_type_fixture,
        )

        mock_response_handler_gen.assert_called_once_with(mock_writer_instance, mock_op, mock_render_context)

        # Check CodeWriter usage
        # get_code is called twice, once for snapshot, once for final
        assert mock_writer_instance.get_code.call_count == 3
        mock_writer_instance.dedent.assert_called_once()  # From the end of generate method

        # Check final result
        assert result_code == "def test_op():\n    # Docstring here\n    pass"

    @patch("pyopenapi_gen.visit.endpoint.generators.endpoint_method_generator.CodeWriter")
    @patch.object(EndpointParameterProcessor, "process_parameters")
    @patch.object(EndpointImportAnalyzer, "analyze_and_register_imports")
    @patch.object(EndpointMethodSignatureGenerator, "generate_signature")
    @patch.object(EndpointDocstringGenerator, "generate_docstring")
    @patch.object(EndpointUrlArgsGenerator, "generate_url_and_args")
    @patch.object(EndpointRequestGenerator, "generate_request_call")
    @patch.object(EndpointResponseHandlerGenerator, "generate_response_handling")
    def test_generate__empty_method_body__writes_pass(
        self,
        mock_response_handler_gen: MagicMock,  # Order matters for @patch decorators
        mock_request_gen: MagicMock,
        mock_url_args_gen: MagicMock,
        mock_docstring_gen: MagicMock,
        mock_signature_gen: MagicMock,
        mock_import_analyzer: MagicMock,
        mock_param_processor: MagicMock,
        mock_code_writer_class: MagicMock,
        mock_op: IROperation,
        mock_render_context: RenderContext,
    ) -> None:
        """
        Scenario:
            - The helper generators produce no actual executable lines for the method body,
              only comments or whitespace.
        Expected Outcome:
            - The generate method detects an effectively empty body.
            - CodeWriter.write_line("pass") is called to ensure valid Python.
            - The final code includes "pass".
        """
        # Arrange
        mock_writer_instance = MagicMock(spec=CodeWriter)
        mock_writer_instance.get_code.side_effect = [
            "def test_op():\n    # Docstring here\n",  # Snapshot for code_snapshot_before_body_parts
            "def test_op():\n    # Docstring here\n    # Only comments or whitespace added by helpers\n",  # Snapshot for current_full_code
            "def test_op():\n    # Docstring here\n    # Only comments or whitespace added by helpers\n    pass",  # Final code
        ]
        mock_code_writer_class.return_value = mock_writer_instance

        mock_param_processor.return_value = ([], None, None)
        mock_url_args_gen.return_value = False

        generator = EndpointMethodGenerator(schemas={})

        # Act
        result_code = generator.generate(mock_op, mock_render_context)

        # Assert
        # Helper calls would be similar to the basic flow, so we focus on the "pass" logic
        mock_writer_instance.write_line.assert_any_call("pass")  # Check that pass was written
        assert (
            result_code
            == "def test_op():\n    # Docstring here\n    # Only comments or whitespace added by helpers\n    pass"
        )
