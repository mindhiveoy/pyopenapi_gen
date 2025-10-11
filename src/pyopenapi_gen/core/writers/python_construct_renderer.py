"""
PythonConstructRenderer: Renders Python language constructs like classes, enums, and type aliases.

This module provides the PythonConstructRenderer class, which is responsible for
generating well-formatted Python code for common constructs used in the generated client.
It handles all the details of formatting, import registration, and docstring generation
for these constructs.
"""

from typing import List, Tuple

from pyopenapi_gen.context.render_context import RenderContext

from .code_writer import CodeWriter
from .documentation_writer import DocumentationBlock, DocumentationWriter


class PythonConstructRenderer:
    """
    Generates Python code for common constructs like dataclasses, enums, and type aliases.

    This class provides methods to render different Python language constructs with
    proper formatting, documentation, and import handling. It uses CodeWriter and
    DocumentationWriter internally to ensure consistent output and automatically
    registers necessary imports into the provided RenderContext.

    The renderer handles:
    - Type aliases (e.g., UserId = str)
    - Enums (with str or int values)
    - Dataclasses (with required and optional fields)
    - Generic classes (with bases, docstrings, and body)
    """

    def render_alias(
        self,
        alias_name: str,
        target_type: str,
        description: str | None,
        context: RenderContext,
    ) -> str:
        """
        Render a type alias assignment as Python code.

        Args:
            alias_name: The name for the type alias
            target_type: The target type expression
            description: Optional description for the docstring
            context: The rendering context for import registration

        Returns:
            Formatted Python code for the type alias

        Example:
            ```python
            # Assuming: from typing import TypeAlias
            UserId: TypeAlias = str
            '''Alias for a user identifier'''  # Reverted to triple-single for example
            ```
        """
        writer = CodeWriter()
        # Add TypeAlias import
        context.add_import("typing", "TypeAlias")
        # Register imports needed by the target type itself
        context.add_typing_imports_for_type(target_type)

        # Add __all__ export
        writer.write_line(f'__all__ = ["{alias_name}"]')
        writer.write_line("")  # Add a blank line for separation

        writer.write_line(f"{alias_name}: TypeAlias = {target_type}")
        if description:
            # Sanitize description for use within a triple-double-quoted string for the actual docstring
            safe_desc_content = description.replace("\\", "\\\\")  # Escape backslashes first
            safe_desc_content = safe_desc_content.replace('"""', '\\"\\"\\"')  # Escape triple-double-quotes
            writer.write_line(f'"""Alias for {safe_desc_content}"""')  # Actual generated docstring uses """
        return writer.get_code()

    def render_enum(
        self,
        enum_name: str,
        base_type: str,  # 'str' or 'int'
        values: List[Tuple[str, str | int]],  # List of (MEMBER_NAME, value)
        description: str | None,
        context: RenderContext,
    ) -> str:
        """
        Render an Enum class as Python code.

        Args:
            enum_name: The name of the enum class
            base_type: The base type, either 'str' or 'int'
            values: List of (member_name, value) pairs
            description: Optional description for the docstring
            context: The rendering context for import registration

        Returns:
            Formatted Python code for the enum class

        Example:
            ```python
            @unique
            class Color(str, Enum):
                \"\"\"Color options available in the API\"\"\"
                RED = "red"
                GREEN = "green"
                BLUE = "blue"
            ```
        """
        writer = CodeWriter()
        context.add_import("enum", "Enum")
        context.add_import("enum", "unique")

        # Add __all__ export
        writer.write_line(f'__all__ = ["{enum_name}"]')
        writer.write_line("")  # Add a blank line for separation

        writer.write_line("@unique")
        writer.write_line(f"class {enum_name}(" + base_type + ", Enum):")
        writer.indent()

        # Build and write docstring
        doc_args: list[tuple[str, str, str] | tuple[str, str]] = []
        for member_name, value in values:
            doc_args.append((str(value), base_type, f"Value for {member_name}"))
        doc_block = DocumentationBlock(
            summary=description or f"{enum_name} Enum",
            args=doc_args if doc_args else None,
        )
        docstring = DocumentationWriter(width=88).render_docstring(doc_block, indent=0)
        for line in docstring.splitlines():
            writer.write_line(line)

        # Write Enum members
        for member_name, value in values:
            if base_type == "str":
                writer.write_line(f'{member_name} = "{value}"')
            else:  # int
                writer.write_line(f"{member_name} = {value}")

        writer.dedent()
        return writer.get_code()

    def render_dataclass(
        self,
        class_name: str,
        fields: List[Tuple[str, str, str | None, str | None]],  # name, type_hint, default_expr, description
        description: str | None,
        context: RenderContext,
        field_mappings: dict[str, str] | None = None,
    ) -> str:
        """
        Render a dataclass as Python code with BaseSchema support.

        Args:
            class_name: The name of the dataclass
            fields: List of (name, type_hint, default_expr, description) tuples for each field
            description: Optional description for the class docstring
            context: The rendering context for import registration
            field_mappings: Optional mapping of API field names to Python field names for BaseSchema

        Returns:
            Formatted Python code for the dataclass

        Example:
            ```python
            @dataclass
            class User(BaseSchema):
                \"\"\"User information with automatic JSON field mapping.\"\"\"
                id_: str
                first_name: str
                email: str | None = None
                is_active: bool = True

                class Meta:
                    \"\"\"Configure field name mapping for JSON conversion.\"\"\"
                    key_transform_with_load = {
                        'id': 'id_',
                        'firstName': 'first_name'
                    }
            ```
        """
        writer = CodeWriter()
        context.add_import("dataclasses", "dataclass")

        # Always use self-contained BaseSchema for client independence with automatic field mapping
        # Use absolute core import path - add_import will handle it correctly
        context.add_import(f"{context.core_package_name}.schemas", "BaseSchema")

        # Add __all__ export
        writer.write_line(f'__all__ = ["{class_name}"]')
        writer.write_line("")  # Add a blank line for separation

        writer.write_line("@dataclass")
        writer.write_line(f"class {class_name}(BaseSchema):")
        writer.indent()

        # Build and write docstring
        field_args: list[tuple[str, str, str] | tuple[str, str]] = []
        for name, type_hint, _, field_desc in fields:
            field_args.append((name, type_hint, field_desc or ""))

        # Enhanced description with automatic field mapping
        base_description = description or f"{class_name} dataclass"
        enhanced_description = f"{base_description} with automatic JSON field mapping."

        doc_block = DocumentationBlock(
            summary=enhanced_description,
            args=field_args if field_args else None,
        )
        docstring = DocumentationWriter(width=88).render_docstring(doc_block, indent=0)
        for line in docstring.splitlines():
            writer.write_line(line)

        # Write fields
        if not fields:
            writer.write_line("# No properties defined in schema")
            writer.write_line("pass")
        else:
            # Separate required and optional fields for correct ordering (no defaults first)
            required_fields = [f for f in fields if f[2] is None]  # default_expr is None
            optional_fields = [f for f in fields if f[2] is not None]  # default_expr is not None

            # Required fields
            for name, type_hint, _, field_desc in required_fields:
                line = f"{name}: {type_hint}"
                if field_desc:
                    comment_text = field_desc.replace("\n", " ")
                    line += f"  # {comment_text}"
                writer.write_line(line)

            # Optional fields
            for name, type_hint, default_expr, field_desc in optional_fields:
                if default_expr and "default_factory" in default_expr:
                    context.add_import("dataclasses", "field")  # Ensure field is imported
                line = f"{name}: {type_hint} = {default_expr}"
                if field_desc:
                    comment_text = field_desc.replace("\n", " ")
                    line += f"  # {comment_text}"
                writer.write_line(line)

        # Add Meta class if field mappings are provided (for BaseSchema field mapping)
        if field_mappings:
            writer.write_line("")  # Blank line before Meta class
            writer.write_line("class Meta:")
            writer.indent()
            writer.write_line('"""Configure field name mapping for JSON conversion."""')
            writer.write_line("key_transform_with_load = {")
            writer.indent()

            # Sort mappings for consistent output
            for api_field, python_field in sorted(field_mappings.items()):
                writer.write_line(f'"{api_field}": "{python_field}",')

            writer.dedent()
            writer.write_line("}")
            writer.dedent()

        writer.dedent()
        return writer.get_code()

    def render_class(
        self,
        class_name: str,
        base_classes: List[str] | None,
        docstring: str | None,
        body_lines: List[str] | None,
        context: RenderContext,
    ) -> str:
        """
        Render a generic class definition as Python code.

        Args:
            class_name: The name of the class
            base_classes: Optional list of base class names (for inheritance)
            docstring: Optional class docstring content
            body_lines: Optional list of code lines for the class body
            context: The rendering context (not used for generic classes)

        Returns:
            Formatted Python code for the class

        Example:
            ```python
            class CustomError(Exception):
                \"\"\"Raised when a custom error occurs.\"\"\"
                def __init__(self, message: str, code: int):
                    self.code = code
                    super().__init__(message)
            ```
        """
        writer = CodeWriter()
        bases = f"({', '.join(base_classes)})" if base_classes else ""
        writer.write_line(f"class {class_name}{bases}:")
        writer.indent()
        has_content = False
        if docstring:
            # Simple triple-quoted docstring is sufficient for exceptions
            writer.write_line(f'"""{docstring}"""')
            has_content = True
        if body_lines:
            for line in body_lines:
                # Handle empty lines without adding indentation (Ruff W293)
                if line == "":
                    writer.writer.newline()  # Just add a newline, no indent
                else:
                    writer.write_line(line)
            has_content = True

        if not has_content:
            writer.write_line("pass")  # Need pass if class is completely empty

        writer.dedent()
        return writer.get_code()
