"""
DocumentationWriter: Utility for generating well-formatted, Google-style Python docstrings.

This module provides the DocumentationWriter and DocumentationBlock classes, which are responsible
for building comprehensive, type-rich docstrings for generated Python code. It supports argument
alignment, line wrapping, and section formatting for Args, Returns, and Raises.
"""

from typing import List, Optional, Tuple, Union

from .line_writer import LineWriter


class DocumentationBlock:
    """
    Data container for docstring content.

    Attributes:
        summary (Optional[str]): The summary line for the docstring.
        description (Optional[str]): The detailed description.
        args (Optional[List[Union[Tuple[str, str, str], Tuple[str, str]]]]):
            List of arguments as (name, type, desc) or (type, desc) tuples.
        returns (Optional[Tuple[str, str]]): The return type and description.
        raises (Optional[List[Tuple[str, str]]]): List of (exception type, description) tuples.
    """

    def __init__(
        self,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        args: Optional[List[Union[Tuple[str, str, str], Tuple[str, str]]]] = None,
        returns: Optional[Tuple[str, str]] = None,
        raises: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        """
        Initialize a DocumentationBlock.

        Args:
            summary (Optional[str]): The summary line.
            description (Optional[str]): The detailed description.
            args (Optional[List[Union[Tuple[str, str, str], Tuple[str, str]]]]): Arguments.
            returns (Optional[Tuple[str, str]]): Return type and description.
            raises (Optional[List[Tuple[str, str]]]): Exceptions.
        """
        self.summary: Optional[str] = summary
        self.description: Optional[str] = description
        self.args: List[Union[Tuple[str, str, str], Tuple[str, str]]] = args or []
        self.returns: Optional[Tuple[str, str]] = returns
        self.raises: List[Tuple[str, str]] = raises or []


class DocumentationFormatter:
    """
    Handles low-level formatting, wrapping, and alignment for docstring lines using LineWriter.
    """

    def __init__(self, width: int = 88, min_desc_col: int = 30) -> None:
        self.width: int = width
        self.min_desc_col: int = min_desc_col

    def wrap(self, text: str, indent: int, prefix: Optional[str] = None) -> List[str]:
        if not text:
            return []
        writer = LineWriter(max_width=self.width)
        for _ in range(indent // len(writer.indent_str)):
            writer.indent()
        if prefix is not None:
            writer.append(prefix)
        writer.append_wrapped(text)
        return writer.getvalue().splitlines()

    def get_arg_prefix(self, arg: Union[Tuple[str, str, str], Tuple[str, str]]) -> str:
        if len(arg) == 3:
            name, typ, _ = arg
            return f"{name} ({typ})"
        return f"{arg[0]}"

    def render_short_prefix_arg(self, prefix: str, desc: str, indent: int, desc_col: int) -> List[str]:
        writer = LineWriter(max_width=self.width)
        for _ in range(indent // len(writer.indent_str)):
            writer.indent()
        writer.append(prefix)
        writer.move_to_column(desc_col)
        writer.append(": ")
        writer.append_wrapped(desc)
        return writer.getvalue().splitlines()

    def render_long_prefix_arg(
        self,
        prefix: str,
        desc: str,
        indent: int,
        min_col: int,
    ) -> List[str]:
        writer = LineWriter(max_width=self.width)
        for _ in range(indent // len(writer.indent_str)):
            writer.indent()
        writer.append(prefix)
        writer.newline()
        writer.move_to_column(min_col)
        writer.append(": ")
        # writer.move_to_column(min_col + 2)
        writer.append_wrapped(desc)
        return writer.getvalue().splitlines()


class DocstringSectionRenderer:
    """
    Renders Args, Returns, and Raises sections for Google-style docstrings using LineWriter.
    """

    def __init__(self, formatter: DocumentationFormatter) -> None:
        self.formatter = formatter

    def _render_short_prefix_arg(self, prefix: str, desc: str, indent: int, min_col: int) -> list[str]:
        return self.formatter.render_short_prefix_arg(prefix, desc, indent, min_col)

    def _render_exact_prefix_arg(self, prefix: str, desc: str, indent: int, min_col: int) -> list[str]:
        return self.formatter.render_short_prefix_arg(prefix, desc, indent, min_col)

    def _render_long_prefix_arg(self, prefix: str, desc: str, indent: int, min_col: int) -> list[str]:
        return self.formatter.render_long_prefix_arg(prefix, desc, indent, min_col)

    def render_args(self, args: List[Union[Tuple[str, str, str], Tuple[str, str]]], indent: int) -> List[str]:
        lines: List[str] = []
        min_col = self.formatter.min_desc_col
        for arg in args:
            prefix = self.formatter.get_arg_prefix(arg)
            desc = arg[2] if len(arg) == 3 else arg[1]
            prefix_len = indent + len(prefix)
            if prefix_len < min_col:
                lines.extend(self._render_short_prefix_arg(prefix, desc, indent, min_col))
            elif prefix_len == min_col:
                lines.extend(self._render_exact_prefix_arg(prefix, desc, indent, min_col))
            else:
                lines.extend(self._render_long_prefix_arg(prefix, desc, indent, min_col))
        return lines

    def render_returns(self, returns: Tuple[str, str], indent: int) -> List[str]:
        typ, desc = returns
        prefix = f"{typ}:"
        writer = LineWriter(max_width=self.formatter.width)
        for _ in range(indent // len(writer.indent_str)):
            writer.indent()
        writer.append(prefix)
        writer.append(" ")
        writer.append_wrapped(desc)
        return writer.getvalue().splitlines()

    def render_raises(self, raises: List[Tuple[str, str]], indent: int) -> List[str]:
        writer = LineWriter(max_width=self.formatter.width)
        for _ in range(indent // len(writer.indent_str)):
            writer.indent()
        if not raises:
            return writer.lines
        writer.append("HttpError:")
        for code, desc in raises:
            writer.newline()
            writer.append(f"    {code}:")
            if desc.strip():
                writer.append(" ")
                writer.append_wrapped(desc)
        return writer.getvalue().splitlines()


class DocumentationWriter:
    """
    Renders a DocumentationBlock into a Google-style Python docstring.
    Delegates all formatting to DocumentationFormatter and section rendering to DocstringSectionRenderer.
    """

    def __init__(self, width: int = 88, min_desc_col: int = 30) -> None:
        """
        Initialize a DocumentationWriter.

        Args:
            width (int): The maximum line width for wrapping (default: 88).
            min_desc_col (int): The minimum column for aligning descriptions (default: 30).
        """
        self.formatter = DocumentationFormatter(width=width, min_desc_col=min_desc_col)
        self.section_renderer = DocstringSectionRenderer(self.formatter)
        self.width = width
        self.min_desc_col = min_desc_col

    def render_docstring(self, doc: DocumentationBlock, indent: int = 0) -> str:
        """
        Render a Google-style docstring from a DocumentationBlock.

        Args:
            doc (DocumentationBlock): The docstring structure to render.
            indent (int): The indentation level (in spaces) for the docstring block.

        Returns:
            str: The formatted docstring as a string.
        """
        lines: List[str] = []
        lines.append(f'"""')
        # Summary
        if doc.summary:
            lines.extend(self.formatter.wrap(doc.summary, indent))
        # Description
        if doc.description:
            if doc.summary:
                lines.append("")
            lines.extend(self.formatter.wrap(doc.description, indent))
        # Args
        if doc.args:
            lines.append("")
            lines.append("Args:")
            lines.extend(self.section_renderer.render_args(doc.args, indent + 4))
        # Returns
        if doc.returns:
            lines.append("")
            lines.append("Returns:")
            lines.extend(self.section_renderer.render_returns(doc.returns, indent + 4))
        # Raises
        if doc.raises:
            lines.append("")
            lines.append("Raises:")
            lines.extend(self.section_renderer.render_raises(doc.raises, indent + 4))
        lines.append('"""')
        return "\n".join(lines)
