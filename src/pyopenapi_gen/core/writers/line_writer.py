"""
LineWriter: Utility for building and formatting lines of text with precise control over indentation and width.

This class is designed for use in both code and documentation generation, providing methods to append text, start
new lines, and query the current line's width.
"""

from typing import List


class LineWriter:
    """
    Utility for building lines of text with indentation and width tracking.

    Attributes:
        lines (List[str]): The accumulated lines of text.
        indent_level (int): The current indentation level.
        indent_str (str): The string used for one indentation level (default: 4 spaces).
        max_width (int): The maximum line width for wrapping.
    """

    def __init__(self, indent_str: str = "    ", max_width: int = 80) -> None:
        """
        Initialize a new LineWriter with a single empty line, indentation state, and max line width.
        Args:
            indent_str (str): The string used for one indentation level (default: 4 spaces).
            max_width (int): The maximum line width for wrapping (default: 80).
        """
        self.lines: List[str] = [""]
        self.indent_level: int = 0
        self.indent_str: str = indent_str
        self._just_newlined: bool = True
        self.max_width: int = max_width

    def indent(self) -> None:
        """
        Increase the indentation level by one.
        """
        self.indent_level += 1

    def dedent(self) -> None:
        """
        Decrease the indentation level by one (never below zero).
        """
        self.indent_level = max(0, self.indent_level - 1)

    def append(self, text: str) -> None:
        """
        Append text to the current line, respecting current indentation if the line is empty and was just newlined.
        Args:
            text (str): The text to append.
        """
        if self.lines[-1] == "" and self._just_newlined:
            self.lines[-1] = self.indent_str * self.indent_level + text
        else:
            self.lines[-1] += text
        self._just_newlined = False

    def newline(self) -> None:
        """
        Start a new line, with current indentation.
        """
        self.lines.append("")
        self._just_newlined = True

    def current_width(self) -> int:
        """
        Get the width (number of characters) of the current line.
        Returns:
            int: The width of the current line.
        """
        return len(self.lines[-1])

    def current_line(self) -> str:
        """
        Get the current line.
        """
        return self.lines[-1]

    def getvalue(self) -> str:
        """
        Get the full text as a single string, joined by newlines.
        Returns:
            str: The full text.
        """
        return "\n".join(self.lines)

    def wrap_and_append(self, text: str, width: int, prefix: str = "") -> None:
        """
        Wrap the given text to the specified width and append it, using the given prefix for the first line.
        Args:
            text (str): The text to wrap and append.
            width (int): The maximum line width.
            prefix (str): The prefix for the first line (default: empty).
        """
        import textwrap

        wrapped = textwrap.wrap(text, width=width, initial_indent=prefix, subsequent_indent=" " * len(prefix))
        for i, line in enumerate(wrapped):
            if i > 0:
                self.newline()
            self.append(line)

    def _get_current_column(self) -> int:
        """
        Get the current column of the cursor.
        """

        line_width = self.current_width()
        if line_width == 0:
            return self.indent_level * len(self.indent_str)
        return line_width

    def append_wrapped(self, text: str) -> None:
        """
        Append text to the current line, wrapping as needed.

        The first line wraps at (self.max_width - current cursor position), so wrapping always respects the available
        space on the current line, including indentation and any already-appended text. Subsequent lines wrap
        at (self.max_width - current column), and are aligned to the current column at the time of the call.

        Args:
            text (str): The text to append and wrap.
        """
        import textwrap

        if not text:
            return
        wrap_col = self._get_current_column()
        first_line_width = self.max_width - wrap_col
        if first_line_width <= 0:
            self.newline()
            wrap_col = self._get_current_column()
            first_line_width = self.max_width - wrap_col

        prefix = self.current_line()
        while len(prefix) < wrap_col:
            prefix += " "
        wrap_col = max(wrap_col, len(prefix))

        wrapper = textwrap.TextWrapper(
            width=self.max_width,
            initial_indent="",
            subsequent_indent=" " * wrap_col,
            break_long_words=True,
            break_on_hyphens=True,
        )
        wrapped_lines = wrapper.wrap(prefix + text)
        if wrapped_lines:
            self.replace_current_line(wrapped_lines[0])
            for line in wrapped_lines[1:]:
                self.newline()
                self.replace_current_line(line)

    def replace_current_line(self, line: str) -> None:
        """
        Replace the current line with the given line.
        """
        self.lines[-1] = line

    def move_to_column(self, col: int) -> None:
        """
        Pad the current line with spaces until the cursor is at column col.
        Args:
            col (int): The target column to move the cursor to.
        """
        current = len(self.lines[-1])
        if current < col:
            self.lines[-1] += " " * (col - current - 1)
        # If already at or past col, do nothing

    def append_wrapped_at_column(self, text: str, width: int, col: int | None = None) -> None:
        """
        Append text, wrapping as needed, so that the first line continues from the current position,
        and all subsequent lines start at column `col`.

        If `col` is None, the current line width at the time of the call is used as the wrap column.
        This allows ergonomic alignment after any prefix or content.

        Args:
            text (str)          : The text to append and wrap.
            width (int)         : The maximum line width.
            col (int | None) : The column at which to start wrapped lines. If None, uses current
                                  line width.
        """
        import textwrap

        if not text:
            return  # Do nothing for empty text
        # Determine wrap column
        wrap_col = self.current_width() if col is None else col
        # First line: fill up to current position, then append as much as fits
        current = len(self.lines[-1])
        available = max(0, width - current)
        if available <= 0:
            # No space left, start a new line at wrap_col
            self.newline()
            self.move_to_column(wrap_col)
            current = len(self.lines[-1])
            available = max(0, width - current)
        words = text.split()
        first_line = ""

        while words and len(first_line) + len(words[0]) + (1 if first_line else 0) <= available:
            if first_line:
                first_line += " "
            first_line += words.pop(0)
        if first_line:
            self.append(first_line)
        # Remaining lines: wrap at width, start at wrap_col
        if words:
            rest = " ".join(words)
            wrapped = textwrap.wrap(rest, width=width - wrap_col)
            for line in wrapped:
                self.newline()
                self.move_to_column(wrap_col)
                self.append(line)
