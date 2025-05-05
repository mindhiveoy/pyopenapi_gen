"""Renderer for common Python code constructs like classes, enums, and aliases."""

from typing import List, Optional, Tuple

from pyopenapi_gen.context.render_context import RenderContext

from .code_writer import CodeWriter
from .documentation_writer import DocumentationBlock, DocumentationWriter


class PythonConstructRenderer:
    """
    Generates Python code strings for common constructs like dataclasses, enums, and type aliases.
    Uses CodeWriter and DocumentationWriter internally.
    Registers necessary imports (e.g., dataclass, Enum) into the provided RenderContext.
    """

    def render_alias(
        self,
        alias_name: str,
        target_type: str,
        description: Optional[str],
        context: RenderContext,
    ) -> str:
        """Renders a type alias assignment (e.g., UserId = str)."""
        writer = CodeWriter()
        writer.write_line(f"{alias_name} = {target_type}")
        if description:
            # Simple docstring for alias
            writer.write_line(f'"""Alias for {description}"""')
        return writer.get_code()

    def render_enum(
        self,
        enum_name: str,
        base_type: str,  # 'str' or 'int'
        values: List[Tuple[str, str | int]],  # List of (MEMBER_NAME, value)
        description: Optional[str],
        context: RenderContext,
    ) -> str:
        """Renders an Enum class."""
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
        fields: List[Tuple[str, str, Optional[str], Optional[str]]],  # name, type_hint, default_expr, description
        description: Optional[str],
        context: RenderContext,
    ) -> str:
        """Renders a dataclass."""
        writer = CodeWriter()
        context.add_import("dataclasses", "dataclass")

        writer.write_line("@dataclass")
        writer.write_line(f"class {class_name}:")
        writer.indent()

        # Build and write docstring
        field_args: list[tuple[str, str, str] | tuple[str, str]] = []
        for name, type_hint, _, field_desc in fields:
            field_args.append((name, type_hint, field_desc or ""))
        doc_block = DocumentationBlock(
            summary=description or f"{class_name} dataclass.",
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
                    line += f"  # {field_desc.replace('\n', ' ')}"
                writer.write_line(line)

            # Optional fields
            for name, type_hint, default_expr, field_desc in optional_fields:
                if default_expr and "default_factory" in default_expr:
                    context.add_import("dataclasses", "field")  # Ensure field is imported
                line = f"{name}: {type_hint} = {default_expr}"
                if field_desc:
                    line += f"  # {field_desc.replace('\n', ' ')}"
                writer.write_line(line)

        writer.dedent()
        return writer.get_code()

    def render_class(
        self,
        class_name: str,
        base_classes: Optional[List[str]],
        docstring: Optional[str],
        body_lines: Optional[List[str]],
        context: RenderContext,
    ) -> str:
        """Renders a generic class definition."""
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
                writer.write_line(line)
            has_content = True

        if not has_content:
            writer.write_line("pass")  # Need pass if class is completely empty

        writer.dedent()
        return writer.get_code()
