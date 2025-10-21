import logging
from typing import Any

from pyopenapi_gen import IROperation

from ....context.render_context import RenderContext
from ....core.utils import Formatter
from ....core.writers.code_writer import CodeWriter
from ....types.strategies import ResponseStrategyResolver
from ..processors.import_analyzer import EndpointImportAnalyzer
from ..processors.parameter_processor import EndpointParameterProcessor
from .docstring_generator import EndpointDocstringGenerator
from .overload_generator import OverloadMethodGenerator
from .request_generator import EndpointRequestGenerator
from .response_handler_generator import EndpointResponseHandlerGenerator
from .signature_generator import EndpointMethodSignatureGenerator
from .url_args_generator import EndpointUrlArgsGenerator

# Get logger instance
logger = logging.getLogger(__name__)


class EndpointMethodGenerator:
    """
    Generates the Python code for a single endpoint method.
    """

    def __init__(self, schemas: dict[str, Any] | None = None) -> None:
        self.schemas = schemas or {}
        self.formatter = Formatter()
        self.parameter_processor = EndpointParameterProcessor(self.schemas)
        self.import_analyzer = EndpointImportAnalyzer(self.schemas)
        self.signature_generator = EndpointMethodSignatureGenerator(self.schemas)
        self.docstring_generator = EndpointDocstringGenerator(self.schemas)
        self.url_args_generator = EndpointUrlArgsGenerator(self.schemas)
        self.request_generator = EndpointRequestGenerator(self.schemas)
        self.response_handler_generator = EndpointResponseHandlerGenerator(self.schemas)
        self.overload_generator = OverloadMethodGenerator(self.schemas)

    def generate(self, op: IROperation, context: RenderContext) -> str:
        """
        Generate a fully functional async endpoint method for the given operation.
        Returns the method code as a string.

        If the operation has multiple content types, generates @overload signatures
        followed by the implementation method with runtime dispatch.
        """
        context.add_import(f"{context.core_package_name}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")

        # UNIFIED RESPONSE STRATEGY: Resolve once, use everywhere
        strategy_resolver = ResponseStrategyResolver(self.schemas)
        response_strategy = strategy_resolver.resolve(op, context)

        # Pass the response strategy to import analyzer for consistent import resolution
        self.import_analyzer.analyze_and_register_imports(op, context, response_strategy)

        # Check if operation has multiple content types
        if self.overload_generator.has_multiple_content_types(op):
            return self._generate_overloaded_method(op, context, response_strategy)
        else:
            return self._generate_standard_method(op, context, response_strategy)

    def _generate_standard_method(self, op: IROperation, context: RenderContext, response_strategy: Any) -> str:
        """Generate standard method without overloads."""
        writer = CodeWriter()

        ordered_params, primary_content_type, resolved_body_type = self.parameter_processor.process_parameters(
            op, context
        )

        # Pass strategy to generators for consistent behavior
        self.signature_generator.generate_signature(writer, op, context, ordered_params, response_strategy)

        self.docstring_generator.generate_docstring(writer, op, context, primary_content_type, response_strategy)

        # Snapshot of code *before* main body parts are written
        # This includes signature and docstring.
        code_snapshot_before_body_parts = writer.get_code()

        has_header_params = self.url_args_generator.generate_url_and_args(
            writer, op, context, ordered_params, primary_content_type, resolved_body_type
        )
        self.request_generator.generate_request_call(writer, op, context, has_header_params, primary_content_type)

        # Call the new response handler generator with strategy
        self.response_handler_generator.generate_response_handling(writer, op, context, response_strategy)

        # Check if any actual statements were added for the body
        current_full_code = writer.get_code()
        # The part of the code added by the body-writing methods
        body_part_actually_written = current_full_code[len(code_snapshot_before_body_parts) :]

        body_is_effectively_empty = True
        # Check if the written body part contains any non-comment, non-whitespace lines
        if body_part_actually_written.strip():  # Check if non-whitespace exists at all
            if any(
                line.strip() and not line.strip().startswith("#") for line in body_part_actually_written.splitlines()
            ):
                body_is_effectively_empty = False

        if body_is_effectively_empty:
            writer.write_line("pass")

        writer.dedent()  # This matches the indent() from _write_method_signature

        return writer.get_code().strip()

    def _generate_overloaded_method(self, op: IROperation, context: RenderContext, response_strategy: Any) -> str:
        """Generate method with @overload signatures for multiple content types."""
        parts = []

        # Generate overload signatures
        overload_sigs = self.overload_generator.generate_overload_signatures(op, context, response_strategy)
        parts.extend(overload_sigs)

        # Generate implementation method
        impl_method = self._generate_implementation_method(op, context, response_strategy)
        parts.append(impl_method)

        # Join with double newlines between overloads and implementation
        return "\n\n".join(parts)

    def _generate_implementation_method(self, op: IROperation, context: RenderContext, response_strategy: Any) -> str:
        """Generate the implementation method with runtime dispatch for multiple content types."""
        # Type narrowing: request_body is guaranteed to exist when this method is called
        assert (
            op.request_body is not None
        ), "request_body should not be None in _generate_implementation_method"  # nosec B101 - Type narrowing for mypy, validated by has_multiple_content_types

        writer = CodeWriter()

        # Import DataclassSerializer for automatic conversion
        context.add_import(f"{context.core_package_name}.utils", "DataclassSerializer")

        # Generate implementation signature (accepts all content-type parameters as optional)
        impl_sig = self.overload_generator.generate_implementation_signature(op, context, response_strategy)
        writer.write_block(impl_sig)

        # Generate docstring
        ordered_params, primary_content_type, _ = self.parameter_processor.process_parameters(op, context)
        writer.indent()
        writer.write_line('"""')
        writer.write_line(f"{op.summary or op.operation_id}")
        writer.write_line("")
        writer.write_line("Supports multiple content types:")
        for content_type in op.request_body.content.keys():
            writer.write_line(f"- {content_type}")
        writer.write_line('"""')

        # Generate URL construction
        writer.write_line(f'url = f"{{self.base_url}}{op.path}"')
        writer.write_line("")

        # Generate runtime dispatch logic
        writer.write_line("# Runtime dispatch based on content type")

        first_content_type = True
        for content_type in op.request_body.content.keys():
            param_info = self.overload_generator._get_content_type_param_info(
                content_type, op.request_body.content[content_type], context
            )

            if first_content_type:
                writer.write_line(f"if {param_info['name']} is not None:")
                first_content_type = False
            else:
                writer.write_line(f"elif {param_info['name']} is not None:")

            writer.indent()

            # Generate request call for this content type
            if content_type == "application/json":
                writer.write_line(f"json_body = DataclassSerializer.serialize({param_info['name']})")
                writer.write_line("response = await self._transport.request(")
                writer.indent()
                writer.write_line(f'"{op.method.value.upper()}", url,')
                writer.write_line("params=None,")
                writer.write_line("json=json_body,")
                writer.write_line("headers=None")
                writer.dedent()
                writer.write_line(")")
            elif content_type == "multipart/form-data":
                # Files dict is already in correct format for httpx - pass directly
                writer.write_line("response = await self._transport.request(")
                writer.indent()
                writer.write_line(f'"{op.method.value.upper()}", url,')
                writer.write_line("params=None,")
                writer.write_line(f"files={param_info['name']},")
                writer.write_line("headers=None")
                writer.dedent()
                writer.write_line(")")
            else:
                writer.write_line(f"data = DataclassSerializer.serialize({param_info['name']})")
                writer.write_line("response = await self._transport.request(")
                writer.indent()
                writer.write_line(f'"{op.method.value.upper()}", url,')
                writer.write_line("params=None,")
                writer.write_line("data=data,")
                writer.write_line("headers=None")
                writer.dedent()
                writer.write_line(")")

            writer.dedent()

        # Add else clause for error
        writer.write_line("else:")
        writer.indent()
        writer.write_line('raise ValueError("One of the content-type parameters must be provided")')
        writer.dedent()
        writer.write_line("")

        # Generate response handling (reuse existing generator)
        self.response_handler_generator.generate_response_handling(writer, op, context, response_strategy)

        writer.dedent()

        return writer.get_code().strip()
