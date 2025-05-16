"""
Handles the promotion of inline object schemas to global schemas.
"""

from __future__ import annotations

import logging
from typing import Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.utils import NameSanitizer


def _attempt_promote_inline_object(
    parent_schema_name: Optional[str],  # Name of the schema containing the property
    property_key: str,  # The key (name) of the property being processed
    property_schema_obj: IRSchema,  # The IRSchema of the property itself (already parsed)
    context: ParsingContext,
    logger: logging.Logger,
) -> Optional[IRSchema]:
    logger.debug(
        f"PROMO_ATTEMPT: parent='{parent_schema_name}', prop_key='{property_key}', "
        f"prop_schema_name='{property_schema_obj.name}', prop_schema_type='{property_schema_obj.type}', "
        f"prop_is_enum='{property_schema_obj.enum is not None}', prop_is_ref='{property_schema_obj._from_unresolved_ref}'"
    )
    """
    Checks if a given property's schema (`property_schema_obj`) represents an inline object
    that should be "promoted" to a global schema definition.

    Conditions for promotion:
    - `property_schema_obj.type` is "object".
    - `property_schema_obj.enum` is None (i.e., it's not an enum).
    - `property_schema_obj._from_unresolved_ref` is False (it wasn't from a $ref).

    If promoted:
    1. A unique global name is generated for `property_schema_obj`.
    2. `property_schema_obj.name` is updated to this new global name.
    3. `property_schema_obj` is added/updated in `context.parsed_schemas` under its new global name.
    4. A new IRSchema is returned for the original property, which now *refers* (by type)
       to the globally registered `property_schema_obj`.
       This new IRSchema preserves the original property's description, nullability etc.
    """
    if property_schema_obj.type != "object":
        logger.debug(
            f"PROMO_SKIP: parent='{parent_schema_name}', prop_key='{property_key}' not promoted, type is '{property_schema_obj.type}', not 'object'."
        )
        return None

    if property_schema_obj.enum is not None:
        logger.debug(
            f"PROMO_SKIP: parent='{parent_schema_name}', prop_key='{property_key}' not promoted, it is an enum."
        )
        return None

    if property_schema_obj._from_unresolved_ref:
        logger.debug(
            f"PROMO_SKIP: parent='{parent_schema_name}', prop_key='{property_key}' not promoted, it was from a $ref."
        )
        return None

    # Improved naming strategy for more intuitive and descriptive schema naming
    sanitized_prop_key_class_name = NameSanitizer.sanitize_class_name(property_key)
    
    # Always add a sensible suffix based on property type
    if sanitized_prop_key_class_name.endswith("s") and len(sanitized_prop_key_class_name) > 2:
        # Likely a collection property - turn plural to singular (e.g., "Items" -> "Item")
        # This helps with array properties where each item is an unnamed object
        sanitized_prop_key_class_name = sanitized_prop_key_class_name[:-1]
    
    # Add a meaningful suffix if it doesn't already have one
    if not any(sanitized_prop_key_class_name.endswith(suffix) for suffix in ["Item", "Data", "Info", "Object", "Record", "Entry"]):
        if property_schema_obj.properties and any(p.endswith("Id") or p == "id" for p in property_schema_obj.properties):
            # Likely an entity - use basic name (User, Product, etc.)
            pass
        else:
            # Generic data object - add "Data" suffix for clarity
            sanitized_prop_key_class_name += "Data"
            
    if parent_schema_name:
        # Ensure parent and property names are connected meaningfully
        # e.g., "EventData" for the "data" property in "LogEvent" -> "LogEventData"
        sanitized_parent_plus_prop_class_name = NameSanitizer.sanitize_class_name(
            f"{parent_schema_name}{sanitized_prop_key_class_name}"
        )
    else:
        # If no parent, the "parent plus prop" effectively becomes just the prop name, possibly with a prefix for uniqueness
        sanitized_parent_plus_prop_class_name = sanitized_prop_key_class_name

    chosen_global_name: Optional[str] = None

    # Preference 1: Sanitized property key (e.g. "Costs"), if available and not pointing to a different existing schema.
    if (
        sanitized_prop_key_class_name not in context.parsed_schemas
        or context.parsed_schemas.get(sanitized_prop_key_class_name) is property_schema_obj
    ):
        chosen_global_name = sanitized_prop_key_class_name
    # Preference 2: Sanitized ParentName + PropertyName (e.g. "LogDocumentEventRequestCosts" or just "Costs" if parent is None)
    elif (
        sanitized_parent_plus_prop_class_name not in context.parsed_schemas
        or context.parsed_schemas.get(sanitized_parent_plus_prop_class_name) is property_schema_obj
    ):
        chosen_global_name = sanitized_parent_plus_prop_class_name
    else:
        # Fallback to a counter. Base for counter is ParentNamePropertyName or just PropertyName if parent is None.
        base_name_for_counter = sanitized_parent_plus_prop_class_name
        counter = 1
        temp_name = f"{base_name_for_counter}{counter}"
        while temp_name in context.parsed_schemas and context.parsed_schemas[temp_name] is not property_schema_obj:
            counter += 1
            temp_name = f"{base_name_for_counter}{counter}"
        chosen_global_name = temp_name

    original_name_of_promoted_obj = property_schema_obj.name
    property_schema_obj.name = chosen_global_name
    context.parsed_schemas[chosen_global_name] = property_schema_obj

    # Corrected logger call for clarity and f-string safety
    parent_display_name = parent_schema_name or "<None>"
    logger.info(
        f"PROMOTED_OBJECT: Promoted inline object for property '{parent_display_name}.{property_key}' "
        f"(original contextual name: '{original_name_of_promoted_obj}') to global schema '{chosen_global_name}'."
    )

    property_ref_ir = IRSchema(
        name=property_key,
        type=chosen_global_name,
        description=property_schema_obj.description,
        is_nullable=property_schema_obj.is_nullable,
    )
    property_ref_ir._refers_to_schema = property_schema_obj

    return property_ref_ir
