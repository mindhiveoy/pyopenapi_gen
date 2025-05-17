"""
Helper module for handling cyclic property references in schemas.
"""

import logging
from typing import Set

from pyopenapi_gen.ir import IRSchema

from ....context import ParsingContext

logger = logging.getLogger(__name__)


def mark_cyclic_property_references(schema_obj: IRSchema, ref_name: str, context: ParsingContext) -> None:
    """
    Marks properties in a schema that form cycles as unresolved.

    Args:
        schema_obj: The schema object to check for cycles
        ref_name: The name of the schema being referenced
        context: The parsing context

    Pre-conditions:
        - schema_obj is a valid IRSchema instance
        - ref_name is a non-empty string
        - context is a valid ParsingContext instance

    Post-conditions:
        - Properties that form cycles are marked as unresolved
        - Non-cyclic properties remain unchanged
    """
    if not schema_obj.properties:
        return

    visited: Set[str] = set()

    def _check_cycle(prop_name: str) -> bool:
        if prop_name in visited:
            return True
        visited.add(prop_name)

        prop_schema = schema_obj.properties.get(prop_name)
        if not prop_schema or not prop_schema._refers_to_schema:
            return False

        if prop_schema._refers_to_schema.name == ref_name:
            return True

        if prop_schema._refers_to_schema.properties:
            for nested_prop_name in prop_schema._refers_to_schema.properties:
                nested_prop = prop_schema._refers_to_schema.properties[nested_prop_name]
                if nested_prop._refers_to_schema and nested_prop._refers_to_schema.name == ref_name:
                    return True
                if _check_cycle(nested_prop_name):
                    return True

        return False

    # Check each property for cycles
    for prop_name, prop_schema in schema_obj.properties.items():
        if _check_cycle(prop_name):
            prop_schema._from_unresolved_ref = True
            prop_schema._is_circular_ref = True
            context.cycle_detected = True
            logger.debug(f"Cyclic property reference detected: {ref_name}.{prop_name}")
