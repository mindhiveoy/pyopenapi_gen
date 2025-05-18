"""Unit tests for ParsingContext class."""

import pytest

from pyopenapi_gen.core.parsing.context import ParsingContext


def test_parsing_context_missing_methods() -> None:
    """
    Test for missing methods in ParsingContext that are needed by schema_parser.py.
    These methods were referenced in schema_parser but don't exist in ParsingContext.
    """
    context = ParsingContext()

    # These methods are missing but should be present
    assert hasattr(context, "is_schema_parsed"), "ParsingContext should have is_schema_parsed method"
    assert hasattr(context, "get_parsed_schema"), "ParsingContext should have get_parsed_schema method"

    # Test functionality of the methods (will only run if the methods exist)
    if hasattr(context, "is_schema_parsed"):
        assert not context.is_schema_parsed("non_existent_schema"), "Non-existent schema should not be parsed"

    if hasattr(context, "get_parsed_schema"):
        assert context.get_parsed_schema("non_existent_schema") is None, "Should return None for non-existent schema"
