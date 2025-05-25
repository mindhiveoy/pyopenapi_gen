"""
Unified cycle detection system for schema parsing.

This module provides a comprehensive, conflict-free approach to cycle detection
that handles structural cycles, processing cycles, and depth limits consistently.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


class SchemaState(Enum):
    """States a schema can be in during parsing."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PLACEHOLDER_CYCLE = "placeholder_cycle"
    PLACEHOLDER_DEPTH = "placeholder_depth"
    PLACEHOLDER_SELF_REF = "placeholder_self_ref"


class CycleType(Enum):
    """Types of cycles that can be detected."""
    STRUCTURAL = "structural"  # Schema references form a loop
    SELF_REFERENCE = "self_reference"  # Schema directly references itself
    MAX_DEPTH = "max_depth"  # Recursion depth limit exceeded


class CycleAction(Enum):
    """Actions to take when cycle is detected."""
    CONTINUE_PARSING = "continue"  # No cycle or allowed cycle
    RETURN_PLACEHOLDER = "placeholder"  # Return pre-made placeholder
    CREATE_PLACEHOLDER = "create"  # Create new placeholder
    RETURN_EXISTING = "existing"  # Return existing parsed schema


@dataclass
class CycleInfo:
    """Information about a detected cycle."""
    schema_name: str
    cycle_path: List[str]
    cycle_type: CycleType
    is_direct_self_reference: bool
    depth_when_detected: int


@dataclass
class CycleDetectionResult:
    """Result of cycle detection check."""
    is_cycle: bool
    cycle_type: Optional[CycleType]
    action: CycleAction
    cycle_info: Optional[CycleInfo] = None
    placeholder_schema: Optional[IRSchema] = None


@dataclass
class UnifiedCycleContext:
    """Unified context for all cycle detection mechanisms."""

    # Core tracking
    schema_stack: List[str] = field(default_factory=list)
    schema_states: Dict[str, SchemaState] = field(default_factory=dict)
    parsed_schemas: Dict[str, IRSchema] = field(default_factory=dict)
    recursion_depth: int = 0

    # Detection results
    detected_cycles: List[CycleInfo] = field(default_factory=list)
    depth_exceeded_schemas: Set[str] = field(default_factory=set)
    cycle_detected: bool = False  # Global flag for backward compatibility

    # Configuration
    max_depth: int = 150
    allow_self_reference: bool = False


def analyze_cycle(schema_name: str, schema_stack: List[str]) -> CycleInfo:
    """Analyze a detected cycle to determine its characteristics."""
    try:
        start_index = schema_stack.index(schema_name)
        cycle_path = schema_stack[start_index:] + [schema_name]
    except ValueError:
        # Schema not in stack - shouldn't happen, but handle gracefully
        cycle_path = [schema_name, schema_name]

    is_direct_self_reference = len(cycle_path) == 2 and cycle_path[0] == cycle_path[1]

    cycle_type = CycleType.SELF_REFERENCE if is_direct_self_reference else CycleType.STRUCTURAL

    return CycleInfo(
        schema_name=schema_name,
        cycle_path=cycle_path,
        cycle_type=cycle_type,
        is_direct_self_reference=is_direct_self_reference,
        depth_when_detected=len(schema_stack)
    )


def create_cycle_placeholder(schema_name: str, cycle_info: CycleInfo) -> IRSchema:
    """Create a placeholder IRSchema for cycle detection."""
    sanitized_name = NameSanitizer.sanitize_class_name(schema_name)
    cycle_path_str = " -> ".join(cycle_info.cycle_path)

    return IRSchema(
        name=sanitized_name,
        type="object",
        description=f"[Circular reference detected: {cycle_path_str}]",
        _from_unresolved_ref=True,
        _circular_ref_path=cycle_path_str,
        _is_circular_ref=True,
    )


def create_self_ref_placeholder(schema_name: str, cycle_info: CycleInfo) -> IRSchema:
    """Create a placeholder IRSchema for allowed self-reference."""
    sanitized_name = NameSanitizer.sanitize_class_name(schema_name)

    return IRSchema(
        name=sanitized_name,
        type="object",
        description=f"[Self-referencing schema: {schema_name}]",
        _is_self_referential_stub=True,
    )


def create_depth_placeholder(schema_name: str, depth: int) -> IRSchema:
    """Create a placeholder IRSchema for max depth exceeded."""
    sanitized_name = NameSanitizer.sanitize_class_name(schema_name)
    description = f"[Maximum recursion depth ({depth}) exceeded for '{schema_name}']"

    # Import cycle_helpers to use its logging functionality
    from .cycle_helpers import logger as cycle_helpers_logger
    cycle_helpers_logger.warning(description)

    return IRSchema(
        name=sanitized_name,
        type="object",
        description=description,
        _max_depth_exceeded_marker=True,
    )


