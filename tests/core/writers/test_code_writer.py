from pyopenapi_gen.core.writers.code_writer import CodeWriter


def test_write_line_and_get_code() -> None:
    writer = CodeWriter()
    writer.write_line("foo")
    writer.write_line("bar")
    assert writer.get_code() == "foo\nbar"


def test_indent_and_dedent() -> None:
    writer = CodeWriter()
    writer.write_line("a")
    writer.indent()
    writer.write_line("b")
    writer.dedent()
    writer.write_line("c")
    assert writer.get_code() == "a\n    b\nc"


def test_dedent_below_zero() -> None:
    writer = CodeWriter()
    writer.dedent()
    writer.write_line("x")
    assert writer.get_code() == "x"


def test_write_block() -> None:
    writer = CodeWriter()
    block = "foo\nbar\n\nbaz"
    writer.write_block(block)
    assert writer.get_code() == "foo\nbar\n\nbaz"


def test_write_wrapped_line() -> None:
    writer = CodeWriter()
    long_text = "This is a very long line that should be wrapped at a certain width for readability."
    writer.write_wrapped_line(long_text, width=40)
    lines = writer.get_code().splitlines()
    assert all(len(line) <= 40 for line in lines)
    assert "This is a very long line that should be" in lines[0]


def test_write_function_signature_sync() -> None:
    writer = CodeWriter()
    writer.write_function_signature("foo", ["a: int", "b: str"], return_type="str", async_=False)
    code = writer.get_code()
    assert "def foo(" in code
    assert "a: int," in code
    assert "b: str," in code
    assert ") -> str:" in code


def test_write_function_signature_async() -> None:
    writer = CodeWriter()
    writer.write_function_signature("bar", ["x: int = 1"], return_type=None, async_=True)
    code = writer.get_code()
    assert "async def bar(" in code
    assert "x: int = 1," in code
    assert "):" in code


def test_write_wrapped_docstring_line() -> None:
    writer = CodeWriter()
    prefix = "param (str): "
    text = "This is a long description that should wrap and align under the prefix for clarity."
    writer.write_wrapped_docstring_line(prefix, text, width=50)
    lines = writer.get_code().splitlines()
    assert lines[0].startswith(prefix)
    assert all(len(line) <= 50 for line in lines)
    # Wrapped lines should be indented after the prefix
    assert lines[1].startswith(" " * len(prefix))


def test_codewriter__write_wrapped_line__wraps_long_lines() -> None:
    """
    Scenario:
        Write a long line using CodeWriter.write_wrapped_line with a small width.
    Expected Outcome:
        The output is split into multiple lines, each not exceeding the specified width, and indentation is preserved.
    """

    writer = CodeWriter()
    long_text = (
        "This is a very long line that should be wrapped by the CodeWriter at the specified width for readability."
    )
    writer.indent()
    writer.write_wrapped_line(long_text, width=40)
    code = writer.get_code()
    lines = code.splitlines()
    # All lines should be <= 40 chars (plus indentation)
    for line in lines:
        assert len(line.strip()) <= 40
    # Should be more than one line
    assert len(lines) > 1
    # Indentation should be present
    for line in lines:
        assert line.startswith("    ")
