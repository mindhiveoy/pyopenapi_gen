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

    def generate(self, op: IROperation, context: RenderContext) -> str:
        """
        Generate a fully functional async endpoint method for the given operation.
        Returns the method code as a string.
        """
        writer = CodeWriter()
        context.add_import(f"{context.core_package_name}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")

        # UNIFIED RESPONSE STRATEGY: Resolve once, use everywhere
        strategy_resolver = ResponseStrategyResolver(self.schemas)
        response_strategy = strategy_resolver.resolve(op, context)

        # Pass the response strategy to import analyzer for consistent import resolution
        self.import_analyzer.analyze_and_register_imports(op, context, response_strategy)

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
