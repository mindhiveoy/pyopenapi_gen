import difflib

from pyopenapi_gen.core.writers.line_writer import LineWriter


def assert_docstring_output(actual: str, expected: str) -> None:
    actual_norm = actual.strip().replace("\r\n", "\n")
    expected_norm = expected.strip().replace("\r\n", "\n")
    if actual_norm != expected_norm:
        diff = "\n".join(
            difflib.unified_diff(
                expected_norm.splitlines(),
                actual_norm.splitlines(),
                fromfile="expected",
                tofile="actual",
                lineterm="",
            )
        )
        raise AssertionError(f"Docstring output does not match expected:\n{diff}")


def test_append_and_newline() -> None:
    """
    Scenario: Appending text and starting new lines.
    Expected: Lines are accumulated correctly with indentation.
    """
    writer = LineWriter()
    writer.append("foo")
    writer.newline()
    writer.append("bar")
    assert writer.lines == ["foo", "bar"]
    assert writer.getvalue() == "foo\nbar"


def test_indent_and_dedent() -> None:
    """
    Scenario: Indenting and dedenting lines.
    Expected: Indentation is applied to new lines, dedent never goes below zero.
    """
    writer = LineWriter()
    writer.indent()
    writer.append("foo")
    writer.newline()
    writer.dedent()
    writer.append("bar")
    writer.dedent()  # Should not go below zero
    writer.newline()
    writer.append("baz")
    assert writer.lines == ["    foo", "bar", "baz"]


def test_current_width() -> None:
    """
    Scenario: Querying the current line width.
    Expected: Returns the correct width after appending.
    """
    writer = LineWriter()
    writer.append("foo")
    assert writer.current_width() == 3
    writer.append("bar")
    assert writer.current_width() == 6


def test_getvalue() -> None:
    """
    Scenario: Getting the full value as a string.
    Expected: Joins all lines with newlines.
    """
    writer = LineWriter()
    writer.append("foo")
    writer.newline()
    writer.append("bar")
    assert writer.getvalue() == "foo\nbar"


def test_wrap_and_append_basic() -> None:
    """
    Scenario: Visual check for wrapping and appending text to a line.
    Expected: Text is wrapped and appended with correct indentation and width.
    """
    writer = LineWriter(max_width=20)
    writer.append("foo: ")
    writer.append_wrapped("This is a long description that should wrap.")
    expected = f"""
foo: This is a long
     description
     that should
     wrap."""
    actual = f"""
{writer.getvalue()}"""
    assert_docstring_output(actual, expected)


def test_wrap_and_append_with_indent() -> None:
    """
    Scenario: Visual check for wrapping and appending with indentation.
    Expected: Wrapped lines align under the first line's end.
    """
    writer = LineWriter(max_width=30)
    writer.indent()
    writer.append("prefix: ")
    writer.append_wrapped("This is a long description that should wrap and align.")

    expected = f"""
    prefix: This is a long
            description that
            should wrap and
            align."""
    actual = f"""
{writer.getvalue()}"""
    assert_docstring_output(actual, expected)


def test_move_to_column() -> None:
    """
    Scenario: Visual check for moving to a specific column.
    Expected: Pads with spaces to the target column.
    """
    writer = LineWriter()
    writer.append("foo")
    writer.move_to_column(10)
    writer.append(": bar")

    expected = f"""foo      : bar"""
    actual = f"""{writer.getvalue()}"""
    assert_docstring_output(actual, expected)


def test_append_wrapped_at_column_basic() -> None:
    """
    Scenario: Visual check for append_wrapped with col so that subsequent lines start at the given column.
    Expected: All wrapped lines after the first start at the specified column.
    """
    writer = LineWriter(max_width=40)
    writer.append("foo (str)")
    writer.move_to_column(15)
    writer.append(": ")
    writer.append_wrapped(
        "This is a long description that should wrap to the next line for readability.",
    )
    expected = f"""
foo (str)     : This is a long
                description that should
                wrap to the next line
                for readability."""
    actual = f"""
{writer.getvalue()}"""
    assert_docstring_output(actual, expected)


def test_append_wrapped_at_column_prefix_longer_than_col() -> None:
    """
    Scenario: Visual check for prefix longer than the target column for wrapping.
    Expected: The first line is long, subsequent lines start at col.
    """
    writer = LineWriter(max_width=40)
    writer.append("averyveryverylongargumentname (str)")
    writer.newline()
    writer.move_to_column(10)
    writer.append(": ")
    writer.append_wrapped("Description for a very long argument name that should wrap.")
    expected = f"""
averyveryverylongargumentname (str)
         : Description for a very long
           argument name that should
           wrap."""
    actual = f"""
{writer.getvalue()}"""
    assert_docstring_output(actual, expected)


