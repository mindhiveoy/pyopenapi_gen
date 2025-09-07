"""
Tests for the _parse_any_of_schemas helper function in keywords.any_of_parser.
"""

import unittest
from typing import Any, Callable, List, Mapping, Optional
from unittest.mock import MagicMock

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.keywords.any_of_parser import _parse_any_of_schemas


class TestParseAnyOfSchemas(unittest.TestCase):
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
            # Simulate parsing: if node is a ref, extract name from ref, else use provided name or generate one
            # This is a simplified mock; real parsing is more complex.
            type_from_node = "object"  # Default
            if node:
                type_from_node = node.get("type", "object")
                if "$ref" in node and isinstance(node["$ref"], str):
                    name = node["$ref"].split("/")[-1]

            return IRSchema(name=name if name else "AnonymousParsedSchema", type=type_from_node)

        self.mock_parse_fn.side_effect = default_parse_fn_side_effect

    def test_empty_any_of_list(self) -> None:
        """
        Scenario:
            - The _parse_any_of_schemas function is called with an empty list for `any_of_nodes`.
            - This represents an OpenAPI schema where an `anyOf` keyword is present but its value is an empty array.
        Expected Outcome:
            - The function should return (None, False, None) indicating no schemas parsed, not nullable,
              and no effective type derived.
            - The `parse_fn` (mocked schema parsing function) should not be called.
        """
        # Arrange
        any_of_nodes: List[Mapping[str, Any]] = []

        # Act
        parsed_schemas, is_nullable, eff_type = _parse_any_of_schemas(
            any_of_nodes, self.context, 10, self.mock_parse_fn
        )

        # Assert
        self.assertIsNone(parsed_schemas)
        self.assertFalse(is_nullable)
        self.assertIsNone(eff_type)
        self.mock_parse_fn.assert_not_called()

    def test_any_of_with_single_simple_type(self) -> None:
        """
        Scenario:
            - The `anyOf` list contains a single node representing a simple schema type (e.g., {"type": "string"}).
            - This tests the basic case of parsing one item from the `anyOf` array.
        Expected Outcome:
            - The `parse_fn` should be called once with the simple type node.
            - The returned `parsed_schemas` list should contain one IRSchema, which is the result from `parse_fn`.
            - `is_nullable` should be False, and `eff_type` should be None.
        """
        # Arrange
        any_of_nodes: List[Mapping[str, Any]] = [{"type": "string"}]

        # Configure mock_parse_fn to return a specific schema for this input
        string_schema = IRSchema(name="GeneratedStringProperty", type="string")
        self.mock_parse_fn.side_effect = lambda n, nd, c, md: (
            string_schema if nd == any_of_nodes[0] else self.fail("Unexpected call to mock_parse_fn")
        )

        parsed_schemas, is_nullable, eff_type = _parse_any_of_schemas(
            any_of_nodes, self.context, 10, self.mock_parse_fn
        )
        self.assertIsNotNone(parsed_schemas)
        if parsed_schemas:  # Check for linter
            self.assertEqual(len(parsed_schemas), 1)
            self.assertIs(parsed_schemas[0], string_schema)
        self.assertFalse(is_nullable)
        self.assertIsNone(eff_type)
        self.mock_parse_fn.assert_called_once_with(None, any_of_nodes[0], self.context, 10)

    def test_any_of_with_null_type(self) -> None:
        """
        Scenario:
            - The `anyOf` list includes a node representing the null type (e.g., {"type": "null"})
              along with another valid schema type (e.g., {"type": "integer"}).
            - This tests how `anyOf` handles explicit nullability.
        Expected Outcome:
            - The `parse_fn` should be called only for the non-null type node.
            - `is_nullable` should be True because of the presence of {"type": "null"}.
            - The `parsed_schemas` list should contain one IRSchema for the non-null type.
            - `eff_type` should be None.
        """
        # Arrange
        any_of_nodes: List[Mapping[str, Any]] = [{"type": "null"}, {"type": "integer"}]

        integer_schema = IRSchema(name="GeneratedIntProperty", type="integer")
        self.mock_parse_fn.side_effect = lambda n, nd, c, md: (
            integer_schema if nd == any_of_nodes[1] else self.fail("Unexpected call for null type")
        )

        parsed_schemas, is_nullable, eff_type = _parse_any_of_schemas(
            any_of_nodes, self.context, 10, self.mock_parse_fn
        )
        self.assertIsNotNone(parsed_schemas)
        if parsed_schemas:  # Check for linter
            self.assertEqual(len(parsed_schemas), 1)
            self.assertIs(parsed_schemas[0], integer_schema)
        self.assertTrue(is_nullable)
        self.assertIsNone(eff_type)
        self.mock_parse_fn.assert_called_once_with(None, any_of_nodes[1], self.context, 10)

    def test_any_of_with_ref_type(self) -> None:
        """
        Scenario:
            - The `anyOf` list contains a single node that is a $ref to another schema
              (e.g., {"$ref": "#/components/schemas/MyReferencedSchema"}).
            - This ensures that $refs within `anyOf` are correctly passed to `parse_fn`.
        Expected Outcome:
            - `parse_fn` should be called once with the $ref node.
            - The `parsed_schemas` list should contain one IRSchema (the result of parsing the $ref).
            - `is_nullable` should be False, and `eff_type` should be None.
        """
        # Arrange
        ref_node = {"$ref": "#/components/schemas/MyReferencedSchema"}
        any_of_nodes: List[Mapping[str, Any]] = [ref_node]

        ref_schema_parsed = IRSchema(name="MyReferencedSchema", type="object")
        self.mock_parse_fn.side_effect = lambda n, nd, c, md: (
            ref_schema_parsed if nd == ref_node else self.fail("Unexpected call")
        )

        parsed_schemas, is_nullable, eff_type = _parse_any_of_schemas(
            any_of_nodes, self.context, 10, self.mock_parse_fn
        )
        self.assertIsNotNone(parsed_schemas)
        if parsed_schemas:  # Check for linter
            self.assertEqual(len(parsed_schemas), 1)
            self.assertIs(parsed_schemas[0], ref_schema_parsed)
        self.assertFalse(is_nullable)
        self.assertIsNone(eff_type)
        self.mock_parse_fn.assert_called_once_with(None, ref_node, self.context, 10)

    def test_all_sub_nodes_are_empty_after_parse(self) -> None:
        """
        Scenario:
            - The `anyOf` list contains multiple nodes.
            - Each node, when parsed by the mocked `parse_fn`, results in an "empty" IRSchema
              (e.g., an IRSchema with `type=None` and no other significant attributes).
            - This tests the filtering logic within `_parse_any_of_schemas`.
        Expected Outcome:
            - `parse_fn` should be called for each node in the `anyOf` list.
            - The returned `parsed_schemas` should be None because all individual results were empty.
            - `is_nullable` should be False, and `eff_type` should be None.
        """
        # Arrange
        any_of_nodes: List[Mapping[str, Any]] = [{"type": "string"}, {"type": "integer"}]

        # Make mock_parse_fn return "empty" schemas
        empty_schema1 = IRSchema(name="Empty1", type=None)
        empty_schema2 = IRSchema(name="Empty2", type=None)
        self.mock_parse_fn.side_effect = [empty_schema1, empty_schema2]

        parsed_schemas, is_nullable, eff_type = _parse_any_of_schemas(
            any_of_nodes, self.context, 10, self.mock_parse_fn
        )

        self.assertIsNone(parsed_schemas)  # Expect None because all filtered out
        self.assertFalse(is_nullable)
        self.assertIsNone(eff_type)
        self.assertEqual(self.mock_parse_fn.call_count, 2)
        self.mock_parse_fn.assert_any_call(None, any_of_nodes[0], self.context, 10)
        self.mock_parse_fn.assert_any_call(None, any_of_nodes[1], self.context, 10)

    def test_any_of__multiple_simple_types__parses_all(self) -> None:
        """
        Scenario:
            - anyOf contains multiple simple type definitions (e.g., string, integer).
        Expected Outcome:
            - _parse_any_of_schemas should call parse_fn for each definition.
            - The returned list should contain IRSchema objects for each parsed type.
            - is_nullable should be False.
        """
        # Arrange
        any_of_nodes: List[Mapping[str, Any]] = [
            {"type": "string"},
            {"type": "integer"},
            {"type": "boolean"},
        ]

        string_schema = IRSchema(name="GenString", type="string")
        integer_schema = IRSchema(name="GenInt", type="integer")
        boolean_schema = IRSchema(name="GenBool", type="boolean")

        # Configure mock_parse_fn to return specific schemas for corresponding inputs
        def side_effect(
            name: Optional[str], node_data: Optional[Mapping[str, Any]], context: ParsingContext, max_depth: int
        ) -> IRSchema:
            if node_data == any_of_nodes[0]:
                return string_schema
            if node_data == any_of_nodes[1]:
                return integer_schema
            if node_data == any_of_nodes[2]:
                return boolean_schema
            self.fail(f"Unexpected call to mock_parse_fn with node: {node_data}")
            return IRSchema()  # Should not be reached

        self.mock_parse_fn.side_effect = side_effect

        # Act
        parsed_schemas, is_nullable, eff_type = _parse_any_of_schemas(
            any_of_nodes, self.context, 10, self.mock_parse_fn
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
        self.mock_parse_fn.assert_any_call(None, any_of_nodes[0], self.context, 10)
        self.mock_parse_fn.assert_any_call(None, any_of_nodes[1], self.context, 10)
        self.mock_parse_fn.assert_any_call(None, any_of_nodes[2], self.context, 10)

    def test_any_of__mixed_types_null_and_ref__parses_correctly(self) -> None:
        """
        Scenario:
            - anyOf contains a mix: a simple type, a null type, and a $ref.
        Expected Outcome:
            - parse_fn should be called for the simple type and the $ref.
            - The null type should set is_nullable to True.
            - The returned list should contain IRSchema objects for the non-null types.
        """
        # Arrange
        simple_type_node = {"type": "number"}
        null_type_node = {"type": "null"}
        ref_node = {"$ref": "#/components/schemas/MyRef"}
        any_of_nodes: List[Mapping[str, Any]] = [simple_type_node, null_type_node, ref_node]

        number_schema = IRSchema(name="GenNum", type="number")
        my_ref_schema = IRSchema(name="MyRef", type="object")  # Assuming $ref resolves to an object

        def side_effect(
            name: Optional[str], node_data: Optional[Mapping[str, Any]], context: ParsingContext, max_depth: int
        ) -> IRSchema:
            if node_data == simple_type_node:
                return number_schema
            if node_data == ref_node:
                return my_ref_schema
            # parse_fn should not be called for the null_type_node directly by _parse_any_of_schemas
            self.fail(f"Unexpected call to mock_parse_fn with node: {node_data}")
            return IRSchema()  # Should not be reached

        self.mock_parse_fn.side_effect = side_effect

        # Act
        parsed_schemas, is_nullable, eff_type = _parse_any_of_schemas(
            any_of_nodes, self.context, 10, self.mock_parse_fn
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

    def test_any_of__invalid_item_in_list__raises_type_error(self) -> None:
        """
        Scenario:
            - The anyOf list contains an item that is not a dictionary (Mapping).
        Expected Outcome:
            - An TypeError should be raised due to the pre-condition check.
        """
        # Arrange
        any_of_nodes: List[Any] = [{"type": "string"}, "not a mapping"]

        # Act & Assert
        with self.assertRaisesRegex(TypeError, "all items in any_of_nodes must be Mappings"):
            _parse_any_of_schemas(any_of_nodes, self.context, 10, self.mock_parse_fn)


if __name__ == "__main__":
    unittest.main()
