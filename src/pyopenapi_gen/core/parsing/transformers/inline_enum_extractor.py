"""
Handles the extraction of inline enums from schema definitions.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional

from .... import IRSchema
from ...utils import NameSanitizer
from ..context import ParsingContext


def _extract_enum_from_property_node(
    parent_schema_name: Optional[str],
    property_key: str,
    property_node_data: Mapping[str, Any],
    context: ParsingContext,
    logger: logging.Logger,
) -> Optional[IRSchema]:
    """
    Checks a property's schema node for an inline enum definition.

    If an inline enum is found (i.e., the node is a dict, has "enum", and is not a $ref),
    this function:
    1. Creates a new global IRSchema for the enum.
    2. Adds this new enum schema to context.parsed_schemas.
    3. Returns a new IRSchema representing the property, which refers (by type)
       to the globally registered enum.

    Args:
        parent_schema_name: The name of the parent schema containing the property.
                            Used for generating a descriptive enum name.
        property_key: The key (name) of the property being processed.
        property_node_data: The raw schema definition for the property.
        context: The global parsing context.
        logger: Logger instance for logging messages.

    Returns:
        An IRSchema for the property referring to the new global enum if an inline
        enum was extracted. Otherwise, returns None.
    """
    if not (isinstance(property_node_data, dict) and "enum" in property_node_data and "$ref" not in property_node_data):
        return None

    enum_values = property_node_data["enum"]
    # Default to "string" if type is not specified, as per OpenAPI for enums
    enum_type_from_node = property_node_data.get("type", "string")
    enum_description = property_node_data.get("description")

    # Improved naming for inline enums - create more descriptive and semantic names
    # First, process the parent schema name
    if parent_schema_name:
        parent_class_name_for_enum = NameSanitizer.sanitize_class_name(parent_schema_name)
    else:
        # Instead of generic "AnonymousSchema", try to give a more descriptive context name
        # based on common patterns like "status" or "type" fields
        if property_key.lower() in ["status", "state", "type", "category", "role", "permission", "level"]:
            # These are common fields that often have enums - use a descriptive prefix based on the property
            parent_class_name_for_enum = {
                "status": "Status",
                "state": "State",
                "type": "Type",
                "category": "Category",
                "role": "Role",
                "permission": "Permission",
                "level": "Level",
            }.get(property_key.lower(), "Resource")
        else:
            # Use a more semantic name than "AnonymousSchema"
            parent_class_name_for_enum = "AnonymousSchema"

    # Process the property name for the enum
    prop_class_name_for_enum = NameSanitizer.sanitize_class_name(property_key)

    # Special handling for common property names - make the enum name more specific
    if prop_class_name_for_enum.lower() in ["status", "state", "type", "category"]:
        # Example: Convert "Status" property in "Order" class to "OrderStatusEnum"
        # Instead of just "OrderStatusEnum" which doesn't indicate what type of status it is
        base_generated_enum_name = f"{parent_class_name_for_enum}{prop_class_name_for_enum}Enum"
    else:
        # For other properties, keep the standard naming pattern but ensure "Enum" suffix
        if not prop_class_name_for_enum.endswith("Enum"):
            base_generated_enum_name = f"{parent_class_name_for_enum}{prop_class_name_for_enum}Enum"
        else:
            base_generated_enum_name = f"{parent_class_name_for_enum}{prop_class_name_for_enum}"

    # Ensure uniqueness with counter if needed
    generated_enum_name = base_generated_enum_name
    counter = 1
    while generated_enum_name in context.parsed_schemas:
        # Ensure the schema in context isn't the exact same definition
        # For now, simple name collision avoidance is sufficient
        generated_enum_name = f"{base_generated_enum_name}{counter}"
        counter += 1

    # Construct the name for logging/description before sanitization for clarity
    prop_schema_context_name = f"{parent_schema_name}.{property_key}" if parent_schema_name else property_key

    new_enum_ir = IRSchema(
        name=generated_enum_name,
        type=enum_type_from_node,
        enum=enum_values,
        description=property_node_data.get("description") or f"An enumeration for {prop_schema_context_name}",
        properties={},  # Enums do not have properties in this context
        required=[],  # Enums do not have required fields
    )
    context.parsed_schemas[generated_enum_name] = new_enum_ir
    logger.debug(
        f"INLINE_ENUM_EXTRACT: Extracted inline enum for '{prop_schema_context_name}' "
        f"to global schema '{generated_enum_name}'. In context: {generated_enum_name in context.parsed_schemas}"
    )

    # Return an IRSchema for the property that refers to this new global enum
    property_ir_referencing_enum = IRSchema(
        name=property_key,  # The property keeps its original name
        type=generated_enum_name,  # Type is the name of the new global enum
        description=enum_description,  # Property's original description
        is_nullable=property_node_data.get("nullable", False)
        or ("null" in enum_type_from_node if isinstance(enum_type_from_node, list) else False),
        # Other fields like format, etc., are not typically on the property ref if it's just a type ref to an enum.
        # The enum definition itself holds those.
    )
    return property_ir_referencing_enum


def _process_standalone_inline_enum(
    schema_name: Optional[str],  # The original intended name for this schema
    node_data: Mapping[str, Any],  # The raw node data for this schema
    schema_obj: IRSchema,  # The IRSchema object already partially parsed for this node
    context: ParsingContext,
    logger: logging.Logger,
) -> IRSchema:
    """
    Processes a schema node that might itself be an inline enum, not nested within a property.

    If the provided `node_data` defines an enum (has "enum" key, is not a $ref),
    and `schema_obj` doesn't yet have its enum values populated or a proper name,
    this function will:
    1. Ensure `schema_obj.name` is correctly sanitized and globally unique if it's an enum.
    2. Populate `schema_obj.enum` and `schema_obj.type` from `node_data`.
    3. Ensure the potentially renamed/finalized `schema_obj` is in `context.parsed_schemas`.

    This is for cases like:
    components:
      schemas:
        MyTopLevelEnum:
          type: string
          enum: ["A", "B"]
        AnotherObject:
          properties:
            some_field:
              type: string # Not an enum
            another_enum_prop: # Handled by _extract_enum_from_property_node
              type: string
              enum: ["X", "Y"]
      requestBodies:
        EnumBody:
          content:
            application/json:
              schema:
                type: string # This schema itself is an inline enum
                enum: ["C", "D"]

    Args:
        schema_name: The original name hint for this schema (e.g. from components.schemas key or a synthesized name).
        node_data: The raw OpenAPI node dictionary for the schema.
        schema_obj: The IRSchema instance created from initial parsing of `node_data`.
        context: The global parsing context.
        logger: Logger instance.

    Returns:
        The (potentially updated) IRSchema object.
    """
    # If it's not an enum defined directly in this node, or if schema_obj already has enum values, do nothing more here.
    if not (isinstance(node_data, dict) and "enum" in node_data and "$ref" not in node_data) or schema_obj.enum:
        return schema_obj

    logger.debug(
        f"STANDALONE_ENUM_CHECK: Processing node for "
        f"'{schema_name or schema_obj.name or "anonymous_schema"}' for direct enum properties."
    )

    # Ensure basic enum properties are on schema_obj if not already there from initial _parse_schema pass
    if not schema_obj.enum:
        schema_obj.enum = node_data.get("enum")
    if not schema_obj.type and node_data.get("type"):
        # TODO: Handle type extraction more robustly here, possibly using extract_primary_type_and_nullability
        # For now, simple type assignment for enums.
        raw_type = node_data.get("type", "string")
        if isinstance(raw_type, list):
            # For enums like type: [string, null], the primary type is string for the enum values themselves.
            # Nullability should be handled by schema_obj.is_nullable elsewhere.
            primary_enum_type = next((t for t in raw_type if t != "null"), "string")
            schema_obj.type = primary_enum_type
        else:
            schema_obj.type = raw_type
    elif not schema_obj.type:  # Default type for enum if not specified
        schema_obj.type = "string"

    # Ensure a proper, unique name if this is indeed an enum and needs one.
    # schema_obj.name might be None if it was parsed from, e.g., a requestBody schema directly.
    if not schema_obj.name and schema_name:
        schema_obj.name = NameSanitizer.sanitize_class_name(schema_name)
    elif not schema_obj.name:
        # Create a more descriptive name based on enum values if possible
        enum_values = schema_obj.enum or []

        # Try to determine a semantic name from the enum values
        if enum_values and all(isinstance(v, str) for v in enum_values):
            # For string enums, look for common patterns in the values
            enum_values_str = [str(v).lower() for v in enum_values]

            # Check for common patterns in enum values
            if any(v in ["pending", "active", "completed", "cancelled", "failed"] for v in enum_values_str):
                base_name = "StatusEnum"
            elif any(v in ["admin", "user", "guest", "moderator"] for v in enum_values_str):
                base_name = "RoleEnum"
            elif any(v in ["read", "write", "admin", "owner"] for v in enum_values_str):
                base_name = "PermissionEnum"
            elif any(v in ["asc", "desc", "ascending", "descending"] for v in enum_values_str):
                base_name = "SortOrderEnum"
            elif any(v in ["true", "false", "yes", "no"] for v in enum_values_str):
                base_name = "BooleanEnum"
            else:
                # Default to more descriptive name than just "UnnamedEnum"
                base_name = "ResourceTypeEnum"
        else:
            # If we can't determine from values, use a generic but still meaningful name
            base_name = "ResourceTypeEnum"

        # Ensure uniqueness
        counter = 1
        candidate_name = base_name
        while candidate_name in context.parsed_schemas:
            candidate_name = f"{base_name}{counter}"
            counter += 1

        schema_obj.name = candidate_name

    # If the name (now sanitized and potentially unique) exists in context.parsed_schemas
    # but refers to a different object, we need to ensure this schema_obj gets a unique name.
    if (
        schema_obj.name
        and schema_obj.name in context.parsed_schemas
        and context.parsed_schemas[schema_obj.name] is not schema_obj
    ):
        original_name_attempt = schema_obj.name
        counter = 1
        new_name_base = original_name_attempt
        # Avoid potential infinite loop if somehow new_name_base ends up empty or just a number.
        if not new_name_base or new_name_base.isnumeric():
            new_name_base = "Enum"  # Fallback to a generic base name

        while schema_obj.name in context.parsed_schemas and context.parsed_schemas[schema_obj.name] is not schema_obj:
            schema_obj.name = f"{new_name_base}{counter}"
            counter += 1
        logger.warning(
            f"STANDALONE_ENUM_NAME_COLLISION: Renamed schema from '{original_name_attempt}' to '{schema_obj.name}' "
            f"due to name collision with a different existing schema."
        )

    # Ensure the final named schema_obj is in the context
    if schema_obj.name and schema_obj.name not in context.parsed_schemas:
        context.parsed_schemas[schema_obj.name] = schema_obj
        logger.debug(
            f"STANDALONE_ENUM_FINALIZED: Added/updated schema '{schema_obj.name}' "
            f"in context after processing as standalone enum."
        )
    elif schema_obj.name and context.parsed_schemas[schema_obj.name] is not schema_obj:
        # This case should ideally be caught by the renaming logic above.
        # If we are here, it means a schema with this name exists, but it's not our schema_obj.
        # This indicates a problem if schema_obj was supposed to be *the* definition for that name.
        logger.error(
            f"STANDALONE_ENUM_ERROR: Schema '{schema_obj.name}' exists in context "
            f"but is not the current schema_obj. This is unexpected."
        )
    elif not schema_obj.name:
        logger.warning(
            "STANDALONE_ENUM_UNNAMED: Processed a standalone enum but it ended up "
            "without a name. This might be an issue."
        )

    return schema_obj
