"""
Tests for the stripped suffix fallback helper in schema reference resolution.
"""

import unittest
from typing import Any, Callable, Mapping, Optional
from unittest.mock import MagicMock

from pyopenapi_gen.core.parsing.common.ref_resolution.helpers.stripped_suffix import try_stripped_suffix_fallback
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestTryStrippedSuffixFallback(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        self.context = ParsingContext()
        self.ref_name = "TestResponse"
        self.ref_value = "#/components/schemas/TestResponse"
        self.max_depth = 100
        self.mock_parse_fn = MagicMock(
            spec=Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema]
        )

    def test_try_stripped_suffix_fallback__valid_response_suffix__returns_schema(self) -> None:
        """
        Scenario:
            - A schema reference ends with "Response" suffix
            - The base schema exists in raw_spec_schemas
            - The base schema can be parsed successfully
        Expected Outcome:
            - Returns the resolved schema
            - Registers the schema in context.parsed_schemas
            - Adds a warning to context.collected_warnings
        """
        # Arrange
        base_name = "Test"
        base_schema_data = {"type": "object"}
        self.context.raw_spec_schemas[base_name] = base_schema_data

        resolved_schema = IRSchema(name=base_name, type="object")
        self.mock_parse_fn.return_value = resolved_schema

        # Act
        result = try_stripped_suffix_fallback(
            self.ref_name, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNotNone(result)
        if result is not None:  # Type narrowing for mypy
            self.assertEqual(result.name, base_name)
            self.assertEqual(result.type, "object")
        self.assertIn(self.ref_name, self.context.parsed_schemas)
        self.assertIs(self.context.parsed_schemas[self.ref_name], result)
        self.assertTrue(any("falling back to base name" in warning for warning in self.context.collected_warnings))

    def test_try_stripped_suffix_fallback__valid_request_suffix__returns_schema(self) -> None:
        """
        Scenario:
            - A schema reference ends with "Request" suffix
            - The base schema exists in raw_spec_schemas
            - The base schema can be parsed successfully
        Expected Outcome:
            - Returns the resolved schema
            - Registers the schema in context.parsed_schemas
        """
        # Arrange
        ref_name = "TestRequest"
        base_name = "Test"
        base_schema_data = {"type": "object"}
        self.context.raw_spec_schemas[base_name] = base_schema_data

        resolved_schema = IRSchema(name=base_name, type="object")
        self.mock_parse_fn.return_value = resolved_schema

        # Act
        result = try_stripped_suffix_fallback(
            ref_name, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNotNone(result)
        if result is not None:  # Type narrowing for mypy
            self.assertEqual(result.name, base_name)
            self.assertEqual(result.type, "object")
        self.assertIn(ref_name, self.context.parsed_schemas)
        self.assertIs(self.context.parsed_schemas[ref_name], result)

    def test_try_stripped_suffix_fallback__no_matching_suffix__returns_none(self) -> None:
        """
        Scenario:
            - A schema reference does not end with any known suffix
        Expected Outcome:
            - Returns None
            - No schema is registered in context
        """
        # Arrange
        non_suffix_ref = "TestSchema"

        # Act
        result = try_stripped_suffix_fallback(
            non_suffix_ref, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(result)
        self.assertNotIn(non_suffix_ref, self.context.parsed_schemas)
        self.assertEqual(len(self.context.collected_warnings), 0)

    def test_try_stripped_suffix_fallback__base_schema_not_found__returns_none(self) -> None:
        """
        Scenario:
            - A schema reference ends with a known suffix
            - The base schema does not exist in raw_spec_schemas
        Expected Outcome:
            - Returns None
            - No schema is registered in context
        """
        # Act
        result = try_stripped_suffix_fallback(
            self.ref_name, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(result)
        self.assertNotIn(self.ref_name, self.context.parsed_schemas)
        self.assertEqual(len(self.context.collected_warnings), 0)

    def test_try_stripped_suffix_fallback__base_schema_unresolved__returns_none(self) -> None:
        """
        Scenario:
            - A schema reference ends with a known suffix
            - The base schema exists but cannot be resolved
        Expected Outcome:
            - Returns None
            - No schema is registered in context
        """
        # Arrange
        base_name = "Test"
        base_schema_data = {"type": "object"}
        self.context.raw_spec_schemas[base_name] = base_schema_data

        unresolved_schema = IRSchema(name=base_name, type="object")
        unresolved_schema._from_unresolved_ref = True
        self.mock_parse_fn.return_value = unresolved_schema

        # Act
        result = try_stripped_suffix_fallback(
            self.ref_name, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(result)
        self.assertNotIn(self.ref_name, self.context.parsed_schemas)
        self.assertEqual(len(self.context.collected_warnings), 0)
