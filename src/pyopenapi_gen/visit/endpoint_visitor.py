import logging
from typing import Any

from pyopenapi_gen import IROperation
from pyopenapi_gen.helpers.endpoint_utils import (
    get_param_type,
    get_params,
    get_request_body_type,
    get_return_type,
)
from pyopenapi_gen.helpers.url_utils import extract_url_variables

from ..context.render_context import RenderContext
from ..core.utils import Formatter, NameSanitizer
from ..core.writers.code_writer import CodeWriter
from ..core.writers.documentation_writer import DocumentationBlock, DocumentationWriter
from .visitor import Visitor
from .endpoint_method_generator import EndpointMethodGenerator

# Get logger instance
logger = logging.getLogger(__name__)


class EndpointVisitor(Visitor[IROperation, str]):
    """
    Visitor for rendering a Python endpoint client method/class from an IROperation.
    The method generation part is delegated to EndpointMethodGenerator.
    This class remains responsible for assembling methods into a class (emit_endpoint_client_class).
    Returns the rendered code as a string (does not write files).
    """

    def __init__(self, schemas: dict[str, Any] | None = None) -> None:
        self.schemas = schemas or {}
        # Formatter is likely not needed here anymore if all formatting happens in EndpointMethodGenerator
        # self.formatter = Formatter()

    def visit_IROperation(self, op: IROperation, context: RenderContext) -> str:
        """
        Generate a fully functional async endpoint method for the given operation
        by delegating to EndpointMethodGenerator.
        Returns the method code as a string.
        """
        # Instantiate the new generator
        method_generator = EndpointMethodGenerator(schemas=self.schemas)
        return method_generator.generate(op, context)

    def emit_endpoint_client_class(
        self,
        tag: str,
        method_codes: list[str],
        context: RenderContext,
    ) -> str:
        """
        Emit the endpoint client class for a tag, aggregating all endpoint methods.
        The generated class is fully type-annotated and uses HttpTransport for HTTP communication.
        Args:
            tag: The tag name for the endpoint group.
            method_codes: List of method code blocks as strings.
            context: The RenderContext for import tracking.
        """
        context.add_import("typing", "cast")
        # Import core transport and streaming helpers
        context.add_import(f"{context.core_package_name}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
        context.add_import("typing", "Callable")
        context.add_import("typing", "Optional")
        writer = CodeWriter()
        class_name = NameSanitizer.sanitize_class_name(tag) + "Client"
        writer.write_line(f"class {class_name}:")
        writer.indent()
        writer.write_line(f'"""Client for {tag} endpoints. Uses HttpTransport for all HTTP and header management."""')
        writer.write_line("")

        writer.write_line("def __init__(self, transport: HttpTransport, base_url: str) -> None:")
        writer.indent()
        writer.write_line("self._transport = transport")
        writer.write_line("self.base_url: str = base_url")
        writer.dedent()
        writer.write_line("")

        # Write methods
        for i, method_code in enumerate(method_codes):
            # Revert to write_block, as it handles indentation correctly
            writer.write_block(method_code)

            if i < len(method_codes) - 1:
                writer.write_line("")  # First blank line
                writer.write_line("")  # Second blank line (for testing separation)

        writer.dedent()  # Dedent to close the class block
        return writer.get_code()
