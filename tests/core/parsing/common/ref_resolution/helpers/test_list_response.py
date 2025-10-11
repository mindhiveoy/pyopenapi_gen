"""
Tests for the list response fallback helper in schema reference resolution.
"""

import unittest
from typing import Any, Callable, Mapping, Optional
from unittest.mock import MagicMock

from pyopenapi_gen.core.parsing.common.ref_resolution.helpers.list_response import try_list_response_fallback
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestTryListResponseFallback(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        self.context = ParsingContext()
        self.ref_name = "TestListResponse"
        self.ref_value = "#/components/schemas/TestListResponse"
        self.max_depth = 100
        self.mock_parse_fn = MagicMock(
            spec=Callable[[str | None, Optional[Mapping[str, Any]], ParsingContext, int], IRSchema]
        )

    def test_try_list_response_fallback__valid_list_response__returns_array_schema(self) -> None:
        """
        Scenario:
            - A schema reference ends with "ListResponse"
            - The base schema exists in raw_spec_schemas
            - The base schema can be parsed successfully
        Expected Outcome:
            - Returns an array schema with the base schema as items
            - Registers the schema in context.parsed_schemas
            - Adds a warning to context.collected_warnings
        """
        # Arrange
        base_name = "Test"
        base_schema_data = {"type": "string"}
        self.context.raw_spec_schemas[base_name] = base_schema_data

        base_schema = IRSchema(name=base_name, type="string")
        self.mock_parse_fn.return_value = base_schema

        # Act
        result = try_list_response_fallback(
            self.ref_name, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNotNone(result)
        if result is not None:  # Type narrowing for mypy
            self.assertEqual(result.name, self.ref_name)
            self.assertEqual(result.type, "array")
            self.assertIs(result.items, base_schema)
        self.assertIn(self.ref_name, self.context.parsed_schemas)
        self.assertIs(self.context.parsed_schemas[self.ref_name], result)
        self.assertTrue(any("falling back to LIST" in warning for warning in self.context.collected_warnings))

    def test_try_list_response_fallback__not_list_response__returns_none(self) -> None:
        """
        Scenario:
            - A schema reference does not end with "ListResponse"
        Expected Outcome:
            - Returns None
            - No schema is registered in context
        """
        # Arrange
        non_list_ref = "TestSchema"

        # Act
        result = try_list_response_fallback(
            non_list_ref, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(result)
        self.assertNotIn(non_list_ref, self.context.parsed_schemas)
        self.assertEqual(len(self.context.collected_warnings), 0)

    def test_try_list_response_fallback__base_schema_not_found__returns_none(self) -> None:
        """
        Scenario:
            - A schema reference ends with "ListResponse"
            - The base schema does not exist in raw_spec_schemas
        Expected Outcome:
            - Returns None
            - No schema is registered in context
        """
        # Act
        result = try_list_response_fallback(
            self.ref_name, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(result)
        self.assertNotIn(self.ref_name, self.context.parsed_schemas)
        self.assertEqual(len(self.context.collected_warnings), 0)

    def test_try_list_response_fallback__base_schema_unresolved__returns_none(self) -> None:
        """
        Scenario:
            - A schema reference ends with "ListResponse"
            - The base schema exists but cannot be resolved
        Expected Outcome:
            - Returns None
            - No schema is registered in context
        """
        # Arrange
        base_name = "Test"
        base_schema_data = {"type": "string"}
        self.context.raw_spec_schemas[base_name] = base_schema_data

        unresolved_schema = IRSchema(name=base_name, type="string")
        unresolved_schema._from_unresolved_ref = True
        self.mock_parse_fn.return_value = unresolved_schema

        # Act
        result = try_list_response_fallback(
            self.ref_name, self.ref_value, self.context, self.max_depth, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(result)
        self.assertNotIn(self.ref_name, self.context.parsed_schemas)
        self.assertEqual(len(self.context.collected_warnings), 0)
