"""
Helpers for generating Python Protocol definitions from IR structures.

This module provides utilities for creating Protocol classes that define
the structural interface of generated clients, enabling type-safe dependency
injection and test double creation.
"""

from ..core.writers.code_writer import CodeWriter


class ProtocolGenerator:
    """Base class for generating Protocol definitions."""

    def generate_protocol_decorator(self) -> str:
        """
        Generate @runtime_checkable decorator for Protocol classes.

        Returns:
            The decorator as a string: "@runtime_checkable"
        """
        return "@runtime_checkable"

    def generate_method_signature(
        self, method_name: str, parameters: str, return_type: str, is_async: bool = False
    ) -> str:
        """
        Generate a Protocol method signature with ellipsis body.

        Args:
            method_name: Name of the method
            parameters: Parameter list as string (e.g., "self, user_id: int")
            return_type: Return type annotation
            is_async: Whether the method is async

        Returns:
            Complete method signature with ellipsis body
        """
        async_prefix = "async " if is_async else ""
        return f"{async_prefix}def {method_name}({parameters}) -> {return_type}: ..."

    def generate_property_signature(self, property_name: str, return_type: str) -> str:
        """
        Generate a Protocol property signature.

        Args:
            property_name: Name of the property
            return_type: Return type annotation

        Returns:
            Complete property signature with @property decorator and ellipsis body
        """
        writer = CodeWriter()
        writer.write_line("@property")
        writer.write_line(f"def {property_name}(self) -> {return_type}: ...")
        return writer.get_code()

    def generate_protocol_class_header(self, protocol_name: str, docstring: str) -> str:
        """
        Generate the Protocol class header with decorator and docstring.

        Args:
            protocol_name: Name of the Protocol class
            docstring: Documentation for the Protocol

        Returns:
            Protocol class header as string
        """
        writer = CodeWriter()
        writer.write_line(self.generate_protocol_decorator())
        writer.write_line(f"class {protocol_name}(Protocol):")
        writer.indent()
        writer.write_line(f'"""{docstring}"""')
        writer.write_line("")
        writer.dedent()
        return writer.get_code()

    def combine_protocol_parts(self, protocol_name: str, docstring: str, members: list[str]) -> str:
        """
        Combine Protocol class parts into complete Protocol definition.

        Args:
            protocol_name: Name of the Protocol class
            docstring: Documentation for the Protocol
            members: List of member signatures (methods, properties)

        Returns:
            Complete Protocol class code as string
        """
        writer = CodeWriter()

        # Write decorator and class definition
        writer.write_line(self.generate_protocol_decorator())
        writer.write_line(f"class {protocol_name}(Protocol):")
        writer.indent()

        # Write docstring
        writer.write_line(f'"""{docstring}"""')
        writer.write_line("")

        # Write members
        for member in members:
            # Member might be multi-line (e.g., property with decorator)
            for line in member.split("\n"):
                if line.strip():  # Skip empty lines
                    writer.write_line(line)
            writer.write_line("")  # Blank line after each member

        writer.dedent()
        return writer.get_code()
