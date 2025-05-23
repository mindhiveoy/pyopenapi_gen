"""
Module for handling ListResponse fallback strategy.
"""

import logging
from typing import Any, Callable, Mapping, Optional

from pyopenapi_gen.ir import IRSchema

from ....context import ParsingContext

logger = logging.getLogger(__name__)


def try_list_response_fallback(
    ref_name: str,
    ref_value: str,
    context: ParsingContext,
    max_depth: int,
    parse_fn: Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema],
) -> Optional[IRSchema]:
    """
    Attempts to resolve a reference by treating it as a list of a base type.

    Contracts:
        Pre-conditions:
            - ref_name must end with "ListResponse"
            - parse_fn must be a callable that parses schemas
            - context must be a valid ParsingContext instance
        Post-conditions:
            - If successful, returns an array IRSchema with items of the base type
            - If unsuccessful, returns None
            - Successful resolutions are added to context.parsed_schemas
    """
    list_response_suffix = "ListResponse"
    if not ref_name.endswith(list_response_suffix):
        return None

    base_name = ref_name[: -len(list_response_suffix)]
    referenced_node_data_fallback = context.raw_spec_schemas.get(base_name)

    if not referenced_node_data_fallback:
        return None

    item_schema = parse_fn(base_name, referenced_node_data_fallback, context, max_depth)
    if item_schema._from_unresolved_ref:
        return None

    warning_msg = f"Resolved $ref: {ref_value} by falling back to LIST of base name '{base_name}'."
    context.collected_warnings.append(warning_msg)

    resolved_schema = IRSchema(name=ref_name, type="array", items=item_schema)
    context.parsed_schemas[ref_name] = resolved_schema
    return resolved_schema
