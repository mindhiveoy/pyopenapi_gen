"""
Dedicated parser for determining primary type and nullability from a schema's 'type' field.
"""

from __future__ import annotations

from typing import (
    Any,
    Optional,
    List,
)  # Changed from list to List for older Python compatibility if needed, but list is fine for 3.9+

# Note: IRSchema is not needed here as this function doesn't construct it.


def extract_primary_type_and_nullability(
    node_type_field: Any, schema_name_for_warning: Optional[str]
) -> tuple[Optional[str], bool, List[str]]:  # Changed to List[str]
    """Determines schema type and nullability from a schema's 'type' field.

    Args:
        node_type_field: The value of the 'type' field from the schema node.
        schema_name_for_warning: The name of the schema, for use in warning messages.

    Returns:
        A tuple of (primary_type, is_nullable, warnings).

        primary_type: The main data type of the schema (e.g. "string" or "integer")
        is_nullable: Whether the schema can be null.
        warnings: Any warnings that occurred during processing.
    """
    warnings: List[str] = []
    
    # No type field at all?
    if node_type_field is None:
        return None, False, warnings
    
    # Simple type as string
    if isinstance(node_type_field, str):
        if node_type_field == "null":
            return None, True, warnings
        return node_type_field, False, warnings
    
    # If the type field is an array, handle each type in it
    if isinstance(node_type_field, list):
        # Empty array case - this should result in Any type
        if not node_type_field:
            return None, False, warnings
            
        # Parse type field as array [primary_type, "null"]
        has_null_type = False
        non_null_types = []
        
        for t in node_type_field:
            if t == "null":
                has_null_type = True
            else:
                non_null_types.append(t)
        
        if len(non_null_types) == 0:
            # Only "null" in type array?
            if has_null_type:
                return None, True, warnings
            # Empty array (shouldn't happen due to earlier check, but for safety)
            return None, False, warnings
            
        # Exactly one non-null type with possible null
        if len(non_null_types) == 1:
            return non_null_types[0], has_null_type, warnings
            
        # Multiple non-null types - OpenAPI 3.1 allows multiple types
        warning_type_string = ", ".join(f"'{t}'" for t in non_null_types)
        schema_display = f"'{schema_name_for_warning}'" if schema_name_for_warning else "Schema"
        warning_message = f"{schema_display} has multiple types: {warning_type_string}. Using '{non_null_types[0]}'."
        warnings.append(warning_message)
        return non_null_types[0], has_null_type, warnings
    
    # If we get here, type field is neither string nor list
    schema_display = f"'{schema_name_for_warning}'" if schema_name_for_warning else "Schema"
    warning_message = f"{schema_display} has unexpected 'type' field: {node_type_field!r}. Ignoring."
    warnings.append(warning_message)
    return None, False, warnings
