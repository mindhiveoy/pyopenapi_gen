"""Schema extractors for OpenAPI IR transformation.

Provides functions to extract and transform schemas from raw OpenAPI specs.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, Dict, Mapping

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


def build_schemas(raw_schemas: Dict[str, Mapping[str, Any]], raw_components: Mapping[str, Any]) -> ParsingContext:
    """Build all named schemas up front, populating a ParsingContext.

    Contracts:
        Preconditions:
            - raw_schemas is a valid dict containing schema definitions
            - raw_components is a valid mapping containing component definitions
        Postconditions:
            - A ParsingContext is returned with all schemas parsed
            - All schemas in raw_schemas are populated in context.parsed_schemas
    """
    assert isinstance(raw_schemas, dict), "raw_schemas must be a dict"
    assert isinstance(raw_components, Mapping), "raw_components must be a Mapping"

    context = ParsingContext(raw_spec_schemas=raw_schemas, raw_spec_components=raw_components)

    # Build initial IR for all schemas found in components
    for n, nd in raw_schemas.items():
        if n not in context.parsed_schemas:
            _parse_schema(n, nd, context, allow_self_reference=True)

    # Post-condition check
    assert all(n in context.parsed_schemas for n in raw_schemas), "Not all schemas were parsed"

    return context


def extract_inline_array_items(schemas: Dict[str, IRSchema]) -> Dict[str, IRSchema]:
    """Extract inline array item schemas as unique named schemas and update references.

    Contracts:
        Preconditions:
            - schemas is a dict of IRSchema objects
        Postconditions:
            - Returns an updated schemas dict with extracted array item types
            - All array item schemas have proper names
            - No duplicate schema names are created
    """
    assert isinstance(schemas, dict), "schemas must be a dict"
    assert all(isinstance(s, IRSchema) for s in schemas.values()), "all values must be IRSchema objects"

    # Store original schema count for post-condition validation
    original_schema_count = len(schemas)
    original_schemas = set(schemas.keys())

    new_item_schemas = {}
    for schema_name, schema in list(schemas.items()):
        # Check properties for array types
        for prop_name, prop_schema in list(schema.properties.items()):
            if prop_schema.type == "array" and prop_schema.items and not prop_schema.items.name:
                # Only extract complex item schemas (objects and arrays)
                if prop_schema.items.type == "object" or prop_schema.items.type == "array":
                    # Generate a suitable name for the item schema
                    item_schema_name = f"{NameSanitizer.sanitize_class_name(schema_name)}{NameSanitizer.sanitize_class_name(prop_name)}Item"
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
    assert len(schemas) >= original_schema_count, "Schemas count should not decrease"
    assert original_schemas.issubset(set(schemas.keys())), "Original schemas should still be present"

    return schemas


def extract_inline_enums(schemas: Dict[str, IRSchema]) -> Dict[str, IRSchema]:
    """Extract inline property enums as unique schemas and update property references.

    Contracts:
        Preconditions:
            - schemas is a dict of IRSchema objects
        Postconditions:
            - Returns an updated schemas dict with extracted enum types and array item types
            - All property schemas with enums have proper names
            - All array item schemas have proper names
            - No duplicate schema names are created
    """
    assert isinstance(schemas, dict), "schemas must be a dict"
    assert all(isinstance(s, IRSchema) for s in schemas.values()), "all values must be IRSchema objects"

    # Store original schema count for post-condition validation
    original_schema_count = len(schemas)
    original_schemas = set(schemas.keys())

    # First extract array item schemas so they can have enums extracted in the next step
    schemas = extract_inline_array_items(schemas)

    new_enums = {}
    for schema_name, schema in list(schemas.items()):
        for prop_name, prop_schema in list(schema.properties.items()):
            if prop_schema.enum and not prop_schema.name:
                enum_name = f"{NameSanitizer.sanitize_class_name(schema_name)}{NameSanitizer.sanitize_class_name(prop_name)}Enum"
                base_enum_name = enum_name
                i = 1
                while enum_name in schemas or enum_name in new_enums:
                    enum_name = f"{base_enum_name}{i}"
                    i += 1

                enum_schema = IRSchema(
                    name=enum_name,
                    type=prop_schema.type,
                    enum=copy.deepcopy(prop_schema.enum),
                    description=prop_schema.description or f"Enum for {schema_name}.{prop_name}",
                )
                new_enums[enum_name] = enum_schema
                
                # Update the original property to reference the extracted enum
                prop_schema.name = enum_name
                prop_schema.type = enum_name  # Make the property reference the enum by name
                prop_schema.enum = None  # Clear the inline enum since it's now extracted

    # Update the schemas dict with the new enums
    schemas.update(new_enums)

    # Post-condition checks
    assert len(schemas) >= original_schema_count, "Schemas count should not decrease"
    assert original_schemas.issubset(set(schemas.keys())), "Original schemas should still be present"

    return schemas
