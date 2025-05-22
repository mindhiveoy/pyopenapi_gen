"""
Enhanced circular reference detection system for PyOpenAPI Generator.

This module provides improved cycle detection capabilities that address
limitations in the current system:

1. Marks ALL schemas involved in a cycle, not just the re-entrant one
2. Provides better cycle path tracking and reporting
3. Supports different cycle handling strategies
4. Offers comprehensive cycle analysis and metrics
"""

import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from pyopenapi_gen.ir import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


class CycleType(Enum):
    """Types of cycles that can be detected."""
    DIRECT_SELF_REFERENCE = "direct_self_reference"  # A -> A
    MUTUAL_REFERENCE = "mutual_reference"  # A -> B -> A
    INDIRECT_CYCLE = "indirect_cycle"  # A -> B -> C -> A
    COMPLEX_CYCLE = "complex_cycle"  # Multiple interconnected cycles


class CycleHandlingStrategy(Enum):
    """Strategies for handling different types of cycles."""
    ALLOW_SELF_REFERENCE = "allow_self_reference"  # Allow A -> A
    ERROR_ALL_CYCLES = "error_all_cycles"  # Treat all cycles as errors
    FORWARD_REFERENCE = "forward_reference"  # Use forward references
    BREAK_AT_REENTRY = "break_at_reentry"  # Break cycle at re-entry point


@dataclass
class CycleInfo:
    """Information about a detected cycle."""
    cycle_type: CycleType
    schemas_involved: List[str]  # Ordered list of schemas in the cycle
    cycle_path: str  # String representation of the cycle path
    entry_point: str  # Schema where the cycle was first detected
    reentry_point: str  # Schema that caused the cycle detection
    depth_at_detection: int  # Recursion depth when cycle was detected


@dataclass
class CycleAnalysisResult:
    """Result of comprehensive cycle analysis."""
    has_cycles: bool
    cycles: List[CycleInfo]
    total_schemas_in_cycles: int
    unique_cycle_schemas: Set[str]
    max_cycle_length: int
    cycle_complexity_score: float  # Metric for cycle complexity


