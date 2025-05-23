"""
Integration tests comparing original vs enhanced cycle detection.

These tests demonstrate the improvements in the enhanced cycle detection
system, particularly how it marks ALL schemas in a cycle rather than just
the re-entrant schema.
"""

import unittest
import pytest
from typing import Dict, Any, cast

from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema
# from pyopenapi_gen.core.parsing.enhanced_cycle_detection import (
#     integrate_enhanced_cycle_detection,
#     CycleHandlingStrategy,
#     CycleType
# )


class TestCycleDetectionIntegration(unittest.TestCase):
    """Integration tests comparing original and enhanced cycle detection."""
    
    def setUp(self) -> None:
        """Set up test environment."""
        self.original_context = ParsingContext()
        self.enhanced_context = ParsingContext()
        # integrate_enhanced_cycle_detection(
        #     self.enhanced_context, 
        #     CycleHandlingStrategy.FORWARD_REFERENCE
        # )
        
    @pytest.mark.skip(reason="Enhanced cycle detection module not implemented - replaced by unified system")
    def test_indirect_cycle_all_schemas_marked(self) -> None:
        """
        Test that enhanced detection marks ALL schemas in an indirect cycle.
        
        This addresses the limitation shown in the original test:
        test_indirect_cycle where only the re-entrant schema was marked.
        """
        # Create a manual cycle scenario to demonstrate the enhancement
        schema_a = IRSchema(name="SchemaA", type="object")
        schema_b = IRSchema(name="SchemaB", type="object")
        
        # Simulate parsing that would detect a cycle A -> B -> A
        detector = self.enhanced_context.enhanced_cycle_detector
        
        # Manually create the cycle path to simulate what would happen during parsing
        detector.enter_schema("SchemaA")
        detector.enter_schema("SchemaB")
        is_cycle, cycle_info = detector.enter_schema("SchemaA")  # This creates the cycle
        
        self.assertTrue(is_cycle, "Should detect the A -> B -> A cycle")
        self.assertIsNotNone(cycle_info)
        
        if cycle_info:
            self.assertEqual(cycle_info.cycle_type, CycleType.MUTUAL_REFERENCE)
            self.assertEqual(set(cycle_info.schemas_involved), {"SchemaA", "SchemaB"})
        
        # Now mark all schemas in cycles (post-processing step)
        parsed_schemas = {
            "SchemaA": schema_a,
            "SchemaB": schema_b
        }
        detector.mark_all_schemas_in_cycles(parsed_schemas)
        
        # With enhanced detection, BOTH schemas should be marked as circular
        self.assertTrue(schema_a._is_circular_ref, 
                       "SchemaA should be marked as circular with enhanced detection")
        self.assertTrue(schema_b._is_circular_ref, 
                       "SchemaB should be marked as circular with enhanced detection")
        
        # Both should have cycle path information
        self.assertIsNotNone(schema_a._circular_ref_path)
        self.assertIsNotNone(schema_b._circular_ref_path)
        
        # Both should have enhanced cycle metadata
        self.assertTrue(hasattr(schema_a, '_cycle_info'))
        self.assertTrue(hasattr(schema_b, '_cycle_info'))
        
    @pytest.mark.skip(reason="Enhanced cycle detection module not implemented - replaced by unified system")
    def test_three_way_cycle_all_schemas_marked(self) -> None:
        """Test that all schemas in a three-way cycle are marked."""
        # Create manual schemas for the test
        schema_a = IRSchema(name="ThreeWayA", type="object")
        schema_b = IRSchema(name="ThreeWayB", type="object")
        schema_c = IRSchema(name="ThreeWayC", type="object")
        
        # Simulate parsing that would detect a cycle A -> B -> C -> A
        detector = self.enhanced_context.enhanced_cycle_detector
        
        # Manually create the cycle path
        detector.enter_schema("ThreeWayA")
        detector.enter_schema("ThreeWayB")
        detector.enter_schema("ThreeWayC")
        is_cycle, cycle_info = detector.enter_schema("ThreeWayA")  # This creates the cycle
        
        self.assertTrue(is_cycle, "Should detect the A -> B -> C -> A cycle")
        self.assertIsNotNone(cycle_info)
        
        if cycle_info:
            self.assertEqual(cycle_info.cycle_type, CycleType.INDIRECT_CYCLE)
            self.assertEqual(set(cycle_info.schemas_involved), {"ThreeWayA", "ThreeWayB", "ThreeWayC"})
        
        # Mark all schemas in cycles
        parsed_schemas = {
            "ThreeWayA": schema_a,
            "ThreeWayB": schema_b,
            "ThreeWayC": schema_c
        }
        detector.mark_all_schemas_in_cycles(parsed_schemas)
        
        # ALL three schemas should be marked as circular
        for schema_name, result in parsed_schemas.items():
            self.assertTrue(result._is_circular_ref, 
                           f"{schema_name} should be marked as circular")
            self.assertIsNotNone(result._circular_ref_path)
            self.assertTrue(hasattr(result, '_cycle_info'))
            
    @pytest.mark.skip(reason="Enhanced cycle detection module not implemented - replaced by unified system")
    def test_cycle_analysis_provides_comprehensive_info(self) -> None:
        """Test that cycle analysis provides comprehensive information."""
        # Create multiple cycles to test analysis
        
        # Cycle 1: Self-reference
        self.enhanced_context.raw_spec_schemas["SelfRef"] = {
            "properties": {"self": {"$ref": "#/components/schemas/SelfRef"}}
        }
        
        # Cycle 2: Mutual reference  
        self.enhanced_context.raw_spec_schemas.update({
            "MutualA": {"properties": {"b": {"$ref": "#/components/schemas/MutualB"}}},
            "MutualB": {"properties": {"a": {"$ref": "#/components/schemas/MutualA"}}}
        })
        
        # Parse schemas to trigger cycle detection
        _parse_schema("SelfRef", self.enhanced_context.raw_spec_schemas["SelfRef"], 
                     self.enhanced_context, allow_self_reference=False)
        _parse_schema("MutualA", self.enhanced_context.raw_spec_schemas["MutualA"], 
                     self.enhanced_context, allow_self_reference=False)
        _parse_schema("MutualB", self.enhanced_context.raw_spec_schemas["MutualB"], 
                     self.enhanced_context, allow_self_reference=False)
        
        # Get analysis
        analysis = self.enhanced_context.enhanced_cycle_detector.get_cycle_analysis()
        
        # Verify comprehensive analysis
        self.assertTrue(analysis.has_cycles)
        self.assertGreaterEqual(len(analysis.cycles), 1)  # At least one cycle detected
        self.assertGreater(analysis.total_schemas_in_cycles, 0)
        self.assertGreater(len(analysis.unique_cycle_schemas), 0)
        self.assertGreater(analysis.cycle_complexity_score, 0)
        
        # Verify cycle type detection
        cycle_types = [cycle.cycle_type.value for cycle in analysis.cycles]
        self.assertTrue(any("reference" in cycle_type for cycle_type in cycle_types))
        
    @pytest.mark.skip(reason="Enhanced cycle detection module not implemented - replaced by unified system")
    def test_enhanced_vs_original_behavior_comparison(self) -> None:
        """
        Direct comparison showing improvement over original behavior.
        
        This test demonstrates the key improvement: enhanced detection
        can mark ALL schemas in a cycle, not just the re-entrant one.
        """
        # Create schemas to demonstrate the improvement
        schema_a = IRSchema(name="ComparisonA", type="object")
        schema_b = IRSchema(name="ComparisonB", type="object")
        
        # Use enhanced detector to simulate finding a mutual cycle
        detector = self.enhanced_context.enhanced_cycle_detector
        
        detector.enter_schema("ComparisonA")
        detector.enter_schema("ComparisonB")
        is_cycle, cycle_info = detector.enter_schema("ComparisonA")
        
        self.assertTrue(is_cycle, "Should detect mutual reference cycle")
        
        # The original system would only mark the re-entrant schema,
        # but the enhanced system can mark ALL schemas in the cycle
        parsed_schemas = {
            "ComparisonA": schema_a,
            "ComparisonB": schema_b
        }
        detector.mark_all_schemas_in_cycles(parsed_schemas)
        
        # Enhanced behavior: ALL schemas in cycle are marked
        self.assertTrue(schema_a._is_circular_ref, 
                       "Enhanced: SchemaA should be marked as circular")
        self.assertTrue(schema_b._is_circular_ref, 
                       "Enhanced: SchemaB should be marked as circular")
        
        # Enhanced system provides more information
        self.assertTrue(hasattr(schema_a, '_cycle_info'))
        self.assertTrue(hasattr(schema_b, '_cycle_info'))
        self.assertIsNotNone(schema_a._circular_ref_path)
        self.assertIsNotNone(schema_b._circular_ref_path)
        
    @pytest.mark.skip(reason="Enhanced cycle detection module not implemented - replaced by unified system")
    def test_enhanced_detection_maintains_compatibility(self) -> None:
        """Test that enhanced detection maintains compatibility with existing code."""
        # The enhanced detection should still work with the existing entry/exit pattern
        is_cycle, cycle_path = self.enhanced_context.enter_schema("TestSchema")
        self.assertFalse(is_cycle)
        
        # Second entry should detect cycle
        is_cycle, cycle_path = self.enhanced_context.enter_schema("TestSchema")
        self.assertTrue(is_cycle)
        self.assertIsNotNone(cycle_path)
        self.assertIsInstance(cycle_path, str)
        
        # Exit should work normally
        self.enhanced_context.exit_schema("TestSchema")
        self.enhanced_context.exit_schema("TestSchema")
        
        # Enhanced features should be available
        self.assertTrue(hasattr(self.enhanced_context, 'enhanced_cycle_detector'))
        analysis = self.enhanced_context.enhanced_cycle_detector.get_cycle_analysis()
        self.assertTrue(analysis.has_cycles)
        
    @pytest.mark.skip(reason="Enhanced cycle detection module not implemented - replaced by unified system")
    def test_performance_with_deep_cycles(self) -> None:
        """Test performance characteristics with deep cycle chains."""
        import time
        
        # Create a deep cycle: A0 -> A1 -> A2 -> ... -> A9 -> A0
        cycle_depth = 10
        schemas = {}
        
        for i in range(cycle_depth):
            next_i = (i + 1) % cycle_depth
            schema_name = f"DeepCycle{i}"
            next_schema_name = f"DeepCycle{next_i}"
            
            schemas[schema_name] = {
                "properties": {
                    "next": {"$ref": f"#/components/schemas/{next_schema_name}"}
                }
            }
            
        self.enhanced_context.raw_spec_schemas.update(schemas)
        
        # Time the parsing with cycle detection
        start_time = time.time()
        
        for i in range(cycle_depth):
            schema_name = f"DeepCycle{i}"
            _parse_schema(schema_name, schemas[schema_name], 
                         self.enhanced_context, allow_self_reference=False)
            
        end_time = time.time()
        parsing_time = end_time - start_time
        
        # Verify cycle was detected
        analysis = self.enhanced_context.enhanced_cycle_detector.get_cycle_analysis()
        self.assertTrue(analysis.has_cycles)
        
        # Performance should be reasonable (less than 1 second for this test)
        self.assertLess(parsing_time, 1.0, 
                       f"Parsing took {parsing_time:.3f}s, should be under 1s")
        
        # Verify all schemas can be marked
        parsed_schemas = {name: self.enhanced_context.parsed_schemas.get(name) 
                         for name in schemas.keys() 
                         if self.enhanced_context.parsed_schemas.get(name)}
        
        self.enhanced_context.enhanced_cycle_detector.mark_all_schemas_in_cycles(parsed_schemas)
        
        # Most schemas should be marked as circular
        circular_count = sum(1 for schema in parsed_schemas.values() 
                           if schema and schema._is_circular_ref)
        self.assertGreater(circular_count, 0, "At least some schemas should be marked as circular")


if __name__ == "__main__":
    unittest.main()