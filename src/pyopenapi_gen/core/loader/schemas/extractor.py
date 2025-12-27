"""Schema extractors for OpenAPI IR transformation.

Provides functions to extract and transform schemas from raw OpenAPI specs.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Mapping

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


def build_schemas(raw_schemas: dict[str, Mapping[str, Any]], raw_components: Mapping[str, Any]) -> ParsingContext:
    """Build all named schemas up front, populating a ParsingContext.

    Contracts:
        Preconditions:
            - raw_schemas is a valid dict containing schema definitions
            - raw_components is a valid mapping containing component definitions
        Postconditions:
            - A ParsingContext is returned with all schemas parsed
            - All schemas in raw_schemas are populated in context.parsed_schemas
    """
    if not isinstance(raw_schemas, dict):
        raise TypeError("raw_schemas must be a dict")
    if not isinstance(raw_components, Mapping):
        raise TypeError("raw_components must be a Mapping")

    context = ParsingContext(raw_spec_schemas=raw_schemas, raw_spec_components=raw_components)

    # Build initial IR for all schemas found in components
    for n, nd in raw_schemas.items():
        if n not in context.parsed_schemas:
            _parse_schema(n, nd, context, allow_self_reference=True)

    # Post-condition check
    if not all(n in context.parsed_schemas for n in raw_schemas):
        raise RuntimeError("Not all schemas were parsed")

    return context


def extract_inline_array_items(schemas: dict[str, IRSchema]) -> dict[str, IRSchema]:
    """Extract inline array item schemas as unique named schemas and update references.

    Contracts:
        Preconditions:
            - schemas is a dict of IRSchema objects
        Postconditions:
            - Returns an updated schemas dict with extracted array item types
            - All array item schemas have proper names
            - No duplicate schema names are created
    """
    if not isinstance(schemas, dict):
        raise TypeError("schemas must be a dict")
    if not all(isinstance(s, IRSchema) for s in schemas.values()):
        raise TypeError("all values must be IRSchema objects")

    # Store original schema count for post-condition validation
    original_schema_count = len(schemas)
    original_schemas = set(schemas.keys())

    new_item_schemas = {}
    for schema_name, schema in list(schemas.items()):
        # Check properties for array types
        for prop_name, prop_schema in list(schema.properties.items()):
            if prop_schema.type == "array" and prop_schema.items and not prop_schema.items.name:
                # Only extract complex item schemas (objects and arrays), not simple primitives or references
                items_schema = prop_schema.items
                is_complex_item = (
                    items_schema.type == "object"
                    or items_schema.type == "array"
                    or items_schema.properties
                    or items_schema.any_of
                    or items_schema.one_of
                    or items_schema.all_of
                )

                if is_complex_item:
                    # Generate a descriptive name for the item schema using content-aware naming
                    # For arrays of complex objects, use the pattern: {Parent}{Property}Item
                    # For arrays in response wrappers (like "data" fields), consider the content type
                    if prop_name.lower() in ["data", "items", "results", "content"]:
                        # For generic wrapper properties, try to derive name from the item type or parent
                        if items_schema.type == "object" and schema_name.endswith("Response"):
                            # Pattern: MessageBatchResponse.data -> MessageItem
                            base_name = schema_name.replace("Response", "").replace("List", "")
                            item_schema_name = f"{base_name}Item"
                        else:
                            # Fallback to standard pattern
                            item_schema_name = (
                                f"{NameSanitizer.sanitize_class_name(schema_name)}"
                                f"{NameSanitizer.sanitize_class_name(prop_name)}Item"
                            )
                    else:
                        # Standard pattern for named properties
                        item_schema_name = (
                            f"{NameSanitizer.sanitize_class_name(schema_name)}"
                            f"{NameSanitizer.sanitize_class_name(prop_name)}Item"
                        )

                    base_item_name = item_schema_name
                    i = 1
                    while item_schema_name in schemas or item_schema_name in new_item_schemas:
                        item_schema_name = f"{base_item_name}{i}"
                        i += 1

                    # Create a copy of the item schema with a name
                    items_copy = copy.deepcopy(prop_schema.items)
                    items_copy.name = item_schema_name
                    new_item_schemas[item_schema_name] = items_copy

                    # Update the original array schema to reference the named item schema
                    prop_schema.items.name = item_schema_name

    # Update the schemas dict with the new item schemas
    schemas.update(new_item_schemas)

    # Post-condition checks
    if len(schemas) < original_schema_count:
        raise RuntimeError("Schemas count should not decrease")
    if not original_schemas.issubset(set(schemas.keys())):
        raise RuntimeError("Original schemas should still be present")

    return schemas


def extract_inline_enums(schemas: dict[str, IRSchema]) -> dict[str, IRSchema]:
    """Extract inline property enums as unique schemas and update property references.

    Also ensures top-level enum schemas are properly marked for generation.

    Contracts:
        Preconditions:
            - schemas is a dict of IRSchema objects
        Postconditions:
            - Returns an updated schemas dict with extracted enum types and array item types
            - All property schemas with enums have proper names
            - All array item schemas have proper names
            - No duplicate schema names are created
            - Top-level enum schemas have generation_name set
    """
    if not isinstance(schemas, dict):
        raise TypeError("schemas must be a dict")
    if not all(isinstance(s, IRSchema) for s in schemas.values()):
        raise TypeError("all values must be IRSchema objects")

    # Store original schema count for post-condition validation
    original_schema_count = len(schemas)
    original_schemas = set(schemas.keys())

    # First extract array item schemas so they can have enums extracted in the next step
    schemas = extract_inline_array_items(schemas)

    new_enums = {}
    for schema_name, schema in list(schemas.items()):
        # Handle top-level enum schemas (those defined directly in components/schemas)
        # These are already enums but need generation_name set
        if schema.enum and schema.type in ["string", "integer", "number"]:
            # This is a top-level enum schema
            # Ensure it has generation_name set (will be properly set by emitter later,
            # but we can set it here to avoid the warning)
            if not hasattr(schema, "generation_name") or not schema.generation_name:
                schema.generation_name = schema.name
                logger.info(
                    f"Set generation_name for top-level enum schema: {schema_name} with values {schema.enum[:3]}..."
                )
            # Mark this as a properly processed enum by ensuring generation_name is set
            # This serves as the marker that this enum was properly processed
            logger.debug(f"Marked top-level enum schema: {schema_name}")

        # Extract inline enums from properties
        for prop_name, prop_schema in list(schema.properties.items()):
            # Check if this property has an inline enum that needs extraction
            # An inline enum needs extraction if:
            # 1. It has enum values defined
            # 2. The enum doesn't already exist as a separate schema in the schemas dict
            # Note: After schema parsing, property schemas have 'name' set to the property key
            # and 'generation_name' set to a sanitised class name, but the enum itself
            # isn't registered as a separate schema yet.
            has_inline_enum = prop_schema.enum and prop_schema.type in ["string", "integer", "number"]

            # Check if the enum was already extracted or is a named reference
            # Case 1: generation_name exists in schemas dict (already extracted)
            # Case 2: property name itself is a schema reference (e.g., ExistingStatusEnum)
            enum_already_extracted = (
                (
                    prop_schema.generation_name
                    and prop_schema.generation_name in schemas
                    and schemas[prop_schema.generation_name].enum
                )
                or (
                    # Property name is an explicit enum reference (class-like name, not property key)
                    prop_schema.name
                    and prop_schema.name in schemas
                    and schemas[prop_schema.name].enum
                )
                or (
                    # Property name looks like an enum class name (not a property key)
                    # Property keys are typically snake_case, class names are PascalCase
                    prop_schema.name
                    and prop_schema.name[0].isupper()
                    and "_" not in prop_schema.name
                    and prop_schema.name != prop_name  # Name differs from property key
                )
            )

            if has_inline_enum and not enum_already_extracted:
                # Use property's existing generation_name if set, otherwise create a new name
                # This keeps naming consistent with what the type resolver already assigned
                if prop_schema.generation_name:
                    enum_name = prop_schema.generation_name
                else:
                    enum_name = (
                        f"{NameSanitizer.sanitize_class_name(schema_name)}"
                        f"{NameSanitizer.sanitize_class_name(prop_name)}Enum"
                    )
                base_enum_name = enum_name
                i = 1
                while enum_name in schemas or enum_name in new_enums:
                    enum_name = f"{base_enum_name}{i}"
                    i += 1

                # Derive module stem from final enum name
                module_stem = NameSanitizer.sanitize_module_name(enum_name)

                enum_schema = IRSchema(
                    name=enum_name,
                    type=prop_schema.type,
                    enum=copy.deepcopy(prop_schema.enum),
                    description=prop_schema.description or f"Enum for {schema_name}.{prop_name}",
                )
                enum_schema.generation_name = enum_name
                enum_schema.final_module_stem = module_stem
                new_enums[enum_name] = enum_schema
                logger.debug(f"Extracted inline enum from {schema_name}.{prop_name}: {enum_name}")

                # Update the original property to reference the extracted enum
                prop_schema.name = enum_name
                prop_schema.type = enum_name  # Make the property reference the enum by name
                prop_schema.generation_name = enum_name  # Ensure property also has correct generation_name
                prop_schema.final_module_stem = module_stem  # And module stem
                prop_schema.enum = None  # Clear the inline enum since it's now extracted

    # Update the schemas dict with the new enums
    schemas.update(new_enums)

    # Post-condition checks
    if len(schemas) < original_schema_count:
        raise RuntimeError("Schemas count should not decrease")
    if not original_schemas.issubset(set(schemas.keys())):
        raise RuntimeError("Original schemas should still be present")

    return schemas