class EnhancedCycleDetector:
    """Enhanced cycle detection with comprehensive analysis capabilities."""
    
    def __init__(self, strategy: CycleHandlingStrategy = CycleHandlingStrategy.FORWARD_REFERENCE):
        self.strategy = strategy
        self.detected_cycles: List[CycleInfo] = []
        self.schemas_in_cycles: Set[str] = set()
        self.cycle_id_counter = 0
        
        # Stack-based tracking
        self.parsing_stack: List[str] = []
        self.recursion_depth = 0
        
        # Enhanced tracking
        self.schema_entry_depths: Dict[str, int] = {}
        self.schema_dependencies: Dict[str, Set[str]] = {}
        
    def enter_schema(self, schema_name: Optional[str]) -> Tuple[bool, Optional[CycleInfo]]:
        """
        Enhanced schema entry that detects cycles and provides detailed information.
        
        Returns:
            Tuple of (is_cycle_detected, cycle_info)
        """
        self.recursion_depth += 1
        
        if schema_name is None:
            return False, None
            
        # Record the depth where this schema was first entered
        if schema_name not in self.schema_entry_depths:
            self.schema_entry_depths[schema_name] = self.recursion_depth
            
        # Check for cycle
        if schema_name in self.parsing_stack:
            cycle_info = self._analyze_detected_cycle(schema_name)
            self.detected_cycles.append(cycle_info)
            self._mark_schemas_in_cycle(cycle_info)
            
            logger.warning(f"ENHANCED CYCLE DETECTED: {cycle_info.cycle_path}")
            logger.info(f"Cycle type: {cycle_info.cycle_type.value}, "
                       f"Schemas involved: {len(cycle_info.schemas_involved)}")
            
            return True, cycle_info
            
        self.parsing_stack.append(schema_name)
        return False, None
        
    def exit_schema(self, schema_name: Optional[str]) -> None:
        """Exit schema tracking."""
        if self.recursion_depth > 0:
            self.recursion_depth -= 1
            
        if schema_name and schema_name in self.parsing_stack:
            self.parsing_stack.remove(schema_name)
            
    def add_dependency(self, from_schema: str, to_schema: str) -> None:
        """Track schema dependencies for cycle analysis."""
        if from_schema not in self.schema_dependencies:
            self.schema_dependencies[from_schema] = set()
        self.schema_dependencies[from_schema].add(to_schema)
        
    def _analyze_detected_cycle(self, reentry_schema: str) -> CycleInfo:
        """Analyze a detected cycle and determine its properties."""
        try:
            reentry_index = self.parsing_stack.index(reentry_schema)
            cycle_schemas = self.parsing_stack[reentry_index:] + [reentry_schema]
        except ValueError:
            # Fallback if something goes wrong
            cycle_schemas = list(self.parsing_stack) + [reentry_schema]
            reentry_index = 0
            
        cycle_path = " -> ".join(cycle_schemas)
        entry_point = cycle_schemas[0]
        
        # Determine cycle type
        if len(cycle_schemas) == 2 and cycle_schemas[0] == cycle_schemas[1]:
            cycle_type = CycleType.DIRECT_SELF_REFERENCE
        elif len(cycle_schemas) == 3:  # A -> B -> A
            cycle_type = CycleType.MUTUAL_REFERENCE
        elif len(cycle_schemas) <= 5:
            cycle_type = CycleType.INDIRECT_CYCLE
        else:
            cycle_type = CycleType.COMPLEX_CYCLE
            
        return CycleInfo(
            cycle_type=cycle_type,
            schemas_involved=cycle_schemas[:-1],  # Remove duplicate at end
            cycle_path=cycle_path,
            entry_point=entry_point,
            reentry_point=reentry_schema,
            depth_at_detection=self.recursion_depth
        )
        
    def _mark_schemas_in_cycle(self, cycle_info: CycleInfo) -> None:
        """Mark all schemas involved in the cycle."""
        for schema_name in cycle_info.schemas_involved:
            self.schemas_in_cycles.add(schema_name)
            
    def should_allow_cycle(self, cycle_info: CycleInfo) -> bool:
        """Determine if a cycle should be allowed based on strategy."""
        if self.strategy == CycleHandlingStrategy.ALLOW_SELF_REFERENCE:
            return cycle_info.cycle_type == CycleType.DIRECT_SELF_REFERENCE
        elif self.strategy == CycleHandlingStrategy.ERROR_ALL_CYCLES:
            return False
        elif self.strategy == CycleHandlingStrategy.FORWARD_REFERENCE:
            # Allow all cycles, handle with forward references
            return True
        elif self.strategy == CycleHandlingStrategy.BREAK_AT_REENTRY:
            # Break cycle at the re-entry point
            return True
        else:
            return False
            
    def create_cycle_placeholder_schema(
        self, 
        schema_name: str, 
        cycle_info: CycleInfo,
        allow_cycle: bool = False
    ) -> IRSchema:
        """Create a placeholder schema for a schema involved in a cycle."""
        sanitized_name = NameSanitizer.sanitize_class_name(schema_name)
        
        if allow_cycle and cycle_info.cycle_type == CycleType.DIRECT_SELF_REFERENCE:
            # Create self-referential stub
            description = f"[Self-referential schema: {schema_name}]"
            schema = IRSchema(
                name=sanitized_name,
                type="object",
                description=description,
                _is_self_referential_stub=True,
                _from_unresolved_ref=False,
            )
        else:
            # Create circular reference placeholder
            description = f"[Circular reference in cycle: {cycle_info.cycle_path}]"
            schema = IRSchema(
                name=sanitized_name,
                type="object",
                description=description,
                _is_circular_ref=True,
                _circular_ref_path=cycle_info.cycle_path,
                _from_unresolved_ref=True,
            )
            
        return schema
        
    def mark_all_schemas_in_cycles(self, parsed_schemas: Dict[str, IRSchema]) -> None:
        """Post-processing step to mark all schemas involved in cycles."""
        for cycle in self.detected_cycles:
            allow_cycle = self.should_allow_cycle(cycle)
            
            for schema_name in cycle.schemas_involved:
                if schema_name in parsed_schemas:
                    schema = parsed_schemas[schema_name]
                    
                    if allow_cycle and cycle.cycle_type == CycleType.DIRECT_SELF_REFERENCE:
                        schema._is_self_referential_stub = True
                        schema._from_unresolved_ref = False
                    else:
                        schema._is_circular_ref = True
                        schema._circular_ref_path = cycle.cycle_path
                        schema._from_unresolved_ref = True
                        
                    # Add enhanced cycle metadata
                    if not hasattr(schema, '_cycle_info'):
                        schema._cycle_info = []
                    schema._cycle_info.append({
                        'cycle_type': cycle.cycle_type.value,
                        'cycle_path': cycle.cycle_path,
                        'is_entry_point': schema_name == cycle.entry_point,
                        'is_reentry_point': schema_name == cycle.reentry_point,
                    })
                    
    def get_cycle_analysis(self) -> CycleAnalysisResult:
        """Get comprehensive analysis of all detected cycles."""
        if not self.detected_cycles:
            return CycleAnalysisResult(
                has_cycles=False,
                cycles=[],
                total_schemas_in_cycles=0,
                unique_cycle_schemas=set(),
                max_cycle_length=0,
                cycle_complexity_score=0.0
            )
            
        unique_schemas = set()
        max_length = 0
        total_complexity = 0.0
        
        for cycle in self.detected_cycles:
            unique_schemas.update(cycle.schemas_involved)
            max_length = max(max_length, len(cycle.schemas_involved))
            
            # Calculate complexity score based on cycle type and length
            type_weight = {
                CycleType.DIRECT_SELF_REFERENCE: 1.0,
                CycleType.MUTUAL_REFERENCE: 2.0,
                CycleType.INDIRECT_CYCLE: 3.0,
                CycleType.COMPLEX_CYCLE: 5.0,
            }
            
            complexity = type_weight.get(cycle.cycle_type, 1.0) * len(cycle.schemas_involved)
            total_complexity += complexity
            
        avg_complexity = total_complexity / len(self.detected_cycles) if self.detected_cycles else 0.0
        
        return CycleAnalysisResult(
            has_cycles=True,
            cycles=self.detected_cycles,
            total_schemas_in_cycles=len(unique_schemas),
            unique_cycle_schemas=unique_schemas,
            max_cycle_length=max_length,
            cycle_complexity_score=avg_complexity
        )
        
    def reset(self) -> None:
        """Reset the detector for a new parsing session."""
        self.detected_cycles.clear()
        self.schemas_in_cycles.clear()
        self.parsing_stack.clear()
        self.recursion_depth = 0
        self.schema_entry_depths.clear()
        self.schema_dependencies.clear()
        self.cycle_id_counter = 0


