"""
Generator for creating mock method implementations.

This module generates mock methods that raise NotImplementedError,
allowing users to create test doubles by subclassing and overriding
only the methods they need.
"""

from typing import Any

from ....context.render_context import RenderContext
from ....core.utils import NameSanitizer
from ....core.writers.code_writer import CodeWriter
from ....ir import IROperation
from .endpoint_method_generator import EndpointMethodGenerator


class MockGenerator:
    """
    Generates mock method implementations for testing.

    Mock methods preserve the exact signature of the real implementation
    but raise NotImplementedError with helpful error messages instead
    of performing actual operations.
    """

    def __init__(self, schemas: dict[str, Any] | None = None) -> None:
        self.schemas = schemas or {}
        self.method_generator = EndpointMethodGenerator(self.schemas)

    def generate(self, op: IROperation, context: RenderContext) -> str:
        """
        Generate a mock method that raises NotImplementedError.

        Args:
            op: The operation to generate a mock for
            context: Render context for import tracking

        Returns:
            Complete mock method code as string
        """
        # Generate the full method using EndpointMethodGenerator
        full_method = self.method_generator.generate(op, context)

        # Parse and transform it to a mock implementation
        return self._transform_to_mock(full_method, op)

    def _transform_to_mock(self, full_method_code: str, op: IROperation) -> str:
        """
        Transform a full method implementation into a mock that raises NotImplementedError.

        Args:
            full_method_code: Complete method code from EndpointMethodGenerator
            op: The operation (for generating error messages)

        Returns:
            Mock method code with NotImplementedError body
        """
        lines = full_method_code.split("\n")
        writer = CodeWriter()

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Handle @overload decorator - keep it
            if stripped.startswith("@overload"):
                writer.write_line(stripped)
                i += 1

                # Copy overload signature until we hit `: ...`
                while i < len(lines):
                    sig_line = lines[i]
                    sig_stripped = sig_line.strip()
                    writer.write_line(sig_stripped)

                    if sig_stripped.endswith(": ..."):
                        writer.write_line("")  # Blank line after overload
                        i += 1
                        break

                    i += 1
                continue

            # Handle method definition (async def or def)
            if (stripped.startswith("async def ") or stripped.startswith("def ")) and "(" in stripped:
                # Determine if this is an async generator
                is_async_generator = False

                # Collect signature lines to check return type
                signature_lines = []
                temp_i = i
                while temp_i < len(lines):
                    sig_stripped = lines[temp_i].strip()
                    signature_lines.append(sig_stripped)
                    if sig_stripped.endswith(":") and not sig_stripped.endswith(","):
                        # Check if AsyncIterator in return type
                        full_sig = " ".join(signature_lines)
                        is_async_generator = "AsyncIterator" in full_sig
                        break
                    temp_i += 1

                # Write signature lines
                for sig in signature_lines:
                    writer.write_line(sig)

                # Write mock body
                writer.indent()

                # Docstring
                writer.write_line('"""')
                writer.write_line("Mock implementation that raises NotImplementedError.")
                writer.write_line("")
                writer.write_line("Override this method in your test subclass to provide")
                writer.write_line("the behavior needed for your test scenario.")
                writer.write_line('"""')

                # Error message
                method_name = NameSanitizer.sanitize_method_name(op.operation_id)
                tag = op.tags[0] if op.tags else "Client"
                class_name = f"Mock{NameSanitizer.sanitize_class_name(tag)}Client"
                error_msg = (
                    f'"{class_name}.{method_name}() not implemented. ' f'Override this method in your test subclass."'
                )
                writer.write_line(f"raise NotImplementedError({error_msg})")

                # For async generators, add unreachable yield for type checker
                if is_async_generator:
                    writer.write_line("yield  # pragma: no cover")

                writer.dedent()

                # Skip the rest of this method implementation in the original code
                i = len(lines)  # Exit the loop
                break

            i += 1

        return writer.get_code()