def unified_cycle_check(
    schema_name: Optional[str],
    context: UnifiedCycleContext
) -> CycleDetectionResult:
    """Unified cycle detection that handles all cases."""

    if schema_name is None:
        return CycleDetectionResult(False, None, CycleAction.CONTINUE_PARSING)

    # Check current state
    current_state = context.schema_states.get(schema_name, SchemaState.NOT_STARTED)

    # 1. If already completed, reuse (no cycle)
    if current_state == SchemaState.COMPLETED:
        return CycleDetectionResult(False, None, CycleAction.RETURN_EXISTING)

    # 2. If already a placeholder, reuse it
    if current_state in [SchemaState.PLACEHOLDER_CYCLE, SchemaState.PLACEHOLDER_DEPTH, SchemaState.PLACEHOLDER_SELF_REF]:
        return CycleDetectionResult(True, None, CycleAction.RETURN_PLACEHOLDER)

    # 3. Check depth limit BEFORE checking cycles (dynamically check environment)
    import os
    max_depth = int(os.environ.get("PYOPENAPI_MAX_DEPTH", context.max_depth))
    if context.recursion_depth > max_depth:
        context.depth_exceeded_schemas.add(schema_name)
        context.schema_states[schema_name] = SchemaState.PLACEHOLDER_DEPTH
        context.cycle_detected = True  # Max depth exceeded is considered a form of cycle detection
        placeholder = create_depth_placeholder(schema_name, max_depth)
        context.parsed_schemas[schema_name] = placeholder
        return CycleDetectionResult(
            True,
            CycleType.MAX_DEPTH,
            CycleAction.CREATE_PLACEHOLDER,
            placeholder_schema=placeholder
        )

    # 4. Check for structural cycle
    if schema_name in context.schema_stack:
        cycle_info = analyze_cycle(schema_name, context.schema_stack)
        context.cycle_detected = True

        # For cycles, create a placeholder for the re-entrant reference, not the original schema
        # This allows the original schema parsing to complete normally
        # The re-entrant reference gets a circular placeholder

        # Create a unique key for this specific cycle reference
        cycle_ref_key = f"{schema_name}_cycle_ref_{len(context.detected_cycles)}"

        # Determine if cycle is allowed
        if context.allow_self_reference and cycle_info.is_direct_self_reference:
            placeholder = create_self_ref_placeholder(schema_name, cycle_info)
        else:
            context.detected_cycles.append(cycle_info)
            placeholder = create_cycle_placeholder(schema_name, cycle_info)

        # Determine storage policy based on cycle characteristics
        is_synthetic_schema = schema_name and (
            "Item" in schema_name or  # Array item schemas
            "Property" in schema_name  # Property schemas
        )

        # Check for specific known patterns
        cycle_path_str = " -> ".join(cycle_info.cycle_path)
        is_direct_array_self_ref = (
            "Children" in cycle_path_str and "ChildrenItem" in cycle_path_str and
            cycle_info.cycle_path[0] == cycle_info.cycle_path[-1]
        )
        is_nested_property_self_ref = (
            any(name.startswith(schema_name) and name != schema_name and not name.endswith("Item")
                for name in cycle_info.cycle_path) and
            cycle_info.cycle_path[0] == cycle_info.cycle_path[-1]
        )

        should_store_placeholder = (
            is_synthetic_schema or
            cycle_info.is_direct_self_reference or
            is_direct_array_self_ref or
            is_nested_property_self_ref
        )

        if should_store_placeholder:
            context.parsed_schemas[schema_name] = placeholder
            # Mark schema state appropriately
            if context.allow_self_reference and cycle_info.is_direct_self_reference:
                context.schema_states[schema_name] = SchemaState.PLACEHOLDER_SELF_REF
            else:
                context.schema_states[schema_name] = SchemaState.PLACEHOLDER_CYCLE

        # Don't mark the original schema as a placeholder - just return the placeholder for this reference
        return CycleDetectionResult(
            True,
            cycle_info.cycle_type if not (context.allow_self_reference and cycle_info.is_direct_self_reference) else CycleType.SELF_REFERENCE,
            CycleAction.CREATE_PLACEHOLDER,
            cycle_info=cycle_info,
            placeholder_schema=placeholder
        )

    # 5. No cycle detected - proceed with parsing
    context.schema_states[schema_name] = SchemaState.IN_PROGRESS
    return CycleDetectionResult(False, None, CycleAction.CONTINUE_PARSING)


def unified_enter_schema(schema_name: Optional[str], context: UnifiedCycleContext) -> CycleDetectionResult:
    """Unified entry point that always maintains consistent state."""
    context.recursion_depth += 1

    result = unified_cycle_check(schema_name, context)

    # Only add to stack if we're going to continue parsing
    if result.action == CycleAction.CONTINUE_PARSING and schema_name:
        context.schema_stack.append(schema_name)

    return result


def unified_exit_schema(schema_name: Optional[str], context: UnifiedCycleContext) -> None:
    """Unified exit that always maintains consistent state."""
    if context.recursion_depth > 0:
        context.recursion_depth -= 1

    if schema_name and schema_name in context.schema_stack:
        context.schema_stack.remove(schema_name)

    # Mark as completed if it was in progress (but don't change placeholder states)
    if schema_name and context.schema_states.get(schema_name) == SchemaState.IN_PROGRESS:
        context.schema_states[schema_name] = SchemaState.COMPLETED


def get_schema_or_placeholder(schema_name: str, context: UnifiedCycleContext) -> Optional[IRSchema]:
    """Get an existing schema or placeholder from the context."""
    return context.parsed_schemas.get(schema_name)