def integrate_enhanced_cycle_detection(context, strategy: CycleHandlingStrategy = CycleHandlingStrategy.FORWARD_REFERENCE):
    """
    Factory function to integrate enhanced cycle detection into existing parsing context.
    
    This function can be used to upgrade existing ParsingContext instances
    with enhanced cycle detection capabilities while maintaining compatibility
    with the existing schema parser.
    """
    if not hasattr(context, 'enhanced_cycle_detector'):
        context.enhanced_cycle_detector = EnhancedCycleDetector(strategy)
        
        # Store references to original methods
        original_enter = context.enter_schema
        original_exit = context.exit_schema
        
        def enhanced_enter_schema(schema_name):
            # Call original method first to maintain existing behavior
            original_is_cycle, original_cycle_path = original_enter(schema_name)
            
            # Also track in enhanced detector (for comprehensive analysis)
            enhanced_is_cycle, cycle_info = context.enhanced_cycle_detector.enter_schema(schema_name)
            
            # Return original result to maintain compatibility
            return original_is_cycle, original_cycle_path
                
        def enhanced_exit_schema(schema_name):
            # Call enhanced detector exit
            context.enhanced_cycle_detector.exit_schema(schema_name)
            # Call original exit
            return original_exit(schema_name)
            
        # Replace methods with enhanced versions
        context.enter_schema = enhanced_enter_schema
        context.exit_schema = enhanced_exit_schema
        
    return context.enhanced_cycle_detector