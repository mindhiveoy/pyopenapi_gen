"""
Tests for the _parse_properties helper function in keywords.properties_parser.
"""

import logging
import unittest
from typing import Any, Callable, Mapping, Optional
from unittest.mock import MagicMock, patch

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.keywords.properties_parser import _parse_properties

# For mocking the transformers if needed by some tests
# from pyopenapi_gen.core.parsing.transformers import inline_enum_extractor, inline_object_promoter


class TestParseProperties(unittest.TestCase):
    def setUp(self) -> None:
        """Set up for test cases."""
        self.context = ParsingContext(raw_spec_schemas={}, parsed_schemas={}, visited_refs=set())
        self.logger = logging.getLogger("test_properties_parser")
        self.logger.setLevel(logging.CRITICAL)  # Keep logs quiet during most tests

        self.mock_recursive_parse_fn = MagicMock(
            spec=Callable[[str | None, Optional[Mapping[str, Any]], ParsingContext, int], IRSchema]
        )

        # A default side effect for the main parse_fn passed to _parse_properties
        def default_recursive_parse_side_effect(
            name: str | None,
            node: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: int,
        ) -> IRSchema:
            # This mock simulates that the recursive call to _parse_schema happens
            # and returns a basic IRSchema. For specific tests, this can be overridden.
            return IRSchema(name=name, type=node.get("type", "object") if node else "object")

        self.default_parse_fn_side_effect = default_recursive_parse_side_effect
        self.mock_recursive_parse_fn.side_effect = self.default_parse_fn_side_effect

    def test_empty_properties_node(self) -> None:
        """
        Scenario:
            - The `_parse_properties` function is called with an empty `node_properties` dictionary.
            - This represents an OpenAPI object schema with no properties defined under the `properties` keyword.
        Expected Outcome:
            - The function should return an empty dictionary `{}`.
            - The recursive `parse_fn` should not be called.
        """
        # Arrange
        node_properties: dict[str, Any] = {}

        # Act
        parsed_props = _parse_properties(
            node_properties, "ParentSchema", self.context, 10, self.mock_recursive_parse_fn, self.logger
        )

        self.assertEqual(parsed_props, {})
        self.mock_recursive_parse_fn.assert_not_called()

    def test_single_simple_property(self) -> None:
        """
        Scenario:
            - An OpenAPI object schema has a single property with a simple type (e.g., string).
            - This property is not an inline enum and does not qualify for inline object promotion.
        Expected Outcome:
            - `_extract_enum_from_property_node` is called and returns None.
            - The recursive `parse_fn` is called to parse the property's schema.
            - `_attempt_promote_inline_object` is called with the parsed property schema and returns None.
            - The final parsed property in the result dictionary is the IRSchema returned by `parse_fn`.
        """
        # Arrange
        node_properties: dict[str, Any] = {"name": {"type": "string"}}
        parent_schema_name = "ParentSchema"
        expected_prop_schema_name = "ParentSchemaName"

        expected_name_prop_schema = IRSchema(name=expected_prop_schema_name, type="string")
        self.mock_recursive_parse_fn.return_value = expected_name_prop_schema

        # Mock _attempt_promote_inline_object to return None (not promoted)
        with patch(
            "pyopenapi_gen.core.parsing.keywords.properties_parser._attempt_promote_inline_object",
            return_value=None,
        ) as mock_promote_object:
            # Act
            parsed_props = _parse_properties(
                node_properties, parent_schema_name, self.context, 10, self.mock_recursive_parse_fn, self.logger
            )

        # Assert
        self.assertEqual(len(parsed_props), 1)
        self.assertIn("name", parsed_props)
        self.assertEqual(parsed_props["name"], expected_name_prop_schema)

        self.mock_recursive_parse_fn.assert_called_once_with(
            expected_prop_schema_name, node_properties["name"], self.context, 10
        )
        mock_promote_object.assert_called_once_with(
            parent_schema_name,
            "name",
            expected_name_prop_schema,
            self.context,
            self.logger,
        )

    def test_property_is_inline_enum(self) -> None:
        """
        Scenario:
            - A property is an inline enum.
        Expected Outcome:
            - The main `parse_fn` (mock_recursive_parse_fn) is called to parse the property.
            - `parse_fn` is expected to correctly parse the enum and return an appropriate IRSchema.
            - `_attempt_promote_inline_object` is called with the result of `parse_fn`.
            - The IRSchema for the enum (returned by `parse_fn`) is used in the result.
        """
        # Arrange
        node_properties: dict[str, Any] = {"status": {"type": "string", "enum": ["active", "inactive"]}}
        parent_schema_name = "MySchema"
        expected_prop_schema_name = "MySchemaStatus"

        # This IRSchema would be returned by parse_fn if it correctly parses the enum
        enum_prop_ir = IRSchema(name=expected_prop_schema_name, type="MySchemaStatusEnum", description="Status enum")
        enum_prop_ir.original_type = "string"  # type: ignore
        enum_prop_ir.enum_values = ["active", "inactive"]  # type: ignore
        self.mock_recursive_parse_fn.return_value = enum_prop_ir

        # Set side_effect for this test specifically to ensure correct mock return
        def specific_parse_fn_for_enum_test(
            name: str | None,
            node: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: int,  # Match spec of self.mock_recursive_parse_fn
        ) -> IRSchema:
            # Add assertions here if needed to check args, e.g., self.assertEqual(name, expected_prop_schema_name)
            return enum_prop_ir

        self.mock_recursive_parse_fn.side_effect = specific_parse_fn_for_enum_test

        # Mock _attempt_promote_inline_object to return None (not promoted)
        with patch(
            "pyopenapi_gen.core.parsing.keywords.properties_parser._attempt_promote_inline_object",
            return_value=None,
        ) as mock_promote_object:
            # Act
            parsed_props = _parse_properties(
                node_properties, parent_schema_name, self.context, 10, self.mock_recursive_parse_fn, self.logger
            )

        # Assert
        self.assertEqual(len(parsed_props), 1)
        self.assertIn("status", parsed_props)
        # The result should be what parse_fn returned, as _attempt_promote_inline_object returned None
        self.assertIs(parsed_props["status"], enum_prop_ir)

        self.mock_recursive_parse_fn.assert_called_once_with(
            expected_prop_schema_name, node_properties["status"], self.context, 10
        )
        mock_promote_object.assert_called_once_with(
            parent_schema_name,
            "status",
            enum_prop_ir,
            self.context,
            self.logger,
        )

    def test_property_is_inline_object_promoted(self) -> None:
        """
        Scenario:
            - A property is an inline object that gets promoted.
        Expected Outcome:
            - _extract_enum_from_property_node returns None.
            - The main parse_fn is called.
            - _attempt_promote_inline_object is called with the result of parse_fn and returns a promoted schema.
            - The promoted schema is used in the result.
        """
        # Arrange
        node_properties: dict[str, Any] = {"details": {"type": "object", "properties": {"id": {"type": "integer"}}}}
        parent_schema_name = "Order"
        expected_prop_schema_name = "OrderDetails"

        parsed_inline_object_ir = IRSchema(
            name=expected_prop_schema_name, type="object", properties={"id": IRSchema(name="Id", type="integer")}
        )
        # self.mock_recursive_parse_fn.return_value = parsed_inline_object_ir # Original line

        # Replace return_value with a specific side_effect for this test case
        def specific_parse_fn_side_effect(
            name: str | None,
            node: Optional[Mapping[str, Any]],
            context: ParsingContext,
            max_depth: int,
        ) -> IRSchema:
            return parsed_inline_object_ir

        self.mock_recursive_parse_fn.side_effect = specific_parse_fn_side_effect

        promoted_object_ref_ir = IRSchema(name="details", type="OrderDetails", description="Promoted details")
        promoted_object_ref_ir._refers_to_schema = IRSchema(
            name="OrderDetails", type="object"
        )  # Mock the referred schema

        # Mock _attempt_promote_inline_object to return the promoted schema
        with patch(
            "pyopenapi_gen.core.parsing.keywords.properties_parser._attempt_promote_inline_object",
            return_value=promoted_object_ref_ir,
        ) as mock_promote_object:
            # Act
            parsed_props = _parse_properties(
                node_properties, parent_schema_name, self.context, 10, self.mock_recursive_parse_fn, self.logger
            )

        # Assert
        self.assertEqual(len(parsed_props), 1)
        self.assertIn("details", parsed_props)
        self.assertEqual(parsed_props["details"], promoted_object_ref_ir)

        self.mock_recursive_parse_fn.assert_called_once_with(
            expected_prop_schema_name, node_properties["details"], self.context, 10
        )
        mock_promote_object.assert_called_once_with(
            parent_schema_name,
            "details",
            parsed_inline_object_ir,
            self.context,
            self.logger,
        )

    def test_parent_schema_name_is_none(self) -> None:
        """
        Scenario:
            - _parse_properties is called with parent_schema_name as None.
        Expected Outcome:
            - Contextual names for properties (passed to parse_fn, enum extractor, promoter) are just prop_key.
            - Parsing proceeds normally.
        """
        # Arrange
        node_properties: dict[str, Any] = {"data": {"type": "string"}}
        parent_schema_name = None  # Key aspect of this test
        expected_prop_schema_name = "Data_"  # 'data' is sanitized to 'data_'

        expected_data_prop_schema = IRSchema(name=expected_prop_schema_name, type="string")  # Name becomes prop_key
        self.mock_recursive_parse_fn.return_value = expected_data_prop_schema

        # Reset side_effect to the default one from setUp for this test.
        self.mock_recursive_parse_fn.side_effect = self.default_parse_fn_side_effect
        # The default side_effect should produce the expected_data_prop_schema correctly.
        # self.mock_recursive_parse_fn.return_value = expected_data_prop_schema # This would be ignored

        # Mock _attempt_promote_inline_object (assume no promotion for this simple case)
        with patch(
            "pyopenapi_gen.core.parsing.keywords.properties_parser._attempt_promote_inline_object",
            return_value=None,
        ) as mock_promote_object:
            # Act
            parsed_props = _parse_properties(
                node_properties, parent_schema_name, self.context, 10, self.mock_recursive_parse_fn, self.logger
            )

        # Assert
        self.assertEqual(len(parsed_props), 1)
        self.assertIn("data", parsed_props)
        self.assertEqual(parsed_props["data"], expected_data_prop_schema)

        self.mock_recursive_parse_fn.assert_called_once_with(
            expected_prop_schema_name, node_properties["data"], self.context, 10
        )
        mock_promote_object.assert_called_once_with(
            None,  # Positional (parent_schema_name)
            "data",  # Positional
            expected_data_prop_schema,
            self.context,
            self.logger,
        )

    def test_multiple_mixed_properties(self) -> None:
        """
        Scenario:
            - Parse a schema with multiple properties: a simple type, an inline enum,
              and an inline object that gets promoted.
        Expected Outcome:
            - Each property is processed correctly according to its type.
            - _extract_enum_from_property_node, parse_fn, and _attempt_promote_inline_object
              are called appropriately for each property.
            - The final parsed_props map contains the correct IRSchema for each property.
        """
        # Arrange
        parent_schema_name = "ComplexSchema"
        node_properties: dict[str, Any] = {
            "id": {"type": "string"},
            "status": {"type": "string", "enum": ["active", "pending"]},
            "config": {"type": "object", "properties": {"timeout": {"type": "integer"}}},
        }

        # Expected contextual names for parse_fn calls (with name sanitization)
        expected_id_name = "ComplexSchemaId_"  # 'id' is sanitized to 'id_'
        expected_status_name = "ComplexSchemaStatus"
        expected_config_name = "ComplexSchemaConfig_"  # 'config' is sanitized to 'config_'

        # Mock IRSchema returns for each property
        # Note: IRSchema.__post_init__ calls NameSanitizer.sanitize_class_name() which removes trailing underscores
        id_schema = IRSchema(name="ComplexSchemaId", type="string")  # Will be sanitized from "ComplexSchemaId_"
        status_enum_schema = IRSchema(name=expected_status_name, type="ComplexSchemaStatusEnum", enum=["on", "off"])
        config_object_schema = IRSchema(
            name="ComplexSchemaConfig", type="object", properties={"setting": IRSchema(name="Setting", type="boolean")}
        )  # Will be sanitized from "ComplexSchemaConfig_"

        # General mock setup
        def selective_parse_fn_side_effect(
            name: str | None, node: Optional[Mapping[str, Any]], context: ParsingContext, max_depth: int
        ) -> IRSchema:
            if name == expected_id_name:
                return id_schema
            elif name == expected_status_name:
                return status_enum_schema
            elif name == expected_config_name:
                return config_object_schema
            self.fail(f"Unexpected call to mock_recursive_parse_fn with name: {name}")
            return IRSchema()

        self.mock_recursive_parse_fn.side_effect = selective_parse_fn_side_effect

        # Mock the transformer functions
        mock_enum_extractor = MagicMock(return_value=None)  # Default to no enum extracted
        mock_object_promoter = MagicMock(return_value=None)  # Default to no object promoted

        # Side effect for _attempt_promote_inline_object for this specific test
        def object_promoter_side_effect(
            parent_name_arg: str | None,
            prop_key_arg: str,
            property_schema_obj_arg: IRSchema,
            context: ParsingContext,
            logger: logging.Logger,
        ) -> Optional[IRSchema]:
            if prop_key_arg == "config":
                self.assertEqual(property_schema_obj_arg.name, "ComplexSchemaConfig")  # After sanitization
                promoted_ref = IRSchema(
                    name="Config", type="ComplexSchemaConfigPromoted"
                )  # Name will be sanitized to Config_
                promoted_ref._refers_to_schema = property_schema_obj_arg
                return promoted_ref
            return None

        mock_object_promoter.side_effect = object_promoter_side_effect

        with patch(
            "pyopenapi_gen.core.parsing.keywords.properties_parser._attempt_promote_inline_object",
            mock_object_promoter,
        ):  # Removed patch for _extract_enum_from_property_node
            # Act
            parsed_props = _parse_properties(
                node_properties, parent_schema_name, self.context, 10, self.mock_recursive_parse_fn, self.logger
            )

        # Assert
        self.assertEqual(len(parsed_props), 3)

        # Assert 'id' property (simple)
        self.assertIn("id", parsed_props)
        self.assertIs(parsed_props["id"], id_schema)
        mock_object_promoter.assert_any_call(parent_schema_name, "id", id_schema, self.context, self.logger)

        # Assert 'status' property (enum)
        self.assertIn("status", parsed_props)
        self.assertIs(parsed_props["status"], status_enum_schema)
        mock_object_promoter.assert_any_call(
            parent_schema_name, "status", status_enum_schema, self.context, self.logger
        )

        # Assert 'config' property (promoted object)
        self.assertIn("config", parsed_props)
        self.assertEqual(parsed_props["config"].name, "Config_")  # After sanitization (config is a built-in)
        self.assertEqual(parsed_props["config"].type, "ComplexSchemaConfigPromoted")
        self.assertIs(parsed_props["config"]._refers_to_schema, config_object_schema)
        mock_object_promoter.assert_any_call(
            parent_schema_name, "config", config_object_schema, self.context, self.logger
        )

        # Verify overall call counts if precise control is needed
        self.assertEqual(mock_object_promoter.call_count, 3)

        # Verify calls to parse_fn
        self.mock_recursive_parse_fn.assert_any_call(expected_id_name, node_properties["id"], self.context, 10)
        self.mock_recursive_parse_fn.assert_any_call(expected_status_name, node_properties["status"], self.context, 10)
        self.mock_recursive_parse_fn.assert_any_call(expected_config_name, node_properties["config"], self.context, 10)

    def test_parse_property_with_invalid_schema_node_type(self) -> None:
        """
        Scenario:
            - A property schema node is of an invalid type (e.g., a list) instead of a dictionary.
        Expected Outcome:
            - `parse_fn` is called with the invalid node.
            - `parse_fn` (simulating _parse_schema) should handle this gracefully (e.g., return a basic IRSchema).
            - The `isinstance(prop_schema_node, Mapping)` guard in `_parse_properties` prevents a TypeError
              during the `$ref` check for non-Mapping nodes.
            - `_attempt_promote_inline_object` is called with the result from `parse_fn`.
            - The property is added to the result map.
        """
        # Arrange
        # Invalid: property schema is a list, not a dict
        node_properties: dict[str, Any] = {"invalid_list_prop": ["not", "a", "dict"]}
        parent_schema_name = "BadProps"
        expected_prop_schema_name = "BadPropsInvalidListProp"

        # Expected IRSchema that mock_recursive_parse_fn should return for this invalid property node
        # _parse_schema would typically log a warning and return a basic schema
        expected_parsed_invalid_prop_schema = IRSchema(
            name=expected_prop_schema_name, type="object", description="Parsed from invalid node type"
        )

        def side_effect_for_invalid_node(
            name: str | None,
            node: Optional[Mapping[str, Any]],  # Note: actual node will be List here
            context: ParsingContext,
            max_depth: int,
        ) -> IRSchema:
            if name == expected_prop_schema_name and isinstance(node, list):
                # Simulate _parse_schema behavior: log warning (not tested here) and return basic schema
                return expected_parsed_invalid_prop_schema
            # Fallback or raise error if called unexpectedly
            return IRSchema(name=name, type="fallback")

        self.mock_recursive_parse_fn.side_effect = side_effect_for_invalid_node

        with patch(
            "pyopenapi_gen.core.parsing.keywords.properties_parser._attempt_promote_inline_object",
            return_value=None,  # Assume no promotion for this case
        ) as mock_promote_object:
            # Act
            parsed_props = _parse_properties(
                node_properties, parent_schema_name, self.context, 10, self.mock_recursive_parse_fn, self.logger
            )

        # Assert
        self.assertEqual(len(parsed_props), 1)
        self.assertIn("invalid_list_prop", parsed_props)
        self.assertIs(parsed_props["invalid_list_prop"], expected_parsed_invalid_prop_schema)

        self.mock_recursive_parse_fn.assert_called_once_with(
            expected_prop_schema_name, node_properties["invalid_list_prop"], self.context, 10
        )
        mock_promote_object.assert_called_once_with(
            parent_schema_name,  # Positional
            "invalid_list_prop",  # Positional
            expected_parsed_invalid_prop_schema,
            self.context,
            self.logger,
        )


if __name__ == "__main__":
    unittest.main()
