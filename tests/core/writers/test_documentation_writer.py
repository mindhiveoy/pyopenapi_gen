from pyopenapi_gen.core.writers.documentation_writer import DocumentationBlock, DocumentationWriter


def assert_docstring_output(actual: str, expected: str) -> None:
    """
    Helper to compare actual and expected docstring output, normalizing whitespace and line endings.
    Raises AssertionError with a diff if they do not match.
    """
    import difflib

    actual_norm = actual.strip().replace("\r\n", "\n")
    expected_norm = expected.strip().replace("\r\n", "\n")
    if actual_norm != expected_norm:
        diff = "\n".join(
            difflib.unified_diff(
                expected_norm.splitlines(), actual_norm.splitlines(), fromfile="expected", tofile="actual", lineterm=""
            )
        )
        raise AssertionError(f"Docstring output does not match expected:\n{diff}")


def test_render_docstring__summary_only__renders_summary() -> None:
    """
    Scenario:
        A DocumentationBlock is created with only a summary. We want to verify that
        DocumentationWriter.render_docstring outputs a docstring containing just the summary line.

    Expected Outcome:
        The rendered docstring contains the summary and triple quotes, with no extra sections.
    """
    # Arrange
    doc = DocumentationBlock(summary="Short summary.")
    # Config: width=60, min_desc_col=30 (default)
    writer = DocumentationWriter(width=60)

    # Act
    result = writer.render_docstring(doc)
    expected = '''"""
Short summary.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__summary_and_description__renders_both() -> None:
    """
    Scenario:
        A DocumentationBlock is created with a summary and a description. We want to verify that
        both appear in the rendered docstring, separated by a blank line.

    Expected Outcome:
        The docstring contains the summary, a blank line, and the description.
    """
    # Arrange
    doc = DocumentationBlock(summary="Summary.", description="Detailed description.")
    # Config: width=60, min_desc_col=30 (default)
    writer = DocumentationWriter(width=60)

    # Act
    result = writer.render_docstring(doc)
    expected = '''"""
Summary.

Detailed description.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__args_section__renders_args_with_types_and_desc() -> None:
    """
    Scenario:
        A DocumentationBlock is created with multiple arguments, each with a name, type, and description.
        We want to verify that the Args section is rendered, with correct alignment and wrapping.

    Expected Outcome:
        The Args section lists each argument with its type and description, aligned and wrapped.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [
        ("foo", "int", "The foo param."),
        ("bar", "str", "A longer description that should wrap to the next line for readability."),
    ]
    doc = DocumentationBlock(summary="Has args.", args=args)
    # Config: width=50, min_desc_col=32
    writer = DocumentationWriter(width=50, min_desc_col=32)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4         5
    # 78901234567890123456789012345678901234567890
    #                          C D
    expected = '''"""
Has args.

Args:
    foo (int)                  : The foo param.
    bar (str)                  : A longer
                                 description that
                                 should wrap to
                                 the next line for
                                 readability.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__returns_section__renders_return_type_and_desc() -> None:
    """
    Scenario:
        A DocumentationBlock is created with a returns tuple. We want to verify that the Returns section
        is rendered with the correct type and description.

    Expected Outcome:
        The Returns section appears with the return type and description, aligned and wrapped.
    """
    # Arrange
    doc = DocumentationBlock(summary="Has return.", returns=("str", "A string result."))
    # Config: width=60, min_desc_col=30 (default)
    writer = DocumentationWriter(width=60)

    # Act
    result = writer.render_docstring(doc)
    expected = '''"""
Has return.

Returns:
    str: A string result.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__raises_section__renders_exceptions() -> None:
    """
    Scenario:
        A DocumentationBlock is created with multiple raises entries. We want to verify that the Raises
        section is rendered, with each HTTP error code and its description, properly indented and wrapped.

    Expected Outcome:
        The Raises section lists HttpError and each HTTP error code and its description, with correct indentation.
    """
    # Arrange
    raises: list[tuple[str, str]] = [
        ("400", "If the value is invalid."),
        ("404", "If the resource is not found."),
    ]
    doc = DocumentationBlock(summary="Has raises.", raises=raises)
    # Config: width=60, min_desc_col=30 (default)
    writer = DocumentationWriter(width=60)

    # Act
    result = writer.render_docstring(doc)
    expected = '''"""
