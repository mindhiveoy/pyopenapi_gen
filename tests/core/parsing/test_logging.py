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
        os.environ["PYOPENAPI_DEBUG_CYCLES"] = "1"
        os.environ["PYOPENAPI_MAX_DEPTH"] = "2"

        # Reload schema_parser to ensure it picks up the patched environment variables
        # for its module-level constants like ENV_MAX_DEPTH and DEBUG_CYCLES.
        import importlib

        import pyopenapi_gen.core.parsing.schema_parser

        importlib.reload(pyopenapi_gen.core.parsing.schema_parser)

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Restore original environment variables
        if self.original_debug_cycles is not None:
            os.environ["PYOPENAPI_DEBUG_CYCLES"] = self.original_debug_cycles
        else:
            del os.environ["PYOPENAPI_DEBUG_CYCLES"]

        if self.original_max_depth is not None:
            os.environ["PYOPENAPI_MAX_DEPTH"] = self.original_max_depth
        else:
            del os.environ["PYOPENAPI_MAX_DEPTH"]

    @patch("pyopenapi_gen.core.parsing.cycle_helpers.logger")
    def test_cycle_detection_logging(self, mock_logger: MagicMock) -> None:
        """Test that cycle detection is logged when debug is enabled."""
        context = ParsingContext()

        # Create a self-referential schema
        schema: Dict[str, Any] = {"type": "object", "properties": {"self": {"$ref": "#/components/schemas/SelfRef"}}}
        context.raw_spec_schemas["SelfRef"] = schema

        # Parse the schema
        result = _parse_schema("SelfRef", schema, context)

        # Verify logging from cycle_helpers.logger
        expected_log = "Cycle detected via enter_schema for 'SelfRef'. Path: SelfRef -> SelfRef. Returning placeholder for root 'SelfRef'."
        mock_logger.warning.assert_any_call(expected_log)
        self.assertTrue(result._is_circular_ref)
        self.assertTrue(result._from_unresolved_ref)

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

        # Print for debugging
        print(f"DEBUG: Expected log for max_depth: {expected_log}")
        print(f"DEBUG: Actual cycle_helpers.logger.warning calls: {mock_logger.warning.call_args_list}")

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

    @patch("pyopenapi_gen.core.parsing.cycle_helpers.logger")
    def test_cycle_path_logging(self, mock_logger: MagicMock) -> None:
        """Test that cycle paths are logged correctly."""
        # Cycle detection warning comes from cycle_helpers.logger
        context = ParsingContext()

        # Create a mutual reference cycle
        schema_a: Dict[str, Any] = {"type": "object", "properties": {"b": {"$ref": "#/components/schemas/SchemaB"}}}
        schema_b: Dict[str, Any] = {"type": "object", "properties": {"a": {"$ref": "#/components/schemas/SchemaA"}}}
        context.raw_spec_schemas["SchemaA"] = schema_a
        context.raw_spec_schemas["SchemaB"] = schema_b

        # Parse the schemas
        # Parsing A will parse B, which will attempt to re-parse A, triggering cycle detection for A.
        # Then, when _parse_schema("SchemaB", ...) is called, it might re-evaluate.
        # Let's trace: _parse_schema("SchemaA") -> enters A -> sees ref to B -> _parse_schema("SchemaB")
        # -> enters B -> sees ref to A -> _parse_schema("SchemaA" (for B.a property))
        #    -> enter_schema("SchemaA") -> cycle (A->B->A) -> _handle_cycle_detection for original_name="SchemaA"
        # So, placeholder for A is made. Call for B.a returns this placeholder.
        # _parse_schema("SchemaB") finishes, returns IR for B (with ref to placeholder A).
        # _parse_schema("SchemaA") finishes, returns IR for A (with ref to B).
        # The test calls _parse_schema("SchemaA", ...) then _parse_schema("SchemaB", ...)
        # So the second call _parse_schema("SchemaB") might hit a cycle if A already resolved B.

        _ = _parse_schema("SchemaA", schema_a, context)  # Parse A first, this will parse B and detect A->B->A cycle.
        # At this point, context.parsed_schemas will have placeholders or resolved schemas.
        # context.cycle_detected will be True.

        # When we parse B *again* as a top-level call (as per test structure):
        # _parse_schema("SchemaB", schema_b, context)
        # -> enter_schema("SchemaB") - might be okay if not currently_parsing SchemaB from this top stack
        # -> ref to "SchemaA". SchemaA is already in context.parsed_schemas (likely a cycle placeholder itself).
        # This flow depends on yielding logic. If SchemaA yields its placeholder, then SchemaB is built.
        # The cycle log we are checking for is when the cycle is *first* detected and _handle_cycle_detection is called.
        # That happens during the first _parse_schema("SchemaA") call, when B.a tries to parse A again.
        # The log would be for original_name="SchemaA", path="SchemaA -> SchemaB -> SchemaA".

        # To test the log as specified "Cycle detected ... for 'SchemaB' ... Path: SchemaA -> SchemaB -> SchemaA ... root 'SchemaB'"
        # This implies _handle_cycle_detection was called with original_name='SchemaB' and path='SchemaA -> SchemaB -> SchemaA'.
        # This happens if stack is [SchemaA], then we enter B, stack [SchemaA, SchemaB], then B refs A, stack [SchemaA, SchemaB, A].
        # And then A refs B, enter B. Cycle: B -> A -> B. original_name=B.
        # Let's reset context for a clean trace for this specific log expectation.
        context.reset_for_new_parse()
        context.raw_spec_schemas["SchemaA"] = schema_a
        context.raw_spec_schemas["SchemaB"] = schema_b

        # If we parse B, and B refers to A, and A refers back to B:
        # _parse_schema("SchemaB") -> stack [SchemaB]
        #   prop a: $ref SchemaA -> _parse_schema("SchemaA") -> stack [SchemaB, SchemaA]
        #     prop b: $ref SchemaB -> _parse_schema("SchemaB" for A.b) -> enter_schema("SchemaB") -> CYCLE!
        #       Path: SchemaB -> SchemaA -> SchemaB. original_name for _handle_cycle_detection is "SchemaB".
        result = _parse_schema("SchemaB", schema_b, context)

        # Verify logging
        expected_log = "Cycle detected via enter_schema for 'SchemaB'. Path: SchemaB -> SchemaA -> SchemaB. Returning placeholder for root 'SchemaB'."
        mock_logger.warning.assert_any_call(expected_log)
        self.assertTrue(result._is_circular_ref)
        self.assertTrue(result._from_unresolved_ref)

    @patch("pyopenapi_gen.core.parsing.schema_parser.logger")
    @patch.dict(os.environ, {"PYOPENAPI_DEBUG_CYCLES": "0"})  # Patch os.environ for this test
    def test_debug_cycles_disabled(self, mock_schema_logger: MagicMock) -> None:  # Renamed mock_logger
        """Test that debug logs are not emitted when PYOPENAPI_DEBUG_CYCLES is '0'."""
        # Reload schema_parser to re-evaluate DEBUG_CYCLES with the patched environment
        import importlib  # Add import

        import pyopenapi_gen.core.parsing.schema_parser  # Import module itself

        importlib.reload(pyopenapi_gen.core.parsing.schema_parser)

        context = ParsingContext(raw_spec_schemas={})  # Initial context, removed openapi_version
        _parse_schema("SimpleSchema", {"type": "object", "properties": {"name": {"type": "string"}}}, context)
        mock_schema_logger.debug.assert_not_called()

        # Test with a cycle to ensure debug logs related to cycle yielding are also off
        mock_schema_logger.reset_mock()
        context.reset_for_new_parse()
        # Provide raw_spec_schemas to the context for the $ref to resolve
        context.raw_spec_schemas = {
            "SelfRef": {"type": "object", "properties": {"next": {"$ref": "#/components/schemas/SelfRef"}}}
        }
        _parse_schema(
            "SelfRef",
            {"$ref": "#/components/schemas/SelfRef"},
            context,  # Use the context instance
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

        # Print for debugging
        print(f"DEBUG: Expected log for invalid_ref (schema_parser): {expected_log_message}")
        print(f"DEBUG: Actual schema_parser.logger.warning calls: {mock_logger.warning.call_args_list}")

        # Verify logging
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
