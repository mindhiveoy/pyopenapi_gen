"""
Handles the promotion of inline object schemas to global schemas.
"""

from __future__ import annotations

import logging
from typing import Optional

from .... import IRSchema
from ...utils import NameSanitizer
from ..context import ParsingContext


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

    # Primary candidate name: ParentName + PropertyName (sanitized)
    # Example: parent="User", prop_key="address" (sanitized_prop_key_class_name="Address") -> UserAddress
    # Example: parent=None, prop_key="user_profile" -> UserProfile
    if parent_schema_name:
        # First sanitize the parent name to ensure it's in PascalCase
        sanitized_parent_name = NameSanitizer.sanitize_class_name(parent_schema_name)
        # Then combine with the sanitized property key
        base_name_candidate = f"{sanitized_parent_name}{sanitized_prop_key_class_name}"
    else:
        base_name_candidate = sanitized_prop_key_class_name

    chosen_global_name: Optional[str] = None

    # Check if the primary candidate name is available or already points to this object
    if base_name_candidate in context.parsed_schemas:
        existing_schema = context.parsed_schemas[base_name_candidate]
        # If the existing schema is identical to our property schema, reuse it
        if existing_schema.properties == property_schema_obj.properties:
            chosen_global_name = base_name_candidate
        else:
            # If different schema, try with counter
            counter = 1
            temp_name = f"{base_name_candidate}{counter}"
            while temp_name in context.parsed_schemas:
                existing_schema = context.parsed_schemas[temp_name]
                if existing_schema.properties == property_schema_obj.properties:
                    chosen_global_name = temp_name
                    break
                counter += 1
                temp_name = f"{base_name_candidate}{counter}"
            if chosen_global_name is None:
                chosen_global_name = temp_name
    else:
        chosen_global_name = base_name_candidate

    original_name_of_promoted_obj = property_schema_obj.name
    property_schema_obj.name = chosen_global_name
    context.parsed_schemas[chosen_global_name] = property_schema_obj

    # Corrected logger call for clarity and f-string safety
    parent_display_name = parent_schema_name or "<None>"

    property_ref_ir = IRSchema(
        name=property_key,
        type=chosen_global_name,
        description=property_schema_obj.description,
        is_nullable=property_schema_obj.is_nullable,
    )
    property_ref_ir._refers_to_schema = property_schema_obj

    return property_ref_ir
