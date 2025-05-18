"""Tests for logging behavior in schema parsing."""

import os
import unittest
from typing import Any, Dict
from unittest.mock import MagicMock, patch

from pyopenapi_gen.core.parsing.common.ref_resolution import resolve_schema_ref
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema


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
                                actual_level2_placeholder_schema._is_circular_ref,
                                "DeepSchemaLevel1Level2 placeholder schema should be marked _is_circular_ref",
                            )
                            self.assertTrue(
                                actual_level2_placeholder_schema._from_unresolved_ref,
                                "DeepSchemaLevel1Level2 placeholder schema should be marked _from_unresolved_ref",
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

    @patch("pyopenapi_gen.core.parsing.schema_parser.logger")
    def test_invalid_reference_logging(self, mock_logger: MagicMock) -> None:
        """Test that invalid references are logged by schema_parser for property $refs."""
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
        # The unresolvable $ref path
        unresolvable_ref_path = "#/components/schemas/NonExistent"

        context.raw_spec_schemas[parent_schema_name] = schema

        result = _parse_schema(parent_schema_name, schema, context)

        # Expected log message from schema_parser.py for an unresolvable property $ref:
        # f"Property '{prop_name}' in schema '{schema_name or 'anonymous'}' has unresolvable $ref '{ref_path}'. Creating placeholder."
        expected_log_message = (
            f"Property '{property_name_with_ref}' in schema '{parent_schema_name}' "
            f"has unresolvable $ref '{unresolvable_ref_path}'. Creating placeholder."
        )

        mock_logger.warning.assert_any_call(expected_log_message)

        # The result here is for "InvalidRef". Its property "invalid" would be an IRSchema from unresolved ref.
        self.assertIsNotNone(result.properties)
        if result.properties:
            # The property key remains "invalid". The IRSchema.name for this property will be sanitized "Invalid".
            invalid_prop_schema = result.properties.get(property_name_with_ref)  # Use original key
            self.assertIsNotNone(
                invalid_prop_schema, f"Property '{property_name_with_ref}' not found in {result.properties.keys()}"
            )
            if invalid_prop_schema:
                self.assertTrue(invalid_prop_schema._from_unresolved_ref)
                # Check that the IRSchema for the property itself is named correctly (sanitized prop_name)
                self.assertEqual(invalid_prop_schema.name, "Invalid")


if __name__ == "__main__":
    unittest.main()
