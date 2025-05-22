import unittest
from typing import Any, Callable, Dict, Mapping, Optional, Set, cast
from unittest.mock import MagicMock

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext

# Updated import for the new location of all_of_parser
from pyopenapi_gen.core.parsing.keywords.all_of_parser import _process_all_of


class TestProcessAllOf(unittest.TestCase):
    def setUp(self) -> None:
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={}, visited_refs=set())
        self.mock_parse_schema_func = MagicMock()

        # Type hint for the mock function
        MockParseSchema = Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext], IRSchema]

        def side_effect_parse_schema(
            schema_name: Optional[str],
            schema_node: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth_override: Optional[int] = None,
            allow_self_reference: bool = False,
        ) -> IRSchema:
            if schema_node and "$ref" in schema_node:
                ref_val = schema_node["$ref"]
                # Simplified ref handling for mock: assume it's a local ref to a schema name
                # and that it might have been parsed already or will be by a recursive call.
                if ref_val.startswith("#/components/schemas/"):
                    referred_name = ref_val.split("/")[-1]
                    if referred_name in context.parsed_schemas:
                        return context.parsed_schemas[referred_name]
                    # If not parsed, create a placeholder or call recursively (simplified for now)
                    # For this mock, we'll assume direct parsing if not found,
                    # to avoid complex recursive mock logic unless necessary.
                    # This part might need to call the mock_parse_schema_func itself if the referred schema is complex.
                    # For now, let's assume it's a simple schema if not found.
                    # Fall through to normal parsing if ref not already in parsed_schemas
                    # This is a simplification; real parsing would fetch the referred schema definition.
                    pass  # Allow falling through to general parsing if ref not found

            if schema_name and schema_name in context.parsed_schemas:
                # If allow_self_reference is false (default) and we hit this,
                # it's a cycle not allowed by the current parsing path.
                # However, for allOf, components are usually parsed independently first.
                return context.parsed_schemas[schema_name]

            # Determine type from schema_node, default to "object" if not specified
            schema_type = "object"  # Default if not specified or if complex (e.g. allOf, oneOf)
            if schema_node:
                schema_type = schema_node.get("type", "object")
                # If 'allOf', 'oneOf', 'anyOf' is present, it's a composite type,
                # but for individual component parsing, the 'type' field might be 'object'.
                # The IRSchema's 'type' field will ultimately reflect the most specific type.

            ir = IRSchema(name=schema_name, type=schema_type)
            if schema_node:
                ir.description = schema_node.get("description")
                if "properties" in schema_node:
                    ir.properties = {}
                    for k, v_node in schema_node["properties"].items():
                        prop_type = "string"  # Default property type
                        prop_name = f"{schema_name}.{k}" if schema_name else k
                        if isinstance(v_node, dict):
                            prop_type = v_node.get("type", "string")
                            # Potentially recursive call for complex properties:
                            # For now, create a simple IRSchema for property.
                            # A more robust mock might call self.mock_parse_schema_func here.
                            ir.properties[k] = IRSchema(
                                name=prop_name, type=prop_type, description=v_node.get("description")
                            )
                        else:  # Should not happen in valid OpenAPI
                            ir.properties[k] = IRSchema(name=prop_name, type="string")

                if "required" in schema_node:
                    ir.required = list(set(schema_node["required"]))  # Ensure it's a list of unique strings

                # Handle other keywords like 'enum', 'format', 'items' if needed for robustness
                if "enum" in schema_node:
                    ir.enum = schema_node["enum"]
                if "format" in schema_node:
                    ir.format = schema_node["format"]
                if "items" in schema_node and isinstance(schema_node["items"], dict):  # Array items
                    # Simplified items handling: create a basic IRSchema for item type
                    # A more robust mock would recursively parse schema_node["items"]
                    item_schema_node = schema_node["items"]
                    item_type = item_schema_node.get("type", "string")
                    item_name = f"{schema_name}.items" if schema_name else "items"
                    ir.items = IRSchema(name=item_name, type=item_type, description=item_schema_node.get("description"))

            if schema_name:
                # Add to context.parsed_schemas only if it's a named schema being defined,
                # not an anonymous inline schema (e.g. a property's schema).
                context.parsed_schemas[schema_name] = ir
            return ir

        self.mock_parse_schema_func.side_effect = side_effect_parse_schema

    def test_simple_all_of_merge(self) -> None:
        """
        Scenario:
            - An OpenAPI schema node contains an `allOf` keyword with two simple sub-schemas.
            - Each sub-schema defines distinct properties and required fields.
        Expected Outcome:
            - `_process_all_of` correctly merges properties from both sub-schemas.
            - All properties are of type IRSchema.
            - Required fields from both sub-schemas are accumulated.
            - Two component IRSchema objects (one for each item in `allOf`) are returned.
        """
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
        """
        Scenario:
            - An OpenAPI schema node has an `allOf` list and also defines properties directly.
        Expected Outcome:
            - `_process_all_of` merges properties from both the `allOf` components and the direct properties.
            - Required fields from both sources are accumulated.
            - The number of parsed components reflects only those in the `allOf` list.
        """
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
        """
        Scenario:
            - An OpenAPI schema node has conflicting property definitions: one directly in the node,
              and others within the `allOf` components. The `allOf` components also conflict with each other.
        Expected Outcome:
            - Properties defined directly on the node take precedence over those from `allOf` components.
            - For conflicting properties within the `allOf` list, the property from the sub-schema that appears *first* in the list wins.
            - The `parsed_components` list should still contain the IRSchema objects for each allOf member, reflecting their original (pre-override) state.
        """
        prop_a_v1 = IRSchema(name="propA", type="string", description="Version 1")
        prop_a_v2 = IRSchema(name="propA", type="integer", description="Version 2")
        prop_a_direct = IRSchema(name="propA", type="boolean", description="Direct Version")

        original_side_effect = self.mock_parse_schema_func.side_effect

        def custom_side_effect(
            name: Optional[str],
            node_data: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: Optional[int] = None,
        ) -> IRSchema:
            if name == "TestSchemaOverride.propA" and node_data and node_data.get("description") == "Direct Version":
                return prop_a_direct
            if node_data and node_data.get("properties") and "propA" in node_data["properties"]:
                if node_data["properties"]["propA"].get("description") == "Version 1":
                    return IRSchema(name=None, properties={"propA": prop_a_v1}, type="object")
                if node_data["properties"]["propA"].get("description") == "Version 2":
                    return IRSchema(name=None, properties={"propA": prop_a_v2}, type="object")
            if callable(original_side_effect):
                return cast(IRSchema, original_side_effect(name, node_data, context))
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

    def test_all_of_conflicting_properties_in_components__first_wins(self) -> None:
        """
        Scenario:
            - An OpenAPI schema node has an `allOf` list where multiple components define the same property.
            - There are no direct properties on the main node to override these.
        Expected Outcome:
            - The property definition from the *first* component in the `allOf` list that defines the property
              should be present in `merged_props`.
            - Subsequent definitions of the same property in other `allOf` components are ignored for merging.
            - `parsed_components` should still reflect the original properties of each component.
        """
        # Arrange
        prop_x_from_comp1 = IRSchema(name="propX", type="string", description="From Component 1")
        prop_x_from_comp2 = IRSchema(name="propX", type="integer", description="From Component 2")

        # Mock the _parse_schema_func to return specific IRSchema instances for each component
        # This allows us to check object identity for the merged property.
        original_side_effect = self.mock_parse_schema_func.side_effect

        comp1_node_data = {
            "type": "object",
            "properties": {"propX": {"type": "string", "description": "From Component 1"}},
        }
        comp2_node_data = {
            "type": "object",
            "properties": {"propX": {"type": "integer", "description": "From Component 2"}},
        }

        # These will be the IRSchema objects returned by the mock when it parses the components
        comp1_ir = IRSchema(name=None, properties={"propX": prop_x_from_comp1}, type="object")
        comp2_ir = IRSchema(name=None, properties={"propX": prop_x_from_comp2}, type="object")

        def custom_side_effect(
            name: Optional[str],
            node_data: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: Optional[int] = None,
        ) -> IRSchema:
            if node_data == comp1_node_data:
                return comp1_ir
            if node_data == comp2_node_data:
                return comp2_ir
            if callable(original_side_effect):
                return cast(IRSchema, original_side_effect(name, node_data, context, max_depth))
            return IRSchema(name=name, type="object")

        self.mock_parse_schema_func.side_effect = custom_side_effect

        node: Dict[str, Any] = {
            "current_schema_name": "TestSchemaAllOfConflictFirstWins",
            "allOf": [
                comp1_node_data,  # propX from comp1 (string)
                comp2_node_data,  # propX from comp2 (integer) - should be ignored for merge
            ],
            # No direct properties for propX
        }

        # Act
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaAllOfConflictFirstWins", self.context, self.mock_parse_schema_func
        )

        # Assert
        self.assertEqual(len(merged_props), 1, "Should only have one merged property 'propX'")
        self.assertIn("propX", merged_props)
        # Verify that the merged propX is the one from the *first* component
        self.assertIs(merged_props["propX"], prop_x_from_comp1)
        self.assertEqual(merged_props["propX"].type, "string")
        self.assertEqual(merged_props["propX"].description, "From Component 1")

        self.assertEqual(len(parsed_components), 2, "Should have two parsed components")
        # Check original properties in parsed_components
        self.assertIs(parsed_components[0], comp1_ir)  # comp1_ir itself has prop_x_from_comp1
        self.assertIs(parsed_components[0].properties["propX"], prop_x_from_comp1)

        self.assertIs(parsed_components[1], comp2_ir)  # comp2_ir itself has prop_x_from_comp2
        self.assertIs(parsed_components[1].properties["propX"], prop_x_from_comp2)

    def test_all_of_accumulate_required(self) -> None:
        """
        Scenario:
            - An OpenAPI schema node defines `required` fields directly and also has `allOf` components
              that define their own `required` fields.
        Expected Outcome:
            - The `merged_req` set should be a union of all `required` fields from the direct node
              and all `allOf` components.
        """
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
        """
        Scenario:
            - An OpenAPI schema node has an `allOf` keyword with an empty list `[]`.
            - The node also defines properties and required fields directly.
        Expected Outcome:
            - `_process_all_of` should handle the empty `allOf` list gracefully.
            - The merged properties and required fields should only come from the direct definitions on the node.
            - The `parsed_components` list should be empty.
        """
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
        """
        Scenario:
            - An `allOf` list contains components that are valid schemas but do not define any properties themselves
              (e.g., a schema that only has a description, or an empty object type).
            - The main node also defines its own properties.
        Expected Outcome:
            - `_process_all_of` correctly parses these components (they are added to `parsed_components`).
            - The `merged_props` should only contain properties from the main node and any other `allOf` components
              that *do* define properties.
            - Schemas without properties in `allOf` should not cause errors or contribute to `merged_props`.
        """
        empty_schema1 = IRSchema(name="Empty1", type="object")
        empty_schema2 = IRSchema(name="Empty2", description="A descriptive schema part")
        prop_a_schema = IRSchema(name="TestSchemaNoPropsInAllOf.propA", type="string")

        call_count = 0

        def no_props_side_effect(
            name: Optional[str],
            node_data: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: Optional[int] = None,
        ) -> IRSchema:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return empty_schema1
            if call_count == 2:
                return empty_schema2
            if name == "TestSchemaNoPropsInAllOf.propA":
                return prop_a_schema
            return IRSchema(name=name, type=node_data.get("type") if node_data else None)

        self.mock_parse_schema_func.side_effect = no_props_side_effect

        node: Dict[str, Any] = {
            "allOf": [
                {"type": "object"},
                {"description": "A descriptive schema part"},
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
        self.assertFalse(parsed_components[0].properties)
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

        def ref_side_effect(
            name: Optional[str],
            node_data: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: Optional[int] = None,
        ) -> IRSchema:
            if node_data and node_data.get("$ref") == "#/components/schemas/RefA":
                return ref_schema_a
            if name == "TestSchemaRefsInComponents.directProp":
                return direct_prop_schema
            if node_data and "directPropInAllOf" in node_data.get("properties", {}):
                return IRSchema(
                    name=None,
                    type="object",
                    properties={"directPropInAllOf": IRSchema(name="directPropInAllOf", type="integer")},
                    required=[],
                )
            return IRSchema(name=name, type=node_data.get("type") if node_data else "object")

        self.mock_parse_schema_func.side_effect = ref_side_effect

        node: Dict[str, Any] = {
            "allOf": [
                {"$ref": "#/components/schemas/RefA"},
                {"type": "object", "properties": {"directPropInAllOf": {"type": "integer"}}},
            ],
            "properties": {"directProp": {"type": "boolean"}},
            "required": ["directProp"],
        }
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaRefsInComponents", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 3)
        self.assertIn("refPropA", merged_props)
        self.assertEqual(merged_props["refPropA"].type, "string")
        self.assertIn("directPropInAllOf", merged_props)
        self.assertEqual(merged_props["directPropInAllOf"].type, "integer")
        self.assertIn("directProp", merged_props)
        self.assertEqual(merged_props["directProp"].type, "boolean")
        self.assertEqual(merged_req, {"refPropA", "directProp"})
        self.assertEqual(len(parsed_components), 2)
        self.assertIs(parsed_components[0], ref_schema_a)
        self.assertEqual(parsed_components[1].properties["directPropInAllOf"].type, "integer")

    def test_all_of_without_type_object_in_components(self) -> None:
        """
        Scenario:
            - An `allOf` list contains a component that implies `type: object` by having a `properties` keyword,
              but does not explicitly state `type: object`.
            - Another component explicitly states `type: object`.
        Expected Outcome:
            - Both components are treated as object schemas and their properties are merged.
            - The implicitly typed object schema is correctly parsed and contributes its properties.
        """
        node: Dict[str, Any] = {
            "allOf": [
                {"properties": {"propA": {"type": "string"}}},  # Implicitly object
                {"type": "object", "properties": {"propB": {"type": "integer"}}},
            ]
        }
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaImplicitObject", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 2)
        self.assertIn("propA", merged_props)
        self.assertEqual(merged_props["propA"].type, "string")
        self.assertIn("propB", merged_props)
        self.assertEqual(merged_props["propB"].type, "integer")
        self.assertEqual(merged_req, set())  # No required fields specified
        self.assertEqual(len(parsed_components), 2)
        # Ensure the first component (implicitly object) was parsed and has propA
        self.assertIsNotNone(parsed_components[0])
        self.assertIn("propA", parsed_components[0].properties)
        self.assertEqual(parsed_components[0].properties["propA"].type, "string")
        # Ensure the second component (explicitly object) was parsed and has propB
        self.assertIsNotNone(parsed_components[1])
        self.assertIn("propB", parsed_components[1].properties)
        self.assertEqual(parsed_components[1].properties["propB"].type, "integer")

    def test_all_of_components_without_properties(self) -> None:
        """
        Scenario:
            - An `allOf` list contains components that are valid schemas (e.g., a string type, an array type)
              but do not themselves have a `.properties` attribute (i.e., they are not object schemas with direct properties).
            - One component in `allOf` *is* an object schema with properties.
        Expected Outcome:
            - `_process_all_of` correctly parses all components and includes them in `parsed_components`.
            - Only the properties from the object schema component contribute to `merged_props`.
            - Non-object schemas in `allOf` do not cause errors and are correctly ignored for property merging.
        """
        # Arrange
        # Mock parse_fn to simulate parsing schemas that don't have .properties
        schema_no_props1 = IRSchema(name="NoProps1", type="string")
        schema_with_props = IRSchema(
            name="WithProps", type="object", properties={"p1": IRSchema(name="p1", type="integer")}
        )
        schema_no_props2 = IRSchema(name="NoProps2", type="array", items=IRSchema(type="string"))

        call_idx = 0
        schemas_to_return = [schema_no_props1, schema_with_props, schema_no_props2]

        def side_effect_no_props_components(
            name: Optional[str],
            node_data: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: Optional[int] = None,
        ) -> IRSchema:
            nonlocal call_idx
            # Return schema from list for allOf components
            if name is None and node_data and node_data.get("custom_marker") is not None:
                marker_index = node_data.get("custom_marker")
                # We need to ensure marker_index is an int if it's used as list index
                if isinstance(marker_index, int) and 0 <= marker_index < len(schemas_to_return):
                    schema_to_return = schemas_to_return[marker_index]
                    call_idx += 1
                    return schema_to_return
            # Fallback for direct properties if any
            return IRSchema(name=name, type=node_data.get("type") if node_data else "object")

        self.mock_parse_schema_func.side_effect = side_effect_no_props_components

        node: Dict[str, Any] = {
            "allOf": [
                {"custom_marker": 0, "description": "Ref to string type"},  # -> schema_no_props1
                {"custom_marker": 1, "description": "Actual object with props"},  # -> schema_with_props
                {"custom_marker": 2, "description": "Ref to array type"},  # -> schema_no_props2
            ]
        }
        merged_props, merged_req, parsed_components = _process_all_of(
            node, "TestSchemaNoPropsMerge", self.context, self.mock_parse_schema_func
        )
        self.assertEqual(len(merged_props), 1)
        self.assertIn("p1", merged_props)
        self.assertEqual(merged_props["p1"].type, "integer")
        self.assertEqual(merged_req, set())
        self.assertEqual(len(parsed_components), 3)
        self.assertIs(parsed_components[0], schema_no_props1)
        self.assertIs(parsed_components[1], schema_with_props)
        self.assertIs(parsed_components[2], schema_no_props2)

    def test_no_all_of_key_only_direct_properties(self) -> None:
        """
        Scenario:
            - An OpenAPI schema node does NOT contain an `allOf` keyword.
            - The node defines properties and required fields directly.
        Expected Outcome:
            - `_process_all_of` should process only the direct properties and required fields.
            - The `parsed_components` list should be empty.
            - The `_parse_schema_func` should be called for each direct property.
        """
        node: Dict[str, Any] = {
            "properties": {
                "propX": {"type": "string"},
                "propY": {"type": "integer"},
            },
            "required": ["propX"],
        }
        current_schema_name = "TestSchemaNoAllOf"

        # Configure mock to check calls for direct properties
        prop_x_schema = IRSchema(name=f"{current_schema_name}.propX", type="string")
        prop_y_schema = IRSchema(name=f"{current_schema_name}.propY", type="integer")

        def side_effect_for_direct_props(
            name: Optional[str],
            node_data: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: Optional[int] = None,
        ) -> IRSchema:
            if name == f"{current_schema_name}.propX":
                return prop_x_schema
            if name == f"{current_schema_name}.propY":
                return prop_y_schema
            self.fail(f"Unexpected call to mock_parse_schema_func: name={name}, node_data={node_data}")
            return IRSchema()  # Should not reach here

        self.mock_parse_schema_func.side_effect = side_effect_for_direct_props

        merged_props, merged_req, parsed_components = _process_all_of(
            node, current_schema_name, self.context, self.mock_parse_schema_func
        )

        self.assertEqual(len(merged_props), 2)
        self.assertIn("propX", merged_props)
        self.assertIs(merged_props["propX"], prop_x_schema)
        self.assertIn("propY", merged_props)
        self.assertIs(merged_props["propY"], prop_y_schema)

        self.assertEqual(merged_req, {"propX"})
        self.assertEqual(len(parsed_components), 0)

        self.mock_parse_schema_func.assert_any_call(
            f"{current_schema_name}.propX",
            node["properties"]["propX"],
            self.context,
            100,  # Assuming default max_depth
        )
        self.mock_parse_schema_func.assert_any_call(
            f"{current_schema_name}.propY",
            node["properties"]["propY"],
            self.context,
            100,  # Assuming default max_depth
        )
        self.assertEqual(self.mock_parse_schema_func.call_count, 2)

    def test_process_all_of__node_is_empty_mapping__raises_assertionerror(self) -> None:
        """
        Scenario:
            - _process_all_of is called with an empty mapping for the node.
        Expected Outcome:
            - Raises AssertionError due to pre-condition `node must be a non-empty Mapping`.
        """
        # Arrange
        empty_node: Dict[str, Any] = {}

        # Act & Assert
        with self.assertRaisesRegex(AssertionError, "node must be a non-empty Mapping"):
            _process_all_of(empty_node, "TestSchemaEmptyNode", self.context, self.mock_parse_schema_func)


if __name__ == "__main__":
    unittest.main()
