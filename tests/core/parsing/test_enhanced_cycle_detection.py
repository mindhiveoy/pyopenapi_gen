"""
Tests for enhanced circular reference detection system.

These tests verify that the enhanced cycle detection correctly identifies
and handles all schemas involved in cycles, not just the re-entrant schema.
"""

import unittest
from typing import Dict, Any

from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.enhanced_cycle_detection import (
    EnhancedCycleDetector,
    CycleType,
    CycleHandlingStrategy,
    integrate_enhanced_cycle_detection
)


class TestEnhancedCycleDetection(unittest.TestCase):
    """Test cases for enhanced cycle detection functionality."""
    
    def setUp(self) -> None:
        """Set up test environment."""
        self.detector = EnhancedCycleDetector(CycleHandlingStrategy.FORWARD_REFERENCE)
        self.parsed_schemas: Dict[str, IRSchema] = {}
        
    def test_direct_self_reference_detection(self) -> None:
        """Test detection of direct self-reference (A -> A)."""
        # Simulate parsing SchemaA that references itself
        is_cycle, cycle_info = self.detector.enter_schema("SchemaA")
        self.assertFalse(is_cycle, "First entry should not detect cycle")
        
        # Now SchemaA tries to reference itself again
        is_cycle, cycle_info = self.detector.enter_schema("SchemaA")
        self.assertTrue(is_cycle, "Second entry should detect cycle")
        self.assertIsNotNone(cycle_info)
        
        if cycle_info:
            self.assertEqual(cycle_info.cycle_type, CycleType.DIRECT_SELF_REFERENCE)
            self.assertEqual(cycle_info.schemas_involved, ["SchemaA"])
            self.assertEqual(cycle_info.entry_point, "SchemaA")
            self.assertEqual(cycle_info.reentry_point, "SchemaA")
            self.assertEqual(cycle_info.cycle_path, "SchemaA -> SchemaA")
            
    def test_mutual_reference_detection(self) -> None:
        """Test detection of mutual reference (A -> B -> A)."""
        # Start parsing SchemaA
        is_cycle, _ = self.detector.enter_schema("SchemaA")
        self.assertFalse(is_cycle)
        
        # SchemaA references SchemaB
        is_cycle, _ = self.detector.enter_schema("SchemaB")
        self.assertFalse(is_cycle)
        
        # SchemaB references SchemaA (cycle!)
        is_cycle, cycle_info = self.detector.enter_schema("SchemaA")
        self.assertTrue(is_cycle)
        self.assertIsNotNone(cycle_info)
        
        if cycle_info:
            self.assertEqual(cycle_info.cycle_type, CycleType.MUTUAL_REFERENCE)
            self.assertEqual(set(cycle_info.schemas_involved), {"SchemaA", "SchemaB"})
            self.assertEqual(cycle_info.entry_point, "SchemaA")
            self.assertEqual(cycle_info.reentry_point, "SchemaA")
            self.assertEqual(cycle_info.cycle_path, "SchemaA -> SchemaB -> SchemaA")
            
    def test_indirect_cycle_detection(self) -> None:
        """Test detection of indirect cycle (A -> B -> C -> A)."""
        # Build up the cycle step by step
        schemas = ["SchemaA", "SchemaB", "SchemaC"]
        
        for schema in schemas:
            is_cycle, _ = self.detector.enter_schema(schema)
            self.assertFalse(is_cycle, f"Should not detect cycle at {schema} yet")
            
        # Now close the loop: SchemaC -> SchemaA
        is_cycle, cycle_info = self.detector.enter_schema("SchemaA")
        self.assertTrue(is_cycle)
        self.assertIsNotNone(cycle_info)
        
        if cycle_info:
            self.assertEqual(cycle_info.cycle_type, CycleType.INDIRECT_CYCLE)
            self.assertEqual(set(cycle_info.schemas_involved), {"SchemaA", "SchemaB", "SchemaC"})
            self.assertEqual(cycle_info.entry_point, "SchemaA")
            self.assertEqual(cycle_info.reentry_point, "SchemaA")
            
    def test_complex_cycle_detection(self) -> None:
        """Test detection of complex cycle with many schemas."""
        # Create a cycle with 6 schemas (considered complex)
        schemas = [f"Schema{i}" for i in range(6)]
        
        for schema in schemas:
            is_cycle, _ = self.detector.enter_schema(schema)
            self.assertFalse(is_cycle)
            
        # Close the loop
        is_cycle, cycle_info = self.detector.enter_schema(schemas[0])
        self.assertTrue(is_cycle)
        self.assertIsNotNone(cycle_info)
        
        if cycle_info:
            self.assertEqual(cycle_info.cycle_type, CycleType.COMPLEX_CYCLE)
            self.assertEqual(len(cycle_info.schemas_involved), 6)
            
    def test_multiple_cycles_detection(self) -> None:
        """Test detection of multiple separate cycles."""
        # First cycle: A -> B -> A
        self.detector.enter_schema("SchemaA")
        self.detector.enter_schema("SchemaB")
        is_cycle1, cycle_info1 = self.detector.enter_schema("SchemaA")
        self.assertTrue(is_cycle1)
        
        # Reset for second cycle
        self.detector.exit_schema("SchemaA")
        self.detector.exit_schema("SchemaB")
        self.detector.exit_schema("SchemaA")
        
        # Second cycle: C -> D -> C
        self.detector.enter_schema("SchemaC")
        self.detector.enter_schema("SchemaD")
        is_cycle2, cycle_info2 = self.detector.enter_schema("SchemaC")
        self.assertTrue(is_cycle2)
        
        # Verify both cycles were detected
        self.assertEqual(len(self.detector.detected_cycles), 2)
        
        cycle_paths = [cycle.cycle_path for cycle in self.detector.detected_cycles]
        self.assertIn("SchemaA -> SchemaB -> SchemaA", cycle_paths)
        self.assertIn("SchemaC -> SchemaD -> SchemaC", cycle_paths)
        
    def test_mark_all_schemas_in_cycles(self) -> None:
        """Test that all schemas in cycles are properly marked."""
        # Create schemas
        self.parsed_schemas = {
            "SchemaA": IRSchema(name="SchemaA", type="object"),
            "SchemaB": IRSchema(name="SchemaB", type="object"),
            "SchemaC": IRSchema(name="SchemaC", type="object"),
        }
        
        # Simulate detecting a cycle A -> B -> C -> A
        self.detector.enter_schema("SchemaA")
        self.detector.enter_schema("SchemaB")
        self.detector.enter_schema("SchemaC")
        is_cycle, cycle_info = self.detector.enter_schema("SchemaA")
        self.assertTrue(is_cycle)
        
        # Mark all schemas in cycles
        self.detector.mark_all_schemas_in_cycles(self.parsed_schemas)
        
        # Verify all schemas are marked as circular
        for schema_name in ["SchemaA", "SchemaB", "SchemaC"]:
            schema = self.parsed_schemas[schema_name]
            self.assertTrue(schema._is_circular_ref, f"{schema_name} should be marked as circular")
            self.assertIsNotNone(schema._circular_ref_path)
            self.assertTrue(schema._from_unresolved_ref)
            
            # Check enhanced cycle metadata
            self.assertTrue(hasattr(schema, '_cycle_info'))
            self.assertIsInstance(schema._cycle_info, list)
            self.assertGreater(len(schema._cycle_info), 0)
            
    def test_self_reference_strategy_allow(self) -> None:
        """Test that self-reference strategy allows direct self-references."""
        detector = EnhancedCycleDetector(CycleHandlingStrategy.ALLOW_SELF_REFERENCE)
        
        # Simulate self-reference
        detector.enter_schema("SelfRefSchema")
        is_cycle, cycle_info = detector.enter_schema("SelfRefSchema")
        self.assertTrue(is_cycle)
        
        if cycle_info:
            should_allow = detector.should_allow_cycle(cycle_info)
            self.assertTrue(should_allow, "Self-reference should be allowed")
            
    def test_error_all_cycles_strategy(self) -> None:
        """Test that error strategy treats all cycles as errors."""
        detector = EnhancedCycleDetector(CycleHandlingStrategy.ERROR_ALL_CYCLES)
        
        # Test self-reference
        detector.enter_schema("SelfRefSchema")
        is_cycle, cycle_info = detector.enter_schema("SelfRefSchema")
        self.assertTrue(is_cycle)
        
        if cycle_info:
            should_allow = detector.should_allow_cycle(cycle_info)
            self.assertFalse(should_allow, "No cycles should be allowed")
            
    def test_cycle_analysis_result(self) -> None:
        """Test comprehensive cycle analysis functionality."""
        # Create multiple cycles
        # Cycle 1: A -> A (self-reference)
        self.detector.enter_schema("SchemaA")
        self.detector.enter_schema("SchemaA")
        self.detector.exit_schema("SchemaA")
        self.detector.exit_schema("SchemaA")
        
        # Cycle 2: B -> C -> B (mutual reference)
        self.detector.enter_schema("SchemaB")
        self.detector.enter_schema("SchemaC")
        self.detector.enter_schema("SchemaB")
        
        # Get analysis
        analysis = self.detector.get_cycle_analysis()
        
        self.assertTrue(analysis.has_cycles)
        self.assertEqual(len(analysis.cycles), 2)
        self.assertGreaterEqual(analysis.total_schemas_in_cycles, 2)
        self.assertIn("SchemaA", analysis.unique_cycle_schemas)
        self.assertIn("SchemaB", analysis.unique_cycle_schemas)
        self.assertGreater(analysis.cycle_complexity_score, 0)
        
    def test_integration_with_parsing_context(self) -> None:
        """Test integration with existing ParsingContext."""
        context = ParsingContext()
        detector = integrate_enhanced_cycle_detection(context)
        
        self.assertIsNotNone(detector)
        self.assertTrue(hasattr(context, 'enhanced_cycle_detector'))
        self.assertIsInstance(context.enhanced_cycle_detector, EnhancedCycleDetector)
        
        # Test that enhanced detection works through context
        is_cycle, cycle_path = context.enter_schema("TestSchema")
        self.assertFalse(is_cycle)
        
        is_cycle, cycle_path = context.enter_schema("TestSchema")
        self.assertTrue(is_cycle)
        self.assertIsNotNone(cycle_path)
        
    def test_placeholder_schema_creation(self) -> None:
        """Test creation of placeholder schemas for cycles."""
        # Create a cycle for testing
        self.detector.enter_schema("SchemaA")
        is_cycle, cycle_info = self.detector.enter_schema("SchemaA")
        self.assertTrue(is_cycle)
        
        if cycle_info:
            # Test self-referential placeholder
            placeholder = self.detector.create_cycle_placeholder_schema(
                "SchemaA", cycle_info, allow_cycle=True
            )
            self.assertTrue(placeholder._is_self_referential_stub)
            self.assertFalse(placeholder._from_unresolved_ref)
            
            # Test circular reference placeholder
            placeholder = self.detector.create_cycle_placeholder_schema(
                "SchemaA", cycle_info, allow_cycle=False
            )
            self.assertTrue(placeholder._is_circular_ref)
            self.assertTrue(placeholder._from_unresolved_ref)
            self.assertIsNotNone(placeholder._circular_ref_path)
            
    def test_dependency_tracking(self) -> None:
        """Test schema dependency tracking functionality."""
        self.detector.add_dependency("SchemaA", "SchemaB")
        self.detector.add_dependency("SchemaB", "SchemaC")
        self.detector.add_dependency("SchemaA", "SchemaD")
        
        dependencies = self.detector.schema_dependencies
        self.assertIn("SchemaA", dependencies)
        self.assertIn("SchemaB", dependencies["SchemaA"])
        self.assertIn("SchemaD", dependencies["SchemaA"])
        self.assertIn("SchemaC", dependencies["SchemaB"])
        
    def test_detector_reset(self) -> None:
        """Test that detector properly resets state."""
        # Add some state
        self.detector.enter_schema("SchemaA")
        self.detector.enter_schema("SchemaA")  # Create cycle
        self.detector.add_dependency("SchemaA", "SchemaB")
        
        # Verify state exists
        self.assertGreater(len(self.detector.detected_cycles), 0)
        self.assertGreater(len(self.detector.parsing_stack), 0)
        self.assertGreater(len(self.detector.schema_dependencies), 0)
        
        # Reset
        self.detector.reset()
        
        # Verify state is cleared
        self.assertEqual(len(self.detector.detected_cycles), 0)
        self.assertEqual(len(self.detector.parsing_stack), 0)
        self.assertEqual(len(self.detector.schema_dependencies), 0)
        self.assertEqual(len(self.detector.schemas_in_cycles), 0)
        self.assertEqual(self.detector.recursion_depth, 0)


if __name__ == "__main__":
    unittest.main()