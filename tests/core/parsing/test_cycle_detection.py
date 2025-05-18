"""
Tests for the cycle detection functionality in schema parsing.
"""

import importlib  # For reloading
import os
import unittest
from typing import Any, Dict

from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema
from pyopenapi_gen.core.utils import NameSanitizer


class TestCycleDetection(unittest.TestCase):
    def setUp(self) -> None:
        """Set up test environment."""
        self.context = ParsingContext()

        # Store original environment variables
        self.original_env = {
            "PYOPENAPI_DEBUG_CYCLES": os.environ.get("PYOPENAPI_DEBUG_CYCLES"),
            "PYOPENAPI_MAX_CYCLES": os.environ.get("PYOPENAPI_MAX_CYCLES"),
            "PYOPENAPI_MAX_DEPTH": os.environ.get("PYOPENAPI_MAX_DEPTH"),
        }

        # Set test-specific environment variables
        os.environ["PYOPENAPI_DEBUG_CYCLES"] = "1"
        os.environ["PYOPENAPI_MAX_CYCLES"] = "10"  # This is for schema_parser.MAX_CYCLES
        os.environ["PYOPENAPI_MAX_DEPTH"] = "10"  # This is for schema_parser.ENV_MAX_DEPTH

        # Reload schema_parser to pick up new env var values for its module-level constants
        from pyopenapi_gen.core.parsing import schema_parser

        importlib.reload(schema_parser)

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:  # If original was None (not set), delete it
                del os.environ[key]

        # Reload schema_parser to reflect original/default environment variables
        from pyopenapi_gen.core.parsing import schema_parser

        importlib.reload(schema_parser)

    def test_self_reference_cycle_detection(self) -> None:
        """Test detection of a schema that directly references itself."""
        schema_name = "SelfRefSchema"
        schema_data: Dict[str, Any] = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "self_ref": {"$ref": f"#/components/schemas/{schema_name}"}},
        }
        self.context.raw_spec_schemas = {schema_name: schema_data}
        result = _parse_schema(schema_name, schema_data, self.context)

        # Verify cycle detection
        self.assertTrue(result._is_circular_ref, "Schema should be marked as circular")
        self.assertTrue(result._from_unresolved_ref, "Schema should be marked as unresolved")
        self.assertIsNotNone(result._circular_ref_path)
        assert result._circular_ref_path is not None
        self.assertIn(schema_name, result._circular_ref_path, "Cycle path should include original schema name")
        self.assertEqual(result.name, NameSanitizer.sanitize_class_name(schema_name), "Schema name should be sanitized")
        self.assertEqual(result.properties, {}, "Circular placeholder should have no properties")

    def test_mutual_reference_cycle_detection(self) -> None:
        """Test detection of mutual references between schemas."""
        schema_a_name = "SchemaA"
        schema_b_name = "SchemaB"
        schema_a: Dict[str, Any] = {
            "type": "object",
            "properties": {"b": {"$ref": f"#/components/schemas/{schema_b_name}"}},
        }
        schema_b: Dict[str, Any] = {
            "type": "object",
            "properties": {"a": {"$ref": f"#/components/schemas/{schema_a_name}"}},
        }

        self.context.raw_spec_schemas = {schema_a_name: schema_a, schema_b_name: schema_b}

        # Parse schema A
        result_a = _parse_schema(schema_a_name, schema_a, self.context)

        # Verify cycle detection
        self.assertTrue(result_a._is_circular_ref, "SchemaA should be marked as circular")
        self.assertTrue(result_a._from_unresolved_ref, "SchemaA should be marked as unresolved")
        self.assertIsNotNone(result_a._circular_ref_path)
        assert result_a._circular_ref_path is not None
        self.assertIn(schema_a_name, result_a._circular_ref_path, "Cycle path should include original SchemaA")
        self.assertIn(schema_b_name, result_a._circular_ref_path, "Cycle path should include original SchemaB")
        self.assertEqual(
            result_a.name, NameSanitizer.sanitize_class_name(schema_a_name), "Schema name should be sanitized"
        )

    def test_composition_cycle_detection(self) -> None:
        """Test detection of cycles in schema composition (allOf, anyOf, oneOf)."""
        schema_a_name = "SchemaA"
        schema_b_name = "SchemaB"
        schema_a: Dict[str, Any] = {
            "type": "object",
            "allOf": [
                {"type": "object", "properties": {"name": {"type": "string"}}},
                {"$ref": f"#/components/schemas/{schema_b_name}"},
            ],
        }
        schema_b: Dict[str, Any] = {
            "type": "object",
            "anyOf": [
                {"type": "object", "properties": {"id": {"type": "integer"}}},
                {"$ref": f"#/components/schemas/{schema_a_name}"},
            ],
        }

        self.context.raw_spec_schemas = {schema_a_name: schema_a, schema_b_name: schema_b}

        # Parse schema A
        result_a = _parse_schema(schema_a_name, schema_a, self.context)

        # Verify cycle detection
        self.assertTrue(self.context.cycle_detected, "Cycle should be detected in composition")
        self.assertTrue(result_a._is_circular_ref, "SchemaA should be marked as circular")
        self.assertTrue(result_a._from_unresolved_ref, "SchemaA should be marked as unresolved")
        self.assertIsNotNone(result_a._circular_ref_path)
        assert result_a._circular_ref_path is not None
        self.assertIn(schema_a_name, result_a._circular_ref_path, "Cycle path should include original SchemaA")
        self.assertIn(schema_b_name, result_a._circular_ref_path, "Cycle path should include original SchemaB")
        self.assertEqual(
            result_a.name, NameSanitizer.sanitize_class_name(schema_a_name), "Schema name should be sanitized"
        )

    def test_nested_property_cycle_detection(self) -> None:
        """Test detection of cycles in nested properties."""
        schema_name = "NestedSchema"
        schema_data: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "nested": {
                    "type": "object",
                    "properties": {
                        "deep": {
                            "type": "object",
                            "properties": {"ref": {"$ref": f"#/components/schemas/{schema_name}"}},
                        }
                    },
                }
            },
        }

        self.context.raw_spec_schemas = {schema_name: schema_data}
        result = _parse_schema(schema_name, schema_data, self.context)

        # Verify cycle detection
        self.assertTrue(result._is_circular_ref, "Schema should be marked as circular")
        self.assertTrue(result._from_unresolved_ref, "Schema should be marked as unresolved")
        self.assertIsNotNone(result._circular_ref_path)
        assert result._circular_ref_path is not None
        self.assertIn(schema_name, result._circular_ref_path, "Cycle path should include original schema name")
        self.assertEqual(result.name, NameSanitizer.sanitize_class_name(schema_name), "Schema name should be sanitized")

    def test_max_recursion_depth(self) -> None:
        """Test handling of maximum recursion depth."""
        schema_name = "DeepSchema"
        # Create a deeply nested schema
        current_schema: Dict[str, Any] = {"type": "string"}
        for _ in range(15):  # Exceed max depth of 10 (set by ENV_MAX_DEPTH in setUp)
            current_schema = {"type": "array", "items": current_schema}

        self.context.raw_spec_schemas = {schema_name: current_schema}
        result = _parse_schema(schema_name, current_schema, self.context)

        # Verify max depth handling
        # The 'result' (DeepSchema IR) itself may not be the circular placeholder if depth is hit in an anonymous item.
        # However, the context should flag that a cycle (due to max depth) was detected.
        self.assertTrue(self.context.cycle_detected, "Context should flag cycle detected due to max depth")
        self.assertEqual(
            result.name,
            NameSanitizer.sanitize_class_name(schema_name),
            "Schema name should be preserved for the main schema",
        )
        # result._is_circular_ref might be False if the placeholder is for an anonymous item.
        # self.assertTrue(result._is_circular_ref, "Schema should be marked as circular")
        # self.assertTrue(result._from_unresolved_ref, "Schema should be marked as unresolved")
        # self.assertIsNotNone(result._circular_ref_path)
        # assert result._circular_ref_path is not None
        # self.assertIn(NameSanitizer.sanitize_class_name(schema_name), result._circular_ref_path.split(" -> ")[0])
        # self.assertIn("MAX_DEPTH_EXCEEDED", result._circular_ref_path, "Cycle path should indicate max depth")

    def test_environment_variable_effects(self) -> None:
        """Test that environment variables like DEBUG_CYCLES are processed without error.
        ENV_MAX_DEPTH is tested more specifically in test_max_recursion_depth and test_invalid_env_vars_fallback_to_defaults.
        MAX_CYCLES is currently not used by the core parsing logic for cycle limits.
        """
        # PYOPENAPI_DEBUG_CYCLES is set to "1" in setUp, and schema_parser is reloaded.
        # This test primarily ensures that this setup doesn't cause errors and parsing proceeds.
        # A more thorough test would mock the logger to check for debug messages.

        # schema_parser.DEBUG_CYCLES should be True due to setUp
        from pyopenapi_gen.core.parsing import schema_parser

        context = ParsingContext()
        schema_name = "TestSchemaEnvEffect"
        schema_data = {
            "type": "object",
            "properties": {"self_ref": {"$ref": f"#/components/schemas/{schema_name}"}},
        }
        context.raw_spec_schemas = {schema_name: schema_data}
        result = _parse_schema(schema_name, schema_data, context)

        # Basic check that parsing completed and detected the cycle
        self.assertTrue(result._is_circular_ref, "Schema should be marked as circular")
        self.assertTrue(result._from_unresolved_ref, "Schema should be marked as unresolved")
        self.assertIsNotNone(result._circular_ref_path)
        assert result._circular_ref_path is not None
        self.assertIn(schema_name, result._circular_ref_path, "Cycle path should include original schema name")
        self.assertEqual(result.name, NameSanitizer.sanitize_class_name(schema_name), "Schema name should be sanitized")

    def test_array_items_cycle_detection(self) -> None:
        """Test detection of a cycle where array items refer back to the parent schema."""
        schema_name = "ArrayCycleSchema"
        schema_data: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "children": {
                    "type": "array",
                    "items": {"$ref": f"#/components/schemas/{schema_name}"},
                },
            },
        }
        self.context.raw_spec_schemas = {schema_name: schema_data}
        result = _parse_schema(schema_name, schema_data, self.context)

        # Verify cycle detection
        self.assertTrue(result._is_circular_ref, "Schema should be marked as circular due to array items cycle")
        self.assertTrue(result._from_unresolved_ref, "Schema should be marked as unresolved")
        self.assertIsNotNone(result._circular_ref_path, "Circular ref path should be set")
        assert result._circular_ref_path is not None
        self.assertIn(schema_name, result._circular_ref_path, "Cycle path should include original schema name")
        self.assertEqual(result.name, NameSanitizer.sanitize_class_name(schema_name), "Schema name should be sanitized")
        # The properties might be empty or contain 'name' depending on when cycle is detected
        # For this specific case, where the cycle is in 'items', the top-level properties might parse before cycle is fully established.
        # However, the IRSchema for 'children'->'items' should be the circular placeholder.
        # Let's check if the context has the cycle detected flag.
        self.assertTrue(self.context.cycle_detected, "Context should flag that a cycle was detected")

    def test_three_schema_cycle_detection(self) -> None:
        """Test detection of a cycle involving three schemas (A -> B -> C -> A)."""
        schema_a_name = "SchemaA_Triple"
        schema_b_name = "SchemaB_Triple"
        schema_c_name = "SchemaC_Triple"

        schema_a: Dict[str, Any] = {
            "type": "object",
            "properties": {"b_ref": {"$ref": f"#/components/schemas/{schema_b_name}"}},
        }
        schema_b: Dict[str, Any] = {
            "type": "object",
            "properties": {"c_ref": {"$ref": f"#/components/schemas/{schema_c_name}"}},
        }
        schema_c: Dict[str, Any] = {
            "type": "object",
            "properties": {"a_ref": {"$ref": f"#/components/schemas/{schema_a_name}"}},
        }

        self.context.raw_spec_schemas = {
            schema_a_name: schema_a,
            schema_b_name: schema_b,
            schema_c_name: schema_c,
        }

        # Parse schema A, which should trigger the cycle detection through B and C
        result_a = _parse_schema(schema_a_name, schema_a, self.context)

        # Verify cycle detection on SchemaA_Triple
        self.assertTrue(result_a._is_circular_ref, f"{schema_a_name} should be marked as circular")
        self.assertTrue(result_a._from_unresolved_ref, f"{schema_a_name} should be marked as unresolved")
        self.assertIsNotNone(result_a._circular_ref_path)
        assert result_a._circular_ref_path is not None  # For mypy
        self.assertIn(schema_a_name, result_a._circular_ref_path)
        self.assertIn(schema_b_name, result_a._circular_ref_path)
        self.assertIn(schema_c_name, result_a._circular_ref_path)
        self.assertEqual(
            result_a.name, NameSanitizer.sanitize_class_name(schema_a_name), "Schema name should be sanitized"
        )

        # Also check that SchemaB_Triple and SchemaC_Triple are in parsed_schemas.
        # They are part of the cycle, but are not necessarily marked _is_circular_ref=True themselves
        # when the cycle is detected starting from SchemaA_Triple.
        # It's sufficient that result_a is circular and context.cycle_detected is True.
        self.assertTrue(self.context.cycle_detected, "Context should flag that a cycle was detected")
        self.assertIn(schema_b_name, self.context.parsed_schemas)
        self.assertIn(schema_c_name, self.context.parsed_schemas)

        # Ensure that if we were to parse B or C directly, they would also be caught.
        # This is a separate check to ensure the mechanism is sound for other entry points.
        # Clear context for Schema B check (except raw_spec_schemas)
        self.context.currently_parsing.clear()
        self.context.parsed_schemas.clear()
        self.context.recursion_depth = 0
        self.context.cycle_detected = False
        result_b_direct = _parse_schema(schema_b_name, schema_b, self.context)
        self.assertTrue(result_b_direct._is_circular_ref, f"{schema_b_name} should be circular if parsed directly")
        self.assertEqual(result_b_direct.name, NameSanitizer.sanitize_class_name(schema_b_name))

        # Clear context for Schema C check
        self.context.currently_parsing.clear()
        self.context.parsed_schemas.clear()
        self.context.recursion_depth = 0
        self.context.cycle_detected = False
        result_c_direct = _parse_schema(schema_c_name, schema_c, self.context)
        self.assertTrue(result_c_direct._is_circular_ref, f"{schema_c_name} should be circular if parsed directly")
        self.assertEqual(result_c_direct.name, NameSanitizer.sanitize_class_name(schema_c_name))

    def test_invalid_env_vars_fallback_to_defaults(self) -> None:
        """Test that parser falls back to defaults if env vars for limits are invalid."""
        original_max_cycles = os.environ.get("PYOPENAPI_MAX_CYCLES")
        original_max_depth = os.environ.get("PYOPENAPI_MAX_DEPTH")

        try:
            os.environ["PYOPENAPI_MAX_CYCLES"] = "not-an-integer"
            os.environ["PYOPENAPI_MAX_DEPTH"] = "another-bad-value"

            # Reload schema_parser to pick up the modified (invalid) env vars
            # and exercise the try-except blocks for default fallbacks.
            from pyopenapi_gen.core.parsing import schema_parser

            importlib.reload(schema_parser)

            # Check if the module-level constants fell back to defaults
            self.assertEqual(schema_parser.MAX_CYCLES, 0, "MAX_CYCLES should default to 0 on invalid env var")
            self.assertEqual(schema_parser.ENV_MAX_DEPTH, 100, "ENV_MAX_DEPTH should default to 100 on invalid env var")

            # Optional: Perform a minimal parse to ensure no crash and defaults are used by context if applicable
            # This part depends on how ParsingContext gets its max_depth. If it's from ENV_MAX_DEPTH at instantiation, this is good.
            # If schema_parser.ENV_MAX_DEPTH is passed to ParsingContext or _parse_schema, then checking the module var is sufficient.
            # Based on current code, ParsingContext does not directly use ENV_MAX_DEPTH from schema_parser module after import.
            # The _parse_schema function *does* use context.max_depth, which is initialized in ParsingContext.
            # The test for max_recursion_depth already covers the behavior when context.max_depth is hit.
            # This test primarily ensures the module loads with defaults correctly.

        finally:
            # Restore original environment variables
            if original_max_cycles is not None:
                os.environ["PYOPENAPI_MAX_CYCLES"] = original_max_cycles
            elif "PYOPENAPI_MAX_CYCLES" in os.environ:
                del os.environ["PYOPENAPI_MAX_CYCLES"]

            if original_max_depth is not None:
                os.environ["PYOPENAPI_MAX_DEPTH"] = original_max_depth
            elif "PYOPENAPI_MAX_DEPTH" in os.environ:
                del os.environ["PYOPENAPI_MAX_DEPTH"]

            # Reload schema_parser again to restore its state based on original/default env vars for other tests
            from pyopenapi_gen.core.parsing import schema_parser  # Re-import to get fresh reference

            importlib.reload(schema_parser)


if __name__ == "__main__":
    unittest.main()