Has raises.

Raises:
    HttpError:
        400: If the value is invalid.
        404: If the resource is not found.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__all_sections__renders_full_docstring() -> None:
    """
    Scenario:
        A DocumentationBlock is created with summary, description, args, returns, and raises.
        We want to verify that all sections are rendered in the correct order and format.

    Expected Outcome:
        The docstring contains all sections, each with correct content and formatting.
    """
    # Arrange
    doc = DocumentationBlock(
        summary="Full docstring.",
        description="Covers all sections.",
        args=[("x", "int", "First param."), ("y", "str", "Second param.")],
        returns=("bool", "True if success."),
        raises=[("400", "On failure.")],
    )
    # Config: width=70, min_desc_col=26
    writer = DocumentationWriter(width=70, min_desc_col=26)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4         5         6
    # 789012345678901234567890123456789012345678901234567890
    #                    C D
    expected = '''"""
Full docstring.

Covers all sections.

Args:
    x (int)              : First param.
    y (str)              : Second param.

Returns:
    bool: True if success.

Raises:
    HttpError:
        400: On failure.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__wrapping_and_alignment__long_lines_are_wrapped() -> None:
    """
    Scenario:
        A DocumentationBlock is created with long argument names and descriptions. We want to verify
        that the docstring output wraps lines at the specified width and aligns wrapped lines correctly.

    Expected Outcome:
        All lines in the docstring are within the width limit, and wrapped lines are aligned under the prefix.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [
        (
            "very_long_argument_name",
            "str",
            "This is a very long description that should wrap and align under the argument name for clarity and readability.",  # noqa: E501
        )
    ]
    doc = DocumentationBlock(summary="Wrapping test.", args=args)
    writer = DocumentationWriter(width=60, min_desc_col=25)

    # Act
    result = writer.render_docstring(doc)
    lines = result.splitlines()

    # Assert
    for line in lines:
        assert len(line) <= 60
    # Wrapped lines should be indented after the prefix
    prefix = "    very_long_argument_name (str)   : "
    for i, line in enumerate(lines):
        if line.startswith(prefix):
            if i + 1 < len(lines):
                assert lines[i + 1].startswith(" " * len(prefix))


def test_render_docstring__arg_prefix_exactly_at_desc_col__colon_and_space_on_next_line() -> None:
    """
    Scenario:
        The argument prefix length is exactly at the desc_col, so the description starts on the next line.
        We want to verify that the colon and space are present before the description.

    Expected Outcome:
        First line only has the argument name and type, and the next line is padded with a space and
        prefixed with a colon and a space followed by the description.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [
        ("averylongargumentname", "str", "Description for a long argument name.")
    ]
    writer = DocumentationWriter(width=50, min_desc_col=25)
    doc = DocumentationBlock(summary="Edge case.", args=args)

    # Act
    result = writer.render_docstring(doc)

    #    1         2         3         4         5
    # 78901234567890123456789012345678901234567890
    #                   C D
    expected = '''"""
Edge case.

Args:
    averylongargumentname (str)
                        : Description for a long
                          argument name.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__arg_prefix_longer_than_desc_col__colon_and_space_on_next_line() -> None:
    """
    Scenario:
        The argument prefix is longer than desc_col, so the description starts on the next line.
        We want to verify that the colon and space are present before the description.

    Expected Outcome:
        The prefix line ends with a colon, and the next line (description) starts with a space.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [
        ("averyveryverylongargumentnameindeed", "str", "Description for a very long argument name.")
    ]
    writer = DocumentationWriter(width=50, min_desc_col=20)
    doc = DocumentationBlock(summary="Edge case.", args=args)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4         5         6
    # 789012345678901234567890123456789012345678901234567890
    #                        C D

    expected = '''"""
Edge case.

Args:
    averyveryverylongargumentnameindeed (str)
                   : Description for a very long
                     argument name.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__arg_with_empty_description__renders_colon_only() -> None:
    """
    Scenario:
        An argument is provided with an empty description. We want to verify that the colon is still present.

    Expected Outcome:
        The prefix line ends with a colon, and no description follows.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [
        (
            "foo",
            "int",
            "",
        )
    ]
    # Config: width=50, min_desc_col=20
    writer = DocumentationWriter(width=50, min_desc_col=20)
    doc = DocumentationBlock(summary="Empty desc.", args=args)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4         5         6
    # 789012345678901234567890123456789012345678901234567890
    #              C D
    expected = '''"""
Empty desc.

Args:
    foo (int)      : 
"""'''  # noqa: W291
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__arg_with_multiline_description__all_lines_aligned() -> None:
    """
    Scenario:
        An argument is provided with a multiline description. We want to verify that all lines of the description
        are aligned under the colon, not just desc_col+1.

    Expected Outcome:
        All lines of the description are aligned under the colon, with a space after the colon.
    """
    # Arrange
    desc = "This is a long description.\nIt has multiple lines.\nEach should be aligned."
    args: list[tuple[str, str, str] | tuple[str, str]] = [("foo", "str", desc)]
    # Config: width=50, min_desc_col=20
    writer = DocumentationWriter(width=50, min_desc_col=20)
    doc = DocumentationBlock(summary="Multiline desc.", args=args)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4         5         6
    # 789012345678901234567890123456789012345678901234567890
    #              C D
    expected = '''"""
Multiline desc.

Args:
    foo (str)      : This is a long description.
                     It has multiple lines. Each
                     should be aligned.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__arg_prefix_with_unicode__renders_colon_and_space() -> None:
    """
    Scenario:
        The argument prefix contains unicode characters. We want to verify that the colon and space
        are handled correctly.

    Expected Outcome:
        The prefix line ends with a colon, and the description line starts with a space.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [("tên", "str", "Unicode argument name.")]
    # Config: width=40, min_desc_col=15
    writer = DocumentationWriter(width=40, min_desc_col=15)
    doc = DocumentationBlock(summary="Unicode prefix.", args=args)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4
    # 7890123456789012345678901234567890
    #         C D
    expected = '''"""
Unicode prefix.

Args:
    tên (str) : Unicode argument name.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__arg_prefix_with_special_characters__renders_colon_and_space() -> None:
    """
    Scenario:
        The argument prefix contains special characters. We want to verify that the colon and space are
        handled correctly.

    Expected Outcome:
        The description line starts with a colon and a space and following the description.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [("foo-bar_baz", "str", "Special chars in name.")]
    # Config: width=40, min_desc_col=15
    writer = DocumentationWriter(width=40, min_desc_col=15)
    doc = DocumentationBlock(summary="Special chars.", args=args)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4
    # 78901234567890123456789012345678901234567890
    #         C D
    expected = '''"""
Special chars.

Args:
    foo-bar_baz (str)
              : Special chars in name.
"""'''
    # Assert
    assert_docstring_output(result, expected)


def test_render_docstring__multiple_args__alignment_and_wrapping() -> None:
    """
    Scenario:
        Multiple arguments are provided, including a short description, a long description that wraps,
        and a multiline description. We want to verify that all are aligned and wrapped correctly.

    Expected Outcome:
        Each argument's description is aligned under the colon, with wrapped and multiline lines indented
        to the same column as the first line after the colon.
    """
    # Arrange
    args: list[tuple[str, str, str] | tuple[str, str]] = [
        ("foo", "int", "Short desc."),
        ("bar", "str", "This is a long description that should wrap to the next line for readability."),
        ("baz", "str", "First line.\nSecond line of multiline desc.\nThird line."),
    ]
    # Config: width=60, min_desc_col=20
    writer = DocumentationWriter(width=60, min_desc_col=20)
    doc = DocumentationBlock(summary="Multiple args.", args=args)

    # Act
    result = writer.render_docstring(doc)
    #    1         2         3         4         5         6
    # 789012345678901234567890123456789012345678901234567890
    #              C D
    expected = '''"""
Multiple args.

Args:
    foo (int)      : Short desc.
    bar (str)      : This is a long description that should
                     wrap to the next line for readability.
    baz (str)      : First line. Second line of multiline
                     desc. Third line.
"""'''
    # Assert
    assert_docstring_output(result, expected)
