"""
Tests for the missing schema reference helper in schema reference resolution.
"""

import unittest
from typing import Any, Callable, Mapping, Optional
from unittest.mock import MagicMock, patch

from pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref import handle_missing_ref
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestHandleMissingRef(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        self.context = ParsingContext()
        self.ref_value = "#/components/schemas/TestSchema"
        self.ref_name = "TestSchema"
        self.max_depth = 100
        self.mock_parse_fn = MagicMock(
            spec=Callable[[str | None, Optional[Mapping[str, Any]], ParsingContext, int], IRSchema]
        )

    def test_handle_missing_ref__no_fallbacks_succeed__returns_unresolved_schema(self) -> None:
        """
        Scenario:
            - A schema reference is missing
            - All fallback strategies fail
        Expected Outcome:
            - Returns an unresolved schema
            - Schema is registered in context.parsed_schemas
        """
        # Arrange
        with (
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_list_response_fallback",
                return_value=None,
            ),
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_stripped_suffix_fallback",
                return_value=None,
            ),
        ):
            # Act
            result = handle_missing_ref(self.ref_value, self.ref_name, self.context, self.max_depth, self.mock_parse_fn)

            # Assert
            self.assertIsInstance(result, IRSchema)
            self.assertEqual(result.name, self.ref_name)
            self.assertTrue(result._from_unresolved_ref)
            self.assertIn(self.ref_name, self.context.parsed_schemas)
            self.assertIs(self.context.parsed_schemas[self.ref_name], result)

    def test_handle_missing_ref__list_response_fallback_succeeds__returns_list_schema(self) -> None:
        """
        Scenario:
            - A schema reference is missing
            - ListResponse fallback succeeds
        Expected Outcome:
            - Returns the schema from ListResponse fallback
        """
        # Arrange
        list_response_schema = IRSchema(
            name=self.ref_name,
            type="array",
            items=IRSchema(name="Item", type="string"),
        )
        with (
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_list_response_fallback",
                return_value=list_response_schema,
            ),
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_stripped_suffix_fallback",
                return_value=None,
            ),
        ):
            # Act
            result = handle_missing_ref(self.ref_value, self.ref_name, self.context, self.max_depth, self.mock_parse_fn)

            # Assert
            self.assertIs(result, list_response_schema)
            self.assertEqual(result.type, "array")
            self.assertIsInstance(result.items, IRSchema)

    def test_handle_missing_ref__stripped_suffix_fallback_succeeds__returns_stripped_schema(self) -> None:
        """
        Scenario:
            - A schema reference is missing
            - ListResponse fallback fails
            - Stripped suffix fallback succeeds
        Expected Outcome:
            - Returns the schema from stripped suffix fallback
        """
        # Arrange
        stripped_schema = IRSchema(name=self.ref_name, type="object")
        with (
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_list_response_fallback",
                return_value=None,
            ),
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_stripped_suffix_fallback",
                return_value=stripped_schema,
            ),
        ):
            # Act
            result = handle_missing_ref(self.ref_value, self.ref_name, self.context, self.max_depth, self.mock_parse_fn)

            # Assert
            self.assertIs(result, stripped_schema)
            self.assertEqual(result.type, "object")

    def test_handle_missing_ref__both_fallbacks_succeed__prefers_list_response(self) -> None:
        """
        Scenario:
            - A schema reference is missing
            - Both ListResponse and stripped suffix fallbacks succeed
        Expected Outcome:
            - Returns the schema from ListResponse fallback (first fallback)
        """
        # Arrange
        list_response_schema = IRSchema(
            name=self.ref_name,
            type="array",
            items=IRSchema(name="Item", type="string"),
        )
        stripped_schema = IRSchema(name=self.ref_name, type="object")
        with (
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_list_response_fallback",
                return_value=list_response_schema,
            ),
            patch(
                "pyopenapi_gen.core.parsing.common.ref_resolution.helpers.missing_ref.try_stripped_suffix_fallback",
                return_value=stripped_schema,
            ),
        ):
            # Act
            result = handle_missing_ref(self.ref_value, self.ref_name, self.context, self.max_depth, self.mock_parse_fn)

            # Assert
            self.assertIs(result, list_response_schema)
            self.assertEqual(result.type, "array")
