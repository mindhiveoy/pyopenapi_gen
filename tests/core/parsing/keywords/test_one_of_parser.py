"""
Tests for the _parse_one_of_schemas helper function in keywords.one_of_parser.
"""

import unittest
from typing import Any, Callable, List, Mapping, Optional
from unittest.mock import MagicMock

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.keywords.one_of_parser import _parse_one_of_schemas


class TestParseOneOfSchemas(unittest.TestCase):
    def setUp(self) -> None:
        """Set up for test cases."""
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={}, visited_refs=set())
        self.mock_parse_fn = MagicMock(
            spec=Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema]
        )

        # Default side effect for the mock_parse_fn
        def default_parse_fn_side_effect(
            name: Optional[str],
            node: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: int,
        ) -> IRSchema:
            type_from_node = "object"  # Default
            if node:
                type_from_node = node.get("type", "object")
                if "$ref" in node and isinstance(node["$ref"], str):
                    name = node["$ref"].split("/")[-1]
            return IRSchema(name=name if name else "AnonymousParsedSchema", type=type_from_node)

        self.mock_parse_fn.side_effect = default_parse_fn_side_effect

    def test_empty_one_of_list(self) -> None:
        """
        Scenario:
            - The _parse_one_of_schemas function is called with an empty list for `one_of_nodes`.
            - This represents an OpenAPI schema where a `oneOf` keyword is present but its value is an empty array.
        Expected Outcome:
            - The function should return (None, False, None) indicating no schemas parsed, not nullable,
              and no effective type derived.
            - The `parse_fn` (mocked schema parsing function) should not be called.
        """
        # Arrange
        one_of_nodes: List[Mapping[str, Any]] = []

        # Act
        parsed_schemas, is_nullable, eff_type = _parse_one_of_schemas(
            one_of_nodes, self.context, 10, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(parsed_schemas)
        self.assertFalse(is_nullable)
        self.assertIsNone(eff_type)
        self.mock_parse_fn.assert_not_called()

    def test_one_of_with_single_simple_type(self) -> None:
        """
        Scenario:
            - The `oneOf` list contains a single node representing a simple schema type (e.g., {"type": "string"}).
            - This tests the basic case of parsing one item from the `oneOf` array.
        Expected Outcome:
            - The `parse_fn` should be called once with the simple type node.
            - The returned `parsed_schemas` list should contain one IRSchema, which is the result from `parse_fn`.
            - `is_nullable` should be False, and `eff_type` should be None.
        """
        # Arrange
        one_of_nodes: List[Mapping[str, Any]] = [{"type": "string"}]

        string_schema = IRSchema(name="GeneratedStringProperty", type="string")
        self.mock_parse_fn.side_effect = lambda n, nd, c, md: (
            string_schema if nd == one_of_nodes[0] else self.fail("Unexpected call")
        )

        parsed_schemas, is_nullable, eff_type = _parse_one_of_schemas(
            one_of_nodes, self.context, 10, self.mock_parse_fn
        )
        self.assertIsNotNone(parsed_schemas)
        if parsed_schemas:
            self.assertEqual(len(parsed_schemas), 1)
            self.assertIs(parsed_schemas[0], string_schema)
        self.assertFalse(is_nullable)
        self.assertIsNone(eff_type)
        self.mock_parse_fn.assert_called_once_with(None, one_of_nodes[0], self.context, 10)

    def test_one_of__multiple_simple_types__parses_all(self) -> None:
        """
        Scenario:
            - oneOf contains multiple simple type definitions (e.g., string, integer).
        Expected Outcome:
            - _parse_one_of_schemas should call parse_fn for each definition.
            - The returned list should contain IRSchema objects for each parsed type.
            - is_nullable should be False.
        """
        # Arrange
        one_of_nodes: List[Mapping[str, Any]] = [
            {"type": "string"},
            {"type": "integer"},
            {"type": "boolean"},
        ]

        string_schema = IRSchema(name="GenString", type="string")
        integer_schema = IRSchema(name="GenInt", type="integer")
        boolean_schema = IRSchema(name="GenBool", type="boolean")

        def side_effect(
            name: Optional[str], node_data: Optional[Mapping[str, Any]], context: ParsingContext, max_depth: int
        ) -> IRSchema:
            if node_data == one_of_nodes[0]:
                return string_schema
            if node_data == one_of_nodes[1]:
                return integer_schema
            if node_data == one_of_nodes[2]:
                return boolean_schema
            self.fail(f"Unexpected call to mock_parse_fn with node: {node_data}")
            return IRSchema()

        self.mock_parse_fn.side_effect = side_effect

        # Act
        parsed_schemas, is_nullable, eff_type = _parse_one_of_schemas(
            one_of_nodes, self.context, 10, self.mock_parse_fn
        )

        # Assert
        self.assertIsNotNone(parsed_schemas)
        if parsed_schemas:
            self.assertEqual(len(parsed_schemas), 3)
            self.assertIn(string_schema, parsed_schemas)
            self.assertIn(integer_schema, parsed_schemas)
            self.assertIn(boolean_schema, parsed_schemas)
        self.assertFalse(is_nullable)
        self.assertIsNone(eff_type)
        self.assertEqual(self.mock_parse_fn.call_count, 3)
        self.mock_parse_fn.assert_any_call(None, one_of_nodes[0], self.context, 10)
        self.mock_parse_fn.assert_any_call(None, one_of_nodes[1], self.context, 10)
        self.mock_parse_fn.assert_any_call(None, one_of_nodes[2], self.context, 10)

    def test_one_of__mixed_types_null_and_ref__parses_correctly(self) -> None:
        """
        Scenario:
            - oneOf contains a mix: a simple type, a null type, and a $ref.
        Expected Outcome:
            - parse_fn should be called for the simple type and the $ref.
            - The null type should set is_nullable to True.
            - The returned list should contain IRSchema objects for the non-null types.
        """
        # Arrange
        simple_type_node = {"type": "number"}
        null_type_node = {"type": "null"}
        ref_node = {"$ref": "#/components/schemas/MyRef"}
        one_of_nodes: List[Mapping[str, Any]] = [simple_type_node, null_type_node, ref_node]

        number_schema = IRSchema(name="GenNum", type="number")
        my_ref_schema = IRSchema(name="MyRef", type="object")

        def side_effect(
            name: Optional[str], node_data: Optional[Mapping[str, Any]], context: ParsingContext, max_depth: int
        ) -> IRSchema:
            if node_data == simple_type_node:
                return number_schema
            if node_data == ref_node:
                return my_ref_schema
            self.fail(f"Unexpected call to mock_parse_fn with node: {node_data}")
            return IRSchema()

        self.mock_parse_fn.side_effect = side_effect

        # Act
        parsed_schemas, is_nullable, eff_type = _parse_one_of_schemas(
            one_of_nodes, self.context, 10, self.mock_parse_fn
        )

        # Assert
        self.assertIsNotNone(parsed_schemas)
        if parsed_schemas:
            self.assertEqual(len(parsed_schemas), 2)
            self.assertIn(number_schema, parsed_schemas)
            self.assertIn(my_ref_schema, parsed_schemas)
        self.assertTrue(is_nullable)
        self.assertIsNone(eff_type)
        self.assertEqual(self.mock_parse_fn.call_count, 2)
        self.mock_parse_fn.assert_any_call(None, simple_type_node, self.context, 10)
        self.mock_parse_fn.assert_any_call(None, ref_node, self.context, 10)

    def test_one_of__all_sub_nodes_empty__returns_none(self) -> None:
        """
        Scenario:
            - oneOf contains multiple definitions.
            - All sub-nodes, when parsed by parse_fn, result in "empty" IRSchema
              (type=None, no properties, no items, etc.).
        Expected Outcome:
            - _parse_one_of_schemas should return None for the list of parsed schemas.
            - is_nullable should be False (unless a {"type": "null"} was explicitly present).
        """
        # Arrange
        one_of_nodes: List[Mapping[str, Any]] = [
            {"description": "first empty node"},
            {"description": "second empty node"},
        ]

        # Configure mock_parse_fn to return "empty" IRSchema instances
        empty_schema1 = IRSchema(name="Empty1FromOneOf", type=None)
        empty_schema2 = IRSchema(name="Empty2FromOneOf", type=None)

        self.mock_parse_fn.side_effect = [empty_schema1, empty_schema2]

        # Act
        parsed_schemas, is_nullable, eff_type = _parse_one_of_schemas(
            one_of_nodes, self.context, 10, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(parsed_schemas, "Expected None for parsed_schemas when all sub-schemas are empty")
        self.assertFalse(is_nullable, "is_nullable should be false as no explicit null type was provided")
        self.assertIsNone(eff_type)
        self.assertEqual(self.mock_parse_fn.call_count, 2)
        self.mock_parse_fn.assert_any_call(None, one_of_nodes[0], self.context, 10)
        self.mock_parse_fn.assert_any_call(None, one_of_nodes[1], self.context, 10)

    def test_one_of__invalid_item_in_list__raises_assertion_error(self) -> None:
        """
        Scenario:
            - The oneOf list contains an item that is not a dictionary (Mapping).
        Expected Outcome:
            - An AssertionError should be raised due to the pre-condition check.
        """
        # Arrange
        one_of_nodes: List[Any] = [{"type": "string"}, "not a mapping"]

        # Act & Assert
        with self.assertRaisesRegex(AssertionError, "all items in one_of_nodes must be Mappings"):
            _parse_one_of_schemas(one_of_nodes, self.context, 10, self.mock_parse_fn)


if __name__ == "__main__":
    unittest.main()
