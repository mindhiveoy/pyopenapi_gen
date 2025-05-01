"""
CodeWriter: Utility for building indented, well-formatted Python code blocks.

This module provides the CodeWriter class, which is responsible for managing code indentation,
writing lines and blocks, and supporting wrapped output for code and docstrings. It is designed
to be used by code generation visitors and emitters to ensure consistent, readable output.
"""

from typing import List, Optional

from .line_writer import LineWriter


class CodeWriter:
    """
    Utility for writing indented code blocks with support for line wrapping and function signatures.

    Attributes:
        writer (LineWriter): The LineWriter instance used for writing lines and blocks.
    """

    def __init__(self, indent_str: str = "    ", max_width: int = 120) -> None:
        """
        Initialize a new CodeWriter.

        Args:
            indent_str (str): The string to use for one indentation level (default: 4 spaces).
            max_width (int): The maximum line width for wrapping (default: 120).
        """
        self.writer = LineWriter(indent_str=indent_str, max_width=max_width)

    def write_line(self, line: str = "") -> None:
        """
        Write a single line, respecting the current indentation level.

        Args:
            line (str): The line to write. Defaults to an empty line.
        """
        self.writer.append(line)
        self.writer.newline()

    def indent(self) -> None:
        """
        Increase the indentation level by one.
        """
        self.writer.indent()

    def dedent(self) -> None:
        """
        Decrease the indentation level by one (never below zero).
        """
        self.writer.dedent()

    def write_block(self, code: str) -> None:
        """
        Write a multi-line code block using the current indentation level.
        Each non-empty line is prefixed with the current indentation.
        Preserves empty lines.

        Args:
            code (str): The code block to write (may be multiple lines).
        """
        for line in code.splitlines():
            self.write_line(line)

    def get_code(self) -> str:
        """
        Get the full code as a single string.

        Returns:
            str: The accumulated code, joined by newlines.
        """
        return self.writer.getvalue().rstrip("\n")

    def write_wrapped_line(self, text: str, width: int = 120) -> None:
        """
        Write a line (or lines) wrapped to the given width, respecting current indentation.

        Args:
            text (str): The text to write and wrap.
            width (int): The maximum line width (default: 120).
        """
        # Temporarily set max_width for this operation
        old_width = self.writer.max_width
        self.writer.max_width = width
        self.writer.append_wrapped(text)
        self.writer.newline()
        self.writer.max_width = old_width

    def write_function_signature(
        self, name: str, args: List[str], return_type: Optional[str] = None, async_: bool = False
    ) -> None:
        """
        Write a function or method signature, with each argument on its own line and correct indentation.

        Args:
            name (str): The function or method name.
            args (list): The list of argument strings.
            return_type (str): The return type annotation, if any.
            async_ (bool): Whether to emit 'async def' (default: False).
        """
        def_prefix = "async def" if async_ else "def"
        if args:
            self.write_line(f"{def_prefix} {name}(")
            self.indent()
            for arg in args:
                self.write_line(f"{arg},")
            self.dedent()
            if return_type:
                self.write_line(f") -> {return_type}:")
            else:
                self.write_line("):")
        else:
            if return_type:
                self.write_line(f"{def_prefix} {name}(self) -> {return_type}:")
            else:
                self.write_line(f"{def_prefix} {name}(self):")

    def write_wrapped_docstring_line(self, prefix: str, text: str, width: int = 88) -> None:
        """
        Write a docstring line (or lines) wrapped to the given width, with wrapped lines
        indented to align after the prefix (for Args, Returns, etc).

        Args:
            prefix (str): The prefix for the first line (e.g., 'param (type): ').
            text (str): The docstring text to wrap.
            width (int): The maximum line width (default: 88).
        """
        # Temporarily set max_width for this operation
        old_width = self.writer.max_width
        self.writer.max_width = width
        self.writer.append(prefix)
        self.writer.append_wrapped(text)
        self.writer.newline()
        self.writer.max_width = old_width
