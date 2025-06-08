"""
Main module for schema reference resolution.
"""

import logging
from typing import Any, Callable, Mapping, Optional

from pyopenapi_gen.ir import IRSchema

from ...context import ParsingContext
from .helpers.direct_cycle import handle_direct_cycle
from .helpers.existing_schema import handle_existing_schema
from .helpers.missing_ref import handle_missing_ref
from .helpers.new_schema import parse_new_schema

logger = logging.getLogger(__name__)


def resolve_schema_ref(
    ref_value: str,
    ref_name: str,
    context: ParsingContext,
    max_depth: int,
    _parse_schema: Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema],
) -> IRSchema:
    """
    Resolves a schema reference in an OpenAPI specification.

    Contracts:
        Pre-conditions:
            - ref_value must be a valid reference string (e.g., "#/components/schemas/MySchema")
            - ref_name must be a valid schema name
            - context must be a valid ParsingContext instance
            - max_depth must be a non-negative integer
            - _parse_schema must be a callable that parses schemas
        Post-conditions:
            - Returns a valid IRSchema instance
            - The schema is registered in context.parsed_schemas
            - Cyclic references are handled appropriately
    """
    # Extract the actual schema name from the reference
    actual_schema_name = ref_value.split("/")[-1]

    # Check for direct cycles or circular placeholders
    if actual_schema_name in context.parsed_schemas:
        existing_schema = context.parsed_schemas[actual_schema_name]
        if getattr(existing_schema, "_is_circular_ref", False):
            # logger.debug(f"Returning existing circular reference for '{actual_schema_name}'")
            return existing_schema
        # logger.debug(f"Direct cycle detected for '{actual_schema_name}', handling...")
        return handle_direct_cycle(actual_schema_name, context)

    # Check for existing fully parsed schema
    if actual_schema_name in context.parsed_schemas:
        # logger.debug(f"Returning existing fully parsed schema for '{actual_schema_name}'")
        return handle_existing_schema(actual_schema_name, context)

    # Get referenced node data
    referenced_node_data = context.raw_spec_schemas.get(actual_schema_name)

    # Handle missing references with stripped suffix fallback
    if referenced_node_data is None:
        # Try stripping common suffixes
        base_name = actual_schema_name
        for suffix in ["Response", "Request", "Input", "Output"]:
            if base_name.endswith(suffix):
                base_name = base_name[: -len(suffix)]
                if base_name in context.raw_spec_schemas:
                    # logger.debug(f"Found schema '{base_name}' after stripping suffix '{suffix}'")
                    referenced_node_data = context.raw_spec_schemas[base_name]
                    break

        if referenced_node_data is None:
            logger.warning(f"Missing reference '{ref_value}' for schema '{ref_name}'")
            return handle_missing_ref(ref_value, ref_name, context, max_depth, _parse_schema)

    # Standard parsing path for a new schema
    # logger.debug(f"Parsing new schema '{actual_schema_name}'")
    schema = parse_new_schema(actual_schema_name, dict(referenced_node_data), context, max_depth, _parse_schema)

    # Store the schema under the requested reference name if different
    # Don't mutate the original schema name to avoid affecting other references
    if schema.name != ref_name:
        context.parsed_schemas[ref_name] = schema

    return schema
