"""
Tests for the existing schema reference helper in schema reference resolution.
"""

import unittest

from pyopenapi_gen.core.parsing.common.ref_resolution.helpers.existing_schema import handle_existing_schema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestHandleExistingSchema(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        self.context = ParsingContext()
        self.schema_name = "TestSchema"
        self.existing_schema = IRSchema(name=self.schema_name, type="object")
        self.context.parsed_schemas[self.schema_name] = self.existing_schema

    def test_handle_existing_schema__returns_cached_schema(self) -> None:
        """
        Scenario:
            - A schema reference points to an already parsed schema
            - The schema exists in context.parsed_schemas
        Expected Outcome:
            - Returns the existing schema from context.parsed_schemas
        """
        # Act
        result = handle_existing_schema(self.schema_name, self.context)

        # Assert
        self.assertIs(result, self.existing_schema)
        self.assertEqual(result.name, self.schema_name)
        self.assertEqual(result.type, "object")

    def test_handle_existing_schema__schema_not_in_context__raises_key_error(self) -> None:
        """
        Scenario:
            - A schema reference points to a schema that doesn't exist in context.parsed_schemas
        Expected Outcome:
            - Raises KeyError as per pre-condition
        """
        # Arrange
        non_existent_schema = "NonExistentSchema"

        # Act & Assert
        with self.assertRaises(KeyError):
            handle_existing_schema(non_existent_schema, self.context)

    def test_handle_existing_schema__preserves_schema_properties(self) -> None:
        """
        Scenario:
            - A schema reference points to an existing schema with properties
        Expected Outcome:
            - Returns the existing schema with all properties preserved
        """
        # Arrange
        schema_with_props = IRSchema(
            name=self.schema_name,
            type="object",
            properties={"test": IRSchema(name="test", type="string")},
            required=["test"],
        )
        self.context.parsed_schemas[self.schema_name] = schema_with_props

        # Act
        result = handle_existing_schema(self.schema_name, self.context)

        # Assert
        self.assertIs(result, schema_with_props)
        self.assertEqual(result.type, "object")
        self.assertIn("test", result.properties)
        self.assertEqual(result.properties["test"].type, "string")
        self.assertEqual(result.required, ["test"])
