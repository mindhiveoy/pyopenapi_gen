from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, Mapping

# Import NameSanitizer for use in name generation
from pyopenapi_gen.core.utils import NameSanitizer

# REVERTED: TEMPORARY DEBUG LOGGER REMOVED
# properties_logger = logging.getLogger("pyopenapi_gen.core.parsing.keywords.properties_parser_DEBUG")
# properties_logger.setLevel(logging.DEBUG)
# # Ensure there's a handler if running in some environments
# if not properties_logger.handlers:
#    properties_logger.addHandler(logging.StreamHandler())
from ..context import ParsingContext
from ..transformers.inline_object_promoter import _attempt_promote_inline_object

# Specific helpers needed by _parse_properties

if TYPE_CHECKING:
    from pyopenapi_gen import IRSchema  # Main IR model

    # from ..context import ParsingContext  # No longer here
    # No direct import of _parse_schema from schema_parser to avoid circularity
    pass


def _parse_properties(
    properties_node: Mapping[str, Any],
    parent_schema_name: str | None,
    context: ParsingContext,
    max_depth: int,
    parse_fn: Callable[[str | None, Mapping[str, Any] | None, ParsingContext, int | None], IRSchema],
    logger: logging.Logger,
) -> dict[str, IRSchema]:
    """Parse properties from a schema node.

    Contracts:
        Pre-conditions:
            - properties_node is a valid Mapping
            - context is a valid ParsingContext instance
            - max_depth >= 0
            - parse_fn is a callable for parsing schemas
        Post-conditions:
            - Returns a dictionary mapping property names to IRSchema instances
            - Property references are properly maintained
    """
    properties_map: dict[str, IRSchema] = {}

    for prop_key, prop_schema_node in properties_node.items():
        # Skip invalid property names
        if not prop_key or not isinstance(prop_key, str):
            logger.warning(f"Skipping property with invalid name: {prop_key}")
            continue

        # Align with _parse_schema property naming logic:
        # ParentNamePropName or just PropName if parent is anonymous.
        sanitized_prop_key_for_name = NameSanitizer.sanitize_class_name(prop_key)
        if parent_schema_name:
            # Ensure parent_schema_name is also sanitized if it's part of the name
            # This is implicitly handled if parent_schema_name comes from an IRSchema.name already.
            # For direct use, ensure it's PascalCase for consistency,
            # though _parse_schema currently doesn't re-sanitize it.
            # Assuming parent_schema_name is already a valid schema name (e.g. "ParentSchema")
            prop_schema_context_name = f"{parent_schema_name}{sanitized_prop_key_for_name}"
        else:
            prop_schema_context_name = sanitized_prop_key_for_name

        # Parse the property schema
        prop_schema_ir = parse_fn(prop_schema_context_name, prop_schema_node, context, max_depth)

        # Handle $ref in property schema
        if isinstance(prop_schema_node, Mapping) and "$ref" in prop_schema_node:
            ref_value = prop_schema_node["$ref"]
            ref_name = ref_value.split("/")[-1]
            if ref_name in context.parsed_schemas:
                prop_schema_ir._refers_to_schema = context.parsed_schemas[ref_name]

        # Attempt to promote inline object
        promoted_ir = _attempt_promote_inline_object(parent_schema_name, prop_key, prop_schema_ir, context, logger)
        if promoted_ir is not None:
            properties_map[prop_key] = promoted_ir
            logger.debug(
                f"Added promoted '{prop_key}' (name: {getattr(promoted_ir, 'name', 'N/A')}) "
                f"to properties_map for '{parent_schema_name}'"
            )
        else:
            properties_map[prop_key] = prop_schema_ir
            logger.debug(
                f"Added original '{prop_key}' (name: {getattr(prop_schema_ir, 'name', 'N/A')}, "
                f"type: {getattr(prop_schema_ir, 'type', 'N/A')}, "
                f"circular: {getattr(prop_schema_ir, '_is_circular_ref', 'N/A')}) "
                f"to properties_map for '{parent_schema_name}'"
            )

    logger.debug(f"_parse_properties FINALLY returning for parent '{parent_schema_name}': {properties_map}")
    # import pdb; pdb.set_trace() # For local debugging if needed
    return properties_map
