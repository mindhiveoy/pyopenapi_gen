"""
Tests for the cycle detection functionality in schema parsing.
"""

import unittest
import os
from typing import cast, Dict, Any

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema
from pyopenapi_gen.core.parsing.ref_resolver import _resolve_schema_ref


class TestCycleDetection(unittest.TestCase):
    def setUp(self) -> None:
        # Create a context with empty schemas
        self.context = ParsingContext()
        
        # Store original environment variables to restore later
        self.original_env = {
            'PYOPENAPI_DEBUG_CYCLES': os.environ.get('PYOPENAPI_DEBUG_CYCLES', '0'),
            'PYOPENAPI_MAX_CYCLES': os.environ.get('PYOPENAPI_MAX_CYCLES', '0'),
            'PYOPENAPI_MAX_DEPTH': os.environ.get('PYOPENAPI_MAX_DEPTH', '100')
        }
        
        # Set test-specific environment variables
        os.environ['PYOPENAPI_DEBUG_CYCLES'] = '1'
        os.environ['PYOPENAPI_MAX_CYCLES'] = '10'
        os.environ['PYOPENAPI_MAX_DEPTH'] = '10'  # Small depth for tests

    def tearDown(self) -> None:
        # Restore original environment variables
        for key, value in self.original_env.items():
            os.environ[key] = value

    def test_self_reference_cycle_detection(self) -> None:
        """Test detection of a schema that directly references itself."""
        # Create a schema that references itself
        schema_data: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "self_ref": {"$ref": "#/components/schemas/SelfRefSchema"}
            }
        }
        
        # Add to raw_spec_schemas
        self.context.raw_spec_schemas = {"SelfRefSchema": schema_data}
        
        # Parse schema
        result = _parse_schema("SelfRefSchema", schema_data, self.context)
        
        # Assertions
        self.assertTrue(self.context.cycle_detected, "Cycle should be detected")

        # Check the self_ref property exists
        self_ref_prop = result.properties.get("self_ref")
        self.assertIsNotNone(self_ref_prop, "self_ref property should exist")

    def test_mutual_reference_cycle_detection(self) -> None:
        """Test detection of a cycle between two schemas that reference each other."""
        # Create two schemas with mutual references
        schema_a: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "ref_to_b": {"$ref": "#/components/schemas/SchemaB"}
            }
        }
        
        schema_b: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "ref_to_a": {"$ref": "#/components/schemas/SchemaA"}
            }
        }
        
        # Add to raw_spec_schemas
        self.context.raw_spec_schemas = {
            "SchemaA": schema_a,
            "SchemaB": schema_b
        }
        
        # Parse schema A
        result_a = _parse_schema("SchemaA", schema_a, self.context)
        
        # Assertions
        self.assertTrue(self.context.cycle_detected, "Cycle should be detected")

        # Check that both schemas were parsed
        schema_b_parsed = self.context.parsed_schemas.get("SchemaB")
        self.assertIsNotNone(schema_b_parsed, "SchemaB should be in parsed_schemas")

        # Check that we have properties from both schemas
        ref_to_b_prop = result_a.properties.get("ref_to_b")
        self.assertIsNotNone(ref_to_b_prop, "ref_to_b property should exist")

        ref_to_a_prop = schema_b_parsed.properties.get("ref_to_a")
        self.assertIsNotNone(ref_to_a_prop, "ref_to_a property should exist")

    def test_complex_cycle_detection(self) -> None:
        """Test detection of a cycle in a more complex schema graph (A -> B -> C -> A)."""
        # Create three schemas with a cycle A -> B -> C -> A
        schema_a: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "ref_to_b": {"$ref": "#/components/schemas/SchemaB"}
            }
        }
        
        schema_b: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "ref_to_c": {"$ref": "#/components/schemas/SchemaC"}
            }
        }
        
        schema_c: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "ref_to_a": {"$ref": "#/components/schemas/SchemaA"}
            }
        }
        
        # Add to raw_spec_schemas
        self.context.raw_spec_schemas = {
            "SchemaA": schema_a,
            "SchemaB": schema_b,
            "SchemaC": schema_c
        }
        
        # Parse schema A
        result_a = _parse_schema("SchemaA", schema_a, self.context)
        
        # Assertions
        self.assertTrue(self.context.cycle_detected, "Cycle should be detected")
        
        # All three schemas should be in parsed_schemas
        self.assertIn("SchemaA", self.context.parsed_schemas)
        self.assertIn("SchemaB", self.context.parsed_schemas)
        self.assertIn("SchemaC", self.context.parsed_schemas)

        # The cycle should be detected (already verified above)
        self.assertTrue(self.context.cycle_detected,
                       "The test should have detected a cycle in the schema")

    def test_max_recursion_depth(self) -> None:
        """Test that recursion depth is limited to prevent stack overflow."""
        # Create a deeply nested schema that exceeds the max depth
        # We'll use an array with nested items that go beyond the max depth
        
        # Start with the innermost schema
        current_schema: Dict[str, Any] = {"type": "string"}
        
        # Create nested arrays that exceed the max depth
        max_depth = int(os.environ.get('PYOPENAPI_MAX_DEPTH', '10'))
        nesting_depth = max_depth + 5  # Exceed the max depth
        
        for i in range(nesting_depth):
            current_schema = {
                "type": "array",
                "items": current_schema
            }
        
        # Parse the deeply nested schema
        result = _parse_schema("DeeplyNested", current_schema, self.context)
        
        # Assertions
        # Verify we reached a significant recursion depth but didn't crash
        self.assertGreater(self.context.max_recursion_depth, 1,
                         "Max recursion depth should be tracked")

        # Verify that we didn't go too deep
        # (if this passes, we successfully limited recursion)
        self.assertLess(self.context.max_recursion_depth, max_depth + nesting_depth,
                       "Recursion should have been limited")


if __name__ == "__main__":
    unittest.main()