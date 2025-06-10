"""Tests for logging behavior in schema parsing."""

import os
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pyopenapi_gen.core.parsing.schema_parser as schema_parser_module
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema

# If schema_parser is used directly for its logger, ensure it's imported
# For example, if tests use: with patch.object(schema_parser.logger, ... )
# Ensure schema_parser is available. It seems schema_parser_module is intended for this.

# Define a depth for tests that need it.
depth = 2


class TestLogging(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test environment."""
        # Store original environment variables
        self.original_debug_cycles = os.environ.get("PYOPENAPI_DEBUG_CYCLES")
        self.original_max_depth = os.environ.get("PYOPENAPI_MAX_DEPTH")

        # Set test environment variables
        os.environ["PYOPENAPI_DEBUG_CYCLES"] = "1"  # This will be ignored by schema_parser now
        os.environ["PYOPENAPI_MAX_DEPTH"] = "2"

        # Reload schema_parser to ensure it picks up the patched environment variables
        # for its module-level constants like ENV_MAX_DEPTH.
        # DEBUG_CYCLES constant is no longer in schema_parser.
        import importlib

        import pyopenapi_gen.core.parsing.schema_parser

        importlib.reload(pyopenapi_gen.core.parsing.schema_parser)

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Restore original environment variables
        if self.original_debug_cycles is not None:
            os.environ["PYOPENAPI_DEBUG_CYCLES"] = self.original_debug_cycles
        elif "PYOPENAPI_DEBUG_CYCLES" in os.environ:  # Ensure key exists before del
            del os.environ["PYOPENAPI_DEBUG_CYCLES"]

        if self.original_max_depth is not None:
            os.environ["PYOPENAPI_MAX_DEPTH"] = self.original_max_depth
        elif "PYOPENAPI_MAX_DEPTH" in os.environ:  # Ensure key exists before del
            del os.environ["PYOPENAPI_MAX_DEPTH"]

    @patch("pyopenapi_gen.core.parsing.cycle_helpers.logger")
    def test_max_depth_exceeded_logging(self, mock_logger: MagicMock) -> None:
        """Test that exceeding maximum depth is logged."""
        # PYOPENAPI_MAX_DEPTH = "2" is set in setUp
        # Max depth warning comes from cycle_helpers.logger
        context = ParsingContext()

        # Create a deeply nested schema that will exceed depth 2 (root is depth 1)
        # Item -> ItemPropertiesItem -> ItemPropertiesItemPropertiesItem (depth 3, exceeds 2)
        schema: Dict[str, Any] = {
            "type": "object",  # Depth 1: DeepSchema
            "properties": {
                "level1": {  # Depth 2: anonymous object for level1, name passed to _parse_schema might be DeepSchemaLevel1 or None
                    "type": "object",
                    "properties": {
                        "level2": {  # Depth 3: anonymous object for level2, name passed to _parse_schema might be DeepSchemaLevel1Level2 or None
                            "type": "object",
                            "properties": {"final": {"type": "string"}},
                        }
                    },
                }
            },
        }
        # Ensure schema is in raw_spec_schemas if it had a name and $refs, not strictly needed here as no $refs.

        # Parse the schema
        result = _parse_schema("DeepSchema", schema, context)

        # Verify logging. Max depth is hit when parsing an anonymous inner object.
        # The original_name passed to _handle_max_depth_exceeded will be the derived name like "ParentNamePropNameNestedPropName"
        # Corrected: based on how _parse_schema constructs names for recursive calls to properties:
        # DeepSchema -> DeepSchemaLevel1 -> DeepSchemaLevel1Level2
        expected_logged_name = "DeepSchemaLevel1Level2"
        expected_log = f"[Maximum recursion depth (2) exceeded for '{expected_logged_name}']"

        mock_logger.warning.assert_any_call(expected_log)

        # Check the flags on the actual schema that hit the max depth and became a placeholder.
        self.assertIsNotNone(result.properties, "DeepSchema should have properties.")
        level1_property_entry = result.properties.get(
            "level1"
        )  # This is an IRSchema for the property, referencing the actual schema
        self.assertIsNotNone(level1_property_entry, "Property 'level1' not found in DeepSchema.")

        if level1_property_entry:  # Linter fix
            actual_level1_schema = level1_property_entry._refers_to_schema
            self.assertIsNotNone(
                actual_level1_schema,
                "The 'level1' property should refer to an actual schema definition (DeepSchemaLevel1).",
            )
            if actual_level1_schema:  # Linter fix
                self.assertEqual(actual_level1_schema.name, "DeepSchemaLevel1")
                self.assertIsNotNone(actual_level1_schema.properties, "Actual DeepSchemaLevel1 should have properties.")

                if actual_level1_schema.properties:  # Linter fix
                    level2_property_entry = actual_level1_schema.properties.get("level2")
                    self.assertIsNotNone(
                        level2_property_entry, "Property 'level2' not found in actual DeepSchemaLevel1 properties."
                    )

                    if level2_property_entry:  # Linter fix
                        actual_level2_placeholder_schema = level2_property_entry._refers_to_schema
                        self.assertIsNotNone(
                            actual_level2_placeholder_schema,
                            "The 'level2' property should refer to an actual schema definition (the placeholder DeepSchemaLevel1Level2).",
                        )
                        if actual_level2_placeholder_schema:  # Linter fix
                            self.assertEqual(actual_level2_placeholder_schema.name, "DeepSchemaLevel1Level2")

                            self.assertTrue(
                                actual_level2_placeholder_schema._max_depth_exceeded_marker,
                                "DeepSchemaLevel1Level2 placeholder schema should be marked _max_depth_exceeded_marker",
                            )

    @patch("pyopenapi_gen.core.parsing.schema_parser.logger")
    @patch.dict(os.environ, {"PYOPENAPI_DEBUG_CYCLES": "0"})
    def test_debug_cycles_disabled(self, mock_schema_logger: MagicMock) -> None:
        """Test that debug logs (which are now removed) are not emitted.
        This test effectively now checks that no new debug logs were inadvertently added
        to schema_parser.logger, and that PYOPENAPI_DEBUG_CYCLES env var (now unused by schema_parser)
        doesn't cause issues.
        """
        # Reload schema_parser to re-evaluate module-level logic with the patched environment
        # (though DEBUG_CYCLES is no longer used by schema_parser for its logger).
        import importlib

        import pyopenapi_gen.core.parsing.schema_parser

        importlib.reload(pyopenapi_gen.core.parsing.schema_parser)

        context = ParsingContext(raw_spec_schemas={})
        _parse_schema("SimpleSchema", {"type": "object", "properties": {"name": {"type": "string"}}}, context)
        mock_schema_logger.debug.assert_not_called()

        # Test with a cycle to ensure no debug logs related to cycle yielding appear
        mock_schema_logger.reset_mock()
        context.reset_for_new_parse()
        context.raw_spec_schemas = {
            "SelfRef": {"type": "object", "properties": {"next": {"$ref": "#/components/schemas/SelfRef"}}}
        }
        _parse_schema(
            "SelfRef",
            {"$ref": "#/components/schemas/SelfRef"},
            context,
        )
        mock_schema_logger.debug.assert_not_called()

    def test_invalid_reference_handling(self) -> None:
        """Test that invalid references are handled by creating placeholder schemas."""
        context = ParsingContext()

        # Create a schema with invalid reference
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {"invalid": {"$ref": "#/components/schemas/NonExistent"}},
        }
        # schema_name for the parent schema
        parent_schema_name = "InvalidRef"
        # property_name with the unresolvable ref
        property_name_with_ref = "invalid"

        context.raw_spec_schemas[parent_schema_name] = schema

        result = _parse_schema(parent_schema_name, schema, context)

        # The result here is for "InvalidRef". Its property "invalid" would be an IRSchema placeholder.
        self.assertIsNotNone(result.properties)
        if result.properties:
            # The property key remains "invalid". The IRSchema.name for this property will be the property name.
            invalid_prop_schema = result.properties.get(property_name_with_ref)  # Use original key
            self.assertIsNotNone(
                invalid_prop_schema, f"Property '{property_name_with_ref}' not found in {result.properties.keys()}"
            )
            if invalid_prop_schema:
                # Check that the IRSchema for the property uses the target schema name from the ref
                self.assertEqual(invalid_prop_schema.name, "NonExistent")

    @patch("pyopenapi_gen.core.parsing.schema_parser.logger")
    def test_allow_self_reference(self, mock_logger: MagicMock) -> None:
        """Test that allow_self_reference parameter works correctly."""
        context = ParsingContext(raw_spec_schemas={}, raw_spec_components={})

        # Test with allow_self_reference=True because DeepSchema refers to itself.
        schema = {
            "type": "object",
            "properties": {f"prop{i}": {"$ref": "#/components/schemas/DeepSchema"} for i in range(depth)},
        }
        context = ParsingContext(raw_spec_schemas={"DeepSchema": schema}, raw_spec_components={})
        result = _parse_schema("DeepSchema", schema, context, allow_self_reference=True)
        self.assertEqual(result.name, "DeepSchema")
        # Verify logger calls if necessary, e.g. mock_logger.debug.assert_any_call(...)

        with patch.object(schema_parser_module, "logger") as mock_logger_simple:
            _parse_schema(
                "SimpleSchema",
                {"type": "object", "properties": {"name": {"type": "string"}}},
                context,
                allow_self_reference=False,
            )
            mock_logger_simple.warning.assert_not_called()

        with patch.object(schema_parser_module, "logger") as mock_logger_invalid_prop:
            _parse_schema(
                "InvalidPropSchema",
                {"type": "object", "properties": {123: {"type": "string"}}},
                context,
                allow_self_reference=False,
            )
            mock_logger_invalid_prop.warning.assert_called_once()
            assert "Skipping property with invalid name '123'" in mock_logger_invalid_prop.warning.call_args[0][0]

        parent_schema_name = "ParentTestSchema"
        child_schema_name = "ChildTestSchema"
        child_schema = {"type": "string"}

        schema = {"type": "object", "properties": {"child": {"$ref": f"#/components/schemas/{child_schema_name}"}}}
        context = ParsingContext(
            raw_spec_schemas={parent_schema_name: schema, child_schema_name: child_schema}, raw_spec_components={}
        )
        # Test with allow_self_reference=True as this test might involve complex scenarios
        result = _parse_schema(parent_schema_name, schema, context, allow_self_reference=True)
        assert result is not None

    @patch("pyopenapi_gen.core.parsing.schema_parser.logger")
    def test_parse_schema_with_valid_and_invalid_properties(self, mock_logger: MagicMock) -> None:
        """Test _parse_schema logs warning for invalid property names and skips them."""
        context = ParsingContext(raw_spec_schemas={}, raw_spec_components={})
        _parse_schema(
            "TestSchema",
            {"type": "object", "properties": {"validName": {"type": "string"}, 123: {"type": "integer"}}},
            context,
            allow_self_reference=False,
        )
        mock_logger.warning.assert_called_once()
        self.assertIn("Skipping property with invalid name '123'", mock_logger.warning.call_args[0][0])

    @patch("pyopenapi_gen.core.parsing.schema_parser.logger")
    def test_parse_schema_ref_resolution_warning(self, mock_logger: MagicMock) -> None:
        """Test _parse_schema logs warning for unresolvable $ref."""
        context = ParsingContext(raw_spec_schemas={}, raw_spec_components={})
        _parse_schema("TestSchema", {"$ref": "#/components/schemas/NonExistent"}, context, allow_self_reference=False)
        mock_logger.warning.assert_called_once()
        self.assertIn(
            "Cannot resolve $ref '#/components/schemas/NonExistent' for parent 'TestSchema'. "
            "Target 'NonExistent' not in raw_spec_schemas. Returning placeholder.",
            mock_logger.warning.call_args[0][0],
        )

    def test_parse_property_ref_resolution(self) -> None:
        """Test _parse_schema handles unresolvable $ref in a property by creating a placeholder."""
        parent_schema_name = "ParentSchemaWithBadRef"
        schema_data = {
            "type": "object",
            "properties": {"child": {"$ref": "#/components/schemas/NonExistentChild"}},
        }
        context = ParsingContext(raw_spec_schemas={parent_schema_name: schema_data}, raw_spec_components={})
        result = _parse_schema(parent_schema_name, schema_data, context, allow_self_reference=False)

        # Should have the property with a placeholder schema
        self.assertIsNotNone(result.properties)
        self.assertIn("child", result.properties)
        child_schema = result.properties["child"]
        self.assertEqual(child_schema.name, "NonExistentChild")
        # generation_name might be None for unresolved refs
        self.assertIsNotNone(child_schema)


if __name__ == "__main__":
    unittest.main()
