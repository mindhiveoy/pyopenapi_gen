import logging
from typing import Any

from pyopenapi_gen import IROperation

# No longer need endpoint utils helpers - using ResponseStrategy pattern
from ...context.render_context import RenderContext
from ...core.utils import NameSanitizer
from ...core.writers.code_writer import CodeWriter
from ..protocol_helpers import ProtocolGenerator
from ..visitor import Visitor
from .generators.endpoint_method_generator import EndpointMethodGenerator

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
        self.protocol_generator = ProtocolGenerator()
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
        operations: list[IROperation] | None = None,
    ) -> str:
        """
        Emit the endpoint client class for a tag, aggregating all endpoint methods.
        The generated class is fully type-annotated and uses HttpTransport for HTTP communication.
        Args:
            tag: The tag name for the endpoint group.
            method_codes: List of method code blocks as strings.
            context: The RenderContext for import tracking.
            operations: List of operations for Protocol generation (optional for backwards compatibility).
        """
        # Generate Protocol if operations provided
        protocol_code = ""
        if operations:
            protocol_code = self.generate_endpoint_protocol(tag, operations, context)

        # Generate implementation
        impl_code = self._generate_endpoint_implementation(tag, method_codes, context)

        # Combine Protocol and implementation
        if protocol_code:
            return f"{protocol_code}\n\n\n{impl_code}"
        else:
            return impl_code

    def generate_endpoint_protocol(self, tag: str, operations: list[IROperation], context: RenderContext) -> str:
        """
        Generate Protocol definition for tag-based endpoint client.

        Args:
            tag: The tag name for the endpoint group
            operations: List of operations for this tag
            context: Render context for import management

        Returns:
            Protocol class code as string with all operation method signatures
        """
        # Register Protocol imports
        context.add_import("typing", "Protocol")
        context.add_import("typing", "runtime_checkable")

        writer = CodeWriter()
        class_name = NameSanitizer.sanitize_class_name(tag) + "Client"
        protocol_name = f"{class_name}Protocol"

        # Protocol class header
        writer.write_line("@runtime_checkable")
        writer.write_line(f"class {protocol_name}(Protocol):")
        writer.indent()

        # Docstring
        writer.write_line(f'"""Protocol defining the interface of {class_name} for dependency injection."""')
        writer.write_line("")

        # Generate method signatures from operations
        # We need to extract complete signatures including multi-line ones and decorators
        # For Protocol, we only include the method signatures with ..., not implementations
        # IMPORTANT: Preserve multi-line formatting for readability
        for op in operations:
            method_generator = EndpointMethodGenerator(schemas=self.schemas)
            full_method_code = method_generator.generate(op, context)

            # Parse the generated code to extract method signatures
            # We want: @overload stubs (already have ...) and final signature converted to stub
            lines = full_method_code.split("\n")
            i = 0

            while i < len(lines):
                line = lines[i]
                stripped = line.strip()

                # Handle @overload decorator
                if stripped.startswith("@overload"):
                    # Write decorator
                    writer.write_line(stripped)
                    i += 1

                    # Now process the signature following the decorator
                    # Keep collecting lines until we hit the end of the overload signature
                    while i < len(lines):
                        sig_line = lines[i]
                        sig_stripped = sig_line.strip()

                        # Write each line of the signature
                        writer.write_line(sig_stripped)

                        # Check for end of overload signature (ends with `: ...`)
                        if sig_stripped.endswith(": ..."):
                            writer.write_line("")  # Blank line after overload
                            i += 1
                            break

                        i += 1
                    continue

                # Handle non-overload method signatures (the final implementation signature)
                if stripped.startswith("async def ") and "(" in stripped:
                    # This is the start of a method signature
                    # We need to collect all lines until we hit the colon
                    signature_lines = []

                    # Collect signature lines
                    while i < len(lines):
                        sig_line = lines[i]
                        sig_stripped = sig_line.strip()

                        signature_lines.append(sig_stripped)

                        # Check if this completes the signature (ends with :)
                        if sig_stripped.endswith(":") and not sig_stripped.endswith(","):
                            # This is the final line of the signature
                            # For Protocol, convert to stub format

                            # Check if this is an async generator (returns AsyncIterator)
                            # If so, remove 'async' from the first line
                            is_async_generator = "AsyncIterator" in sig_stripped

                            # Write all lines except the last
                            for idx, sig in enumerate(signature_lines[:-1]):
                                # For async generators, remove 'async ' from method definition
                                if idx == 0 and is_async_generator and sig.startswith("async def "):
                                    sig = sig.replace("async def ", "def ", 1)
                                writer.write_line(sig)

                            # Write last line with ... instead of :
                            last_line = signature_lines[-1]
                            if last_line.endswith(":"):
                                last_line = last_line[:-1]  # Remove trailing :
                            writer.write_line(f"{last_line}: ...")
                            writer.write_line("")  # Blank line after method

                            # For Protocol, we only want the signature stub, not the implementation
                            # Skip all remaining lines of this method by jumping to end
                            i = len(lines)  # This will exit the while loop
                            break

                        i += 1
                    continue

                i += 1

        writer.dedent()  # Close class
        return writer.get_code()

    def _generate_endpoint_implementation(self, tag: str, method_codes: list[str], context: RenderContext) -> str:
        """
        Generate the endpoint client implementation class.

        Args:
            tag: The tag name for the endpoint group
            method_codes: List of method code blocks as strings
            context: Render context for import management

        Returns:
            Implementation class code as string
        """
        context.add_import("typing", "cast")
        # Import core transport and streaming helpers
        context.add_import(f"{context.core_package_name}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package_name}.streaming_helpers", "iter_bytes")
        context.add_import("typing", "Callable")
        context.add_import("typing", "Optional")
        writer = CodeWriter()
        class_name = NameSanitizer.sanitize_class_name(tag) + "Client"
        protocol_name = f"{class_name}Protocol"

        # Class definition - implements Protocol
        writer.write_line(f"class {class_name}({protocol_name}):")
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

    def generate_endpoint_mock_class(self, tag: str, operations: list[IROperation], context: RenderContext) -> str:
        """
        Generate mock implementation class for tag-based endpoint client.

        Args:
            tag: The tag name for the endpoint group
            operations: List of operations for this tag
            context: Render context for import management

        Returns:
            Mock class code as string with all operation method stubs
        """
        from .generators.mock_generator import MockGenerator

        # Import Protocol for type checking
        context.add_import("typing", "TYPE_CHECKING")

        writer = CodeWriter()
        class_name = NameSanitizer.sanitize_class_name(tag) + "Client"
        protocol_name = f"{class_name}Protocol"
        mock_class_name = f"Mock{class_name}"

        # TYPE_CHECKING import for Protocol
        writer.write_line("if TYPE_CHECKING:")
        writer.indent()
        writer.write_line(f"from ...endpoints.{NameSanitizer.sanitize_module_name(tag)} import {protocol_name}")
        writer.dedent()
        writer.write_line("")

        # Class header with docstring
        writer.write_line(f"class {mock_class_name}:")
        writer.indent()
        writer.write_line('"""')
        writer.write_line(f"Mock implementation of {class_name} for testing.")
        writer.write_line("")
        writer.write_line("Provides default implementations that raise NotImplementedError.")
        writer.write_line("Override methods as needed in your tests.")
        writer.write_line("")
        writer.write_line("Example:")
        writer.write_line(f"    class Test{class_name}({mock_class_name}):")
        writer.write_line("        async def method_name(self, ...) -> ReturnType:")
        writer.write_line("            return test_data")
        writer.write_line('"""')
        writer.write_line("")

        # Generate mock methods
        mock_generator = MockGenerator(schemas=self.schemas)
        for i, op in enumerate(operations):
            mock_method_code = mock_generator.generate(op, context)
            writer.write_block(mock_method_code)

            if i < len(operations) - 1:
                writer.write_line("")  # Blank line between methods
                writer.write_line("")  # Second blank line for consistency

        writer.dedent()  # Close class
        return writer.get_code()
