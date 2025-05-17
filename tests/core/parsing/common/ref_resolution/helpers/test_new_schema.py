"""
Tests for the new schema parsing helper in schema reference resolution.
"""

import unittest
from typing import Any, Callable, Dict, Mapping, Optional
from unittest.mock import MagicMock

from pyopenapi_gen.core.parsing.common.ref_resolution.helpers.new_schema import parse_new_schema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.ir import IRSchema


class TestParseNewSchema(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test cases."""
        self.context = ParsingContext()
        self.ref_name = "TestSchema"
        self.node_data: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }
        self.max_depth = 100
        self.mock_parse_fn = MagicMock(
            spec=Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema]
        )

    def test_parse_new_schema__creates_and_registers_schema(self) -> None:
        """
        Scenario:
            - A new schema needs to be parsed
            - The schema has valid properties and requirements
        Expected Outcome:
            - Creates a stub schema to prevent infinite recursion
            - Parses the full schema using parse_fn
            - Registers the fully parsed schema in context
            - Returns the fully parsed schema
        """
        # Arrange
        parsed_schema = IRSchema(
            name=self.ref_name,
            type="object",
            properties={
                "name": IRSchema(name="name", type="string"),
                "age": IRSchema(name="age", type="integer"),
            },
            required=["name"],
        )
        self.mock_parse_fn.return_value = parsed_schema

        # Act
        result = parse_new_schema(self.ref_name, self.node_data, self.context, self.max_depth, self.mock_parse_fn)

        # Assert
        self.assertIs(result, parsed_schema)
        self.assertIn(self.ref_name, self.context.parsed_schemas)
        self.assertIs(self.context.parsed_schemas[self.ref_name], parsed_schema)
        self.mock_parse_fn.assert_called_once_with(self.ref_name, self.node_data, self.context, self.max_depth)

    def test_parse_new_schema__handles_cyclic_properties(self) -> None:
        """
        Scenario:
            - A new schema needs to be parsed
            - The schema contains cyclic property references
        Expected Outcome:
            - Creates and registers the schema
            - Marks cyclic property references correctly
        """
        # Arrange
        cyclic_schema = IRSchema(
            name=self.ref_name,
            type="object",
            properties={
                "self": IRSchema(name="self", type=self.ref_name),
            },
        )
        cyclic_schema.properties["self"]._refers_to_schema = cyclic_schema
        self.mock_parse_fn.return_value = cyclic_schema

        # Act
        result = parse_new_schema(self.ref_name, self.node_data, self.context, self.max_depth, self.mock_parse_fn)

        # Assert
        self.assertIs(result, cyclic_schema)
        self.assertIn(self.ref_name, self.context.parsed_schemas)
        self.assertIs(self.context.parsed_schemas[self.ref_name], cyclic_schema)
        self.assertTrue(result.properties["self"]._from_unresolved_ref)

    def test_parse_new_schema__handles_parse_fn_failure(self) -> None:
        """
        Scenario:
            - A new schema needs to be parsed
            - The parse_fn raises an exception
        Expected Outcome:
            - The exception is propagated
            - The stub schema remains in context.parsed_schemas
        """
        # Arrange
        self.mock_parse_fn.side_effect = ValueError("Parse error")

        # Act & Assert
        with self.assertRaises(ValueError):
            parse_new_schema(self.ref_name, self.node_data, self.context, self.max_depth, self.mock_parse_fn)

        # The stub schema should still be in context
        self.assertIn(self.ref_name, self.context.parsed_schemas)
        self.assertEqual(self.context.parsed_schemas[self.ref_name].name, self.ref_name)
        self.assertIsNone(self.context.parsed_schemas[self.ref_name].type)

    def test_parse_new_schema__preserves_schema_metadata(self) -> None:
        """
        Scenario:
            - A new schema needs to be parsed
            - The schema contains metadata (description, format, etc.)
        Expected Outcome:
            - Creates and registers the schema
            - Preserves all metadata from the parsed schema
        """
        # Arrange
        schema_with_metadata = IRSchema(
            name=self.ref_name,
            type="object",
            description="Test schema with metadata",
            format="custom",
            properties={
                "field": IRSchema(name="field", type="string", description="A field"),
            },
        )
        self.mock_parse_fn.return_value = schema_with_metadata

        # Act
        result = parse_new_schema(self.ref_name, self.node_data, self.context, self.max_depth, self.mock_parse_fn)

        # Assert
        self.assertIs(result, schema_with_metadata)
        self.assertEqual(result.description, "Test schema with metadata")
        self.assertEqual(result.format, "custom")
        self.assertEqual(result.properties["field"].description, "A field")
