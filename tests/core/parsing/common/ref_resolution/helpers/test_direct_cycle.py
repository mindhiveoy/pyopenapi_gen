"""
Tests for the direct cycle detection helper in schema reference resolution.
"""

import unittest

from pyopenapi_gen.core.parsing.common.ref_resolution.helpers.direct_cycle import handle_direct_cycle
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestHandleDirectCycle(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        self.context = ParsingContext()
        self.schema_name = "TestSchema"
        self.existing_schema = IRSchema(name=self.schema_name, type="object")
        self.context.parsed_schemas[self.schema_name] = self.existing_schema

    def test_handle_direct_cycle__existing_schema__marks_as_unresolved(self) -> None:
        """
        Scenario:
            - A schema reference creates a direct cycle
            - The schema already exists in context.parsed_schemas
        Expected Outcome:
            - Returns the existing schema
            - Marks the schema as unresolved (_from_unresolved_ref = True)
        """
        # Act
        result = handle_direct_cycle(self.schema_name, self.context)

        # Assert
        self.assertIs(result, self.existing_schema)
        self.assertTrue(result._from_unresolved_ref)

    def test_handle_direct_cycle__schema_not_in_context__raises_key_error(self) -> None:
        """
        Scenario:
            - A schema reference creates a direct cycle
            - The schema does not exist in context.parsed_schemas
        Expected Outcome:
            - Raises KeyError as per pre-condition
        """
        # Arrange
        non_existent_schema = "NonExistentSchema"

        # Act & Assert
        with self.assertRaises(KeyError):
            handle_direct_cycle(non_existent_schema, self.context)

    def test_handle_direct_cycle__preserves_schema_properties(self) -> None:
        """
        Scenario:
            - A schema reference creates a direct cycle
            - The schema has existing properties
        Expected Outcome:
            - Returns the existing schema with all properties preserved
            - Only _from_unresolved_ref flag is modified
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
        result = handle_direct_cycle(self.schema_name, self.context)

        # Assert
        self.assertIs(result, schema_with_props)
        self.assertTrue(result._from_unresolved_ref)
        self.assertEqual(result.type, "object")
        self.assertIn("test", result.properties)
        self.assertEqual(result.properties["test"].type, "string")
        self.assertEqual(result.required, ["test"])