def test_append_wrapped_at_column_empty_text() -> None:
    """
    Scenario: Visual check for append_wrapped with empty text.
    Expected: No additional lines are added.
    """
    writer = LineWriter(max_width=40)
    writer.append("foo (str)")
    writer.move_to_column(15)
    writer.append(": ")
    writer.append_wrapped("")
    expected = f"""
foo (str)     : """
    actual = f"""
{writer.getvalue()}"""
    assert_docstring_output(actual, expected)


def test_wrap_exact_fit() -> None:
    """
    Scenario: Wrapping text that exactly fits the line width.
    Expected: No wrapping occurs, text remains on one line.
    """
    writer = LineWriter(max_width=20)
    writer.append_wrapped("12345678901234567890")
    expected = "12345678901234567890"
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)


def test_wrap_one_char_too_long() -> None:
    """
    Scenario: Wrapping text that is one character too long for the line width.
    Expected: The last character wraps to a new line.
    """
    writer = LineWriter(max_width=10)
    writer.append_wrapped("abcdefghijk")
    expected = "abcdefghij\nk"
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)


def test_wrap_very_long_word() -> None:
    """
    Scenario:
        Wrapping a single word longer than max_width.
        We want to verify that the word is broken across lines as per textwrap's greedy behavior.

    Expected Outcome:
        The word is split into chunks of max_width, each on its own line.
    """
    writer = LineWriter(max_width=8)
    writer.append_wrapped("supercalifragilisticexpialidocious")
    expected = """
supercal
ifragili
sticexpi
alidocio
us"""
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)


def test_wrap_leading_trailing_spaces() -> None:
    """
    Scenario:
        Wrapping text with leading, trailing, and multiple internal spaces.
        We want to verify that spaces are preserved as per textwrap's behavior.

    Expected Outcome:
        Spaces are preserved and lines are wrapped as expected.
    """
    writer = LineWriter(max_width=15)
    writer.append_wrapped("  foo   bar    baz   ")
    expected = """
foo   bar
baz"""
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)


def test_multiple_append_wrapped_calls() -> None:
    """
    Scenario: Multiple consecutive calls to append_wrapped.
    Expected: Each call continues from the current position and wraps as expected.
    """
    writer = LineWriter(max_width=25)
    writer.append_wrapped("foo bar")
    writer.append_wrapped("baz qux quux")
    expected = "foo barbaz qux quux"
    actual = writer.getvalue().replace("\n", "")  # Should be one line
    assert actual == expected.replace("\n", "")


def test_indent_dedent_between_wrapped_lines() -> None:
    """
    Scenario: Indent and dedent between wrapped lines.
    Expected: Indentation is applied to new lines after indent/dedent.
    """
    writer = LineWriter(max_width=20)
    writer.append_wrapped("foo bar baz qux quux corge grault")
    writer.newline()
    writer.indent()
    writer.append_wrapped("indented line one two three")
    writer.dedent()
    writer.newline()
    writer.append_wrapped("back to no indent")
    expected = """
foo bar baz qux quux
corge grault
    indented line
    one two three
back to no indent"""
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)


def test_move_to_column_less_than_current() -> None:
    """
    Scenario: move_to_column with col < current position.
    Expected: No change to the current line.
    """
    writer = LineWriter()
    writer.append("foo bar")
    writer.move_to_column(3)
    expected = "foo bar"
    actual = writer.getvalue()
    assert actual == expected


def test_move_to_column_exact_current() -> None:
    """
    Scenario: move_to_column to exactly the current position.
    Expected: No extra spaces are added.
    """
    writer = LineWriter()
    writer.append("foo bar")
    writer.move_to_column(7)
    expected = "foo bar"
    actual = writer.getvalue()
    assert actual == expected


def test_append_wrapped_only_whitespace() -> None:
    """
    Scenario: append_wrapped with only whitespace.
    Expected: No lines are added or only whitespace is handled as expected.
    """
    writer = LineWriter()
    writer.append_wrapped("   ")
    expected = ""
    actual = writer.getvalue()
    assert actual == expected


def test_append_wrapped_with_newlines() -> None:
    """
    Scenario: append_wrapped with embedded newlines in the input.
    Expected: Newlines are treated as spaces and text is wrapped accordingly.
    """
    writer = LineWriter(max_width=10)
    writer.append_wrapped("foo\nbar baz\nqux")
    expected = "foo bar\nbaz qux"
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)


def test_wrap_max_width_one() -> None:
    """
    Scenario: max_width = 1.
    Expected: Every character is wrapped to a new line.
    """
    writer = LineWriter(max_width=1)
    writer.append_wrapped("abc")
    expected = "a\nb\nc"
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)


def test_wrap_max_width_very_large() -> None:
    """
    Scenario: max_width is very large.
    Expected: No wrapping occurs for long text.
    """
    writer = LineWriter(max_width=1000)
    writer.append_wrapped("foo bar baz qux quux corge grault garply waldo fred plugh xyzzy thud")
    expected = "foo bar baz qux quux corge grault garply waldo fred plugh xyzzy thud"
    actual = writer.getvalue()
    assert_docstring_output(actual, expected)
