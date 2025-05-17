"""
Dedicated parser for determining primary type and nullability from a schema's 'type' field.
"""

from __future__ import annotations

from typing import (
    Any,
    List,
    Optional,
    Tuple,
)  # Changed from list to List for older Python compatibility if needed, but list is fine for 3.9+

# Note: IRSchema is not needed here as this function doesn't construct it.


def extract_primary_type_and_nullability(
    type_node: Any, schema_name: Optional[str] = None
) -> Tuple[Optional[str], bool, List[str]]:
    """Extract the primary type and nullability from a schema's 'type' field.

    Contracts:
        Pre-conditions:
            - type_node is the value of the 'type' field from a schema
        Post-conditions:
            - Returns a tuple of (primary_type, is_nullable, warnings)
            - primary_type is None if type_node is None or invalid
            - is_nullable is True if type_node is 'null' or contains 'null'
            - warnings contains any warnings about type handling
    """
    warnings: List[str] = []
    is_nullable = False

    if type_node is None:
        return None, False, warnings

    # Handle array of types
    if isinstance(type_node, list):
        if not type_node:
            warnings.append(f"Empty type array in schema '{schema_name}'")
            return None, False, warnings

        # Check for nullability
        if "null" in type_node:
            is_nullable = True
            type_node = [t for t in type_node if t != "null"]

        if not type_node:
            warnings.append(f"Only 'null' type in array for schema '{schema_name}'")
            return None, True, warnings

        # Use the first non-null type
        primary_type = type_node[0]
        if len(type_node) > 1:
            warnings.append(f"Multiple types in array for schema '{schema_name}'. Using first type: {primary_type}")
    else:
        primary_type = type_node

    # Validate the type
    if not isinstance(primary_type, str):
        warnings.append(f"Invalid type value '{primary_type}' in schema '{schema_name}'")
        return None, is_nullable, warnings

    # Normalize the type
    primary_type = primary_type.lower()
    if primary_type not in {"string", "number", "integer", "boolean", "object", "array", "null"}:
        warnings.append(f"Unknown type '{primary_type}' in schema '{schema_name}'")
        return None, is_nullable, warnings

    # If the determined primary_type is "null", it means the actual type is None, but it IS nullable.
    if primary_type == "null":
        return None, True, warnings  # Ensure is_nullable is True

    return primary_type, is_nullable, warnings
