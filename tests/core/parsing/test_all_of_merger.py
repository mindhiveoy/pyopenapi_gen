import unittest
from typing import Any, Callable, Dict, Mapping, Optional, Set, cast
from unittest.mock import MagicMock

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.all_of_merger import _process_all_of
from pyopenapi_gen.core.parsing.context import ParsingContext


class TestProcessAllOf(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={}, visited_refs=set())
        self.mock_parse_schema_func = MagicMock()

        # Type hint for the mock function
        MockParseSchema = Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext], IRSchema]

        def side_effect_parse_schema(
            name: Optional[str], node: Optional[Mapping[str, Any]], context: ParsingContext
        ) -> IRSchema:
            if node is None:
                return IRSchema(name=name)
            props: Dict[str, IRSchema] = {}
            reqs: Set[str] = set(node.get("required", []))
            node_props = node.get("properties", {})
            for p_name, p_node in node_props.items():
                if isinstance(p_node, IRSchema):
                    props[p_name] = p_node
                elif isinstance(p_node, dict):
                    props[p_name] = IRSchema(name=p_name, type=p_node.get("type", "string"))
                else:
                    props[p_name] = IRSchema(name=p_name, type="string")

            return IRSchema(name=name, type=node.get("type"), properties=props, required=sorted(list(reqs)))

        self.mock_parse_schema_func.side_effect = side_effect_parse_schema

    def test_simple_all_of_merge(self) -> None:
        """Test merging two simple schemas with distinct properties."""
        node: Dict[str, Any] = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"propA": {"type": "string"}},
                    "required": ["propA"],
                },
                {
                    "type": "object",
                    "properties": {"propB": {"type": "integer"}},
                    "required": ["propB"],
                },
            ]
        }
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchema", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 2)
        self.assertTrue(all(isinstance(p, IRSchema) for p in merged_props.values()))
        self.assertIn("propA", merged_props)
        self.assertEqual(merged_props["propA"].type, "string")
        self.assertIn("propB", merged_props)
        self.assertEqual(merged_props["propB"].type, "integer")
        self.assertEqual(merged_req, {"propA", "propB"})
        self.assertEqual(len(parsed_components), 2)
        self.assertTrue(all(isinstance(pc, IRSchema) for pc in parsed_components))

    def test_all_of_with_direct_properties(self) -> None:
        """Test merging allOf with properties defined directly in the node."""
        node: Dict[str, Any] = {
            "allOf": [
                {
                    "type": "object",
                    "properties": {"propA": {"type": "string"}},
                    "required": ["propA"],
                }
            ],
            "properties": {"propC": {"type": "boolean"}},
            "required": ["propC"],
        }
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaDirect", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 2)
        self.assertIn("propA", merged_props)
        self.assertEqual(merged_props["propA"].type, "string")
        self.assertIn("propC", merged_props)
        self.assertEqual(merged_props["propC"].type, "boolean")
        self.assertEqual(merged_req, {"propA", "propC"})
        self.assertEqual(len(parsed_components), 1)

    def test_all_of_override_properties(self) -> None:
        """Properties from direct node override allOf. Within allOf, first one wins."""
        prop_a_v1 = IRSchema(name="propA", type="string", description="Version 1")
        prop_a_v2 = IRSchema(name="propA", type="integer", description="Version 2")
        prop_a_direct = IRSchema(name="propA", type="boolean", description="Direct Version")

        # Mock _parse_schema to control what IRSchema instances are returned
        # for the direct properties.
        original_side_effect = self.mock_parse_schema_func.side_effect

        def custom_side_effect(
            name: Optional[str], node_data: Optional[Mapping[str, Any]], context: ParsingContext
        ) -> IRSchema:
            if name == "TestSchemaOverride.propA" and node_data and node_data.get("description") == "Direct Version":
                return prop_a_direct
            # Fallback to original mock for allOf components
            if node_data and node_data.get("properties") and "propA" in node_data["properties"]:
                if node_data["properties"]["propA"].get("description") == "Version 1":
                    return IRSchema(name=None, properties={"propA": prop_a_v1}, type="object")
                if node_data["properties"]["propA"].get("description") == "Version 2":
                    return IRSchema(name=None, properties={"propA": prop_a_v2}, type="object")
            # Ensure the fallback call is also typed correctly for the linter
            if callable(original_side_effect):
                return cast(IRSchema, original_side_effect(name, node_data, context))
            # Should not happen in practice with MagicMock setup, but makes linter happy
            return IRSchema(name=name, type="object")

        self.mock_parse_schema_func.side_effect = custom_side_effect

        node: Dict[str, Any] = {
            "allOf": [
                {"type": "object", "properties": {"propA": {"type": "string", "description": "Version 1"}}},
                {"type": "object", "properties": {"propA": {"type": "integer", "description": "Version 2"}}},
            ],
            "properties": {"propA": {"type": "boolean", "description": "Direct Version"}},
        }

        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaOverride", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 1)
        self.assertIn("propA", merged_props)
        self.assertIs(merged_props["propA"], prop_a_direct)
        self.assertEqual(merged_props["propA"].type, "boolean")
        self.assertEqual(merged_props["propA"].description, "Direct Version")
        self.assertEqual(len(parsed_components), 2)
        self.assertIs(parsed_components[0].properties["propA"], prop_a_v1)
        self.assertIs(parsed_components[1].properties["propA"], prop_a_v2)

    def test_all_of_accumulate_required(self) -> None:
        """Required fields should be accumulated from all sources."""
        node: Dict[str, Any] = {
            "allOf": [
                {"type": "object", "properties": {"propA": {"type": "string"}}, "required": ["propA"]},
                {"type": "object", "properties": {"propB": {"type": "integer"}}, "required": ["propB"]},
            ],
            "properties": {"propC": {"type": "boolean"}},
            "required": ["propC"],
        }
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaRequired", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(merged_props["propA"].type, "string")
        self.assertEqual(merged_props["propB"].type, "integer")
        self.assertEqual(merged_props["propC"].type, "boolean")
        self.assertEqual(merged_req, {"propA", "propB", "propC"})

    def test_empty_all_of(self) -> None:
        """Test with an empty allOf array."""
        node: Dict[str, Any] = {"allOf": [], "properties": {"propA": {"type": "string"}}, "required": ["propA"]}
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaEmptyAllOf", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 1)
        self.assertIn("propA", merged_props)
        self.assertEqual(merged_props["propA"].type, "string")
        self.assertEqual(merged_req, {"propA"})
        self.assertEqual(len(parsed_components), 0)

    def test_all_of_no_properties_in_components(self) -> None:
        """Test allOf components that might not define properties."""
        # Mock _parse_schema to return IRSchema without properties for these components
        empty_schema1 = IRSchema(name="Empty1", type="object")
        empty_schema2 = IRSchema(name="Empty2", description="A descriptive schema part")
        prop_a_schema = IRSchema(name="TestSchemaNoPropsInAllOf.propA", type="string")

        call_count = 0

        def no_props_side_effect(
            name: Optional[str], node_data: Optional[Mapping[str, Any]], context: ParsingContext
        ) -> IRSchema:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First allOf component
                return empty_schema1
            if call_count == 2:  # Second allOf component
                return empty_schema2
            if name == "TestSchemaNoPropsInAllOf.propA":
                return prop_a_schema
            # Fallback for any other unexpected call
            return IRSchema(name=name, type=node_data.get("type") if node_data else None)

        self.mock_parse_schema_func.side_effect = no_props_side_effect

        node: Dict[str, Any] = {
            "allOf": [
                {"type": "object"},  # Will be parsed into empty_schema1
                {"description": "A descriptive schema part"},  # empty_schema2
            ],
            "properties": {"propA": {"type": "string"}},
            "required": ["propA"],
        }
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaNoPropsInAllOf", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 1)
        self.assertIn("propA", merged_props)
        self.assertIs(merged_props["propA"], prop_a_schema)
        self.assertEqual(merged_req, {"propA"})
        self.assertEqual(len(parsed_components), 2)
        self.assertIs(parsed_components[0], empty_schema1)
        self.assertIs(parsed_components[1], empty_schema2)
        self.assertFalse(parsed_components[0].properties)  # Empty dict by default
        self.assertFalse(parsed_components[1].properties)

    def test_all_of_with_refs_in_components(self) -> None:
        """Test case where allOf components are $refs.
        _process_all_of relies on the passed _parse_schema_func to resolve these.
        """
        ref_schema_a = IRSchema(
            name="RefSchemaA",
            type="object",
            properties={"refPropA": IRSchema(name="refPropA", type="string")},
            required=["refPropA"],
        )
        direct_prop_schema = IRSchema(name="TestSchemaRefsInComponents.directProp", type="boolean")

        # This mock simulates _parse_schema resolving a $ref and parsing a direct property
        def ref_side_effect(
            name: Optional[str], node_data: Optional[Mapping[str, Any]], context: ParsingContext
        ) -> IRSchema:
            if node_data and node_data.get("$ref") == "#/components/schemas/RefA":
                return ref_schema_a
            if name == "TestSchemaRefsInComponents.directProp":
                return direct_prop_schema
            # Fallback for the sub-schema within allOf[1] if it's not a ref
            if node_data and "directPropInAllOf" in node_data.get("properties", {}):
                return IRSchema(
                    name=None,  # Anonymous inline schema part
                    type="object",
                    properties={"directPropInAllOf": IRSchema(name="directPropInAllOf", type="integer")},
                    required=[],
                )

            # Default fallback for unexpected calls during this test
            return IRSchema(name=name, type=node_data.get("type") if node_data else "object")

        self.mock_parse_schema_func.side_effect = ref_side_effect

        node: Dict[str, Any] = {
            "allOf": [
                {"$ref": "#/components/schemas/RefA"},  # Parsed to ref_schema_a
                {
                    "type": "object",
                    "properties": {"directPropInAllOf": {"type": "integer"}},
                },  # Parsed to an anonymous IRSchema by mock
            ],
            "properties": {"directProp": {"type": "boolean"}},  # Parsed to direct_prop_schema
            "required": ["directProp"],
        }

        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaRefsInComponents", self.context, self.mock_parse_schema_func
        )

        self.assertEqual(len(merged_props), 3)  # refPropA, directPropInAllOf, directProp
        self.assertIn("refPropA", merged_props)
        self.assertIs(merged_props["refPropA"], ref_schema_a.properties["refPropA"])
        self.assertIn("directPropInAllOf", merged_props)
        self.assertEqual(merged_props["directPropInAllOf"].type, "integer")
        self.assertIn("directProp", merged_props)
        self.assertIs(merged_props["directProp"], direct_prop_schema)

        # Required fields from RefA and the direct "required" list
        self.assertEqual(merged_req, {"refPropA", "directProp"})
        self.assertEqual(len(parsed_components), 2)
        self.assertIs(parsed_components[0], ref_schema_a)
        self.assertEqual(parsed_components[1].properties["directPropInAllOf"].type, "integer")


if __name__ == "__main__":
    unittest.main()
