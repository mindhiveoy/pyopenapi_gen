"""
Module for handling missing schema references.
"""

import logging
from typing import Any, Callable, Mapping, Optional

from pyopenapi_gen.ir import IRSchema

from ....context import ParsingContext
from .list_response import try_list_response_fallback
from .stripped_suffix import try_stripped_suffix_fallback

logger = logging.getLogger(__name__)


def handle_missing_ref(
    ref_value: str,
    ref_name: str,
    context: ParsingContext,
    max_depth: int,
    parse_fn: Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema],
) -> IRSchema:
    """
    Handles a missing schema reference by attempting fallback strategies.

    Contracts:
        Pre-conditions:
            - ref_value must be a valid reference string
            - ref_name must be a valid schema name
            - context must be a valid ParsingContext instance
            - max_depth must be a non-negative integer
            - parse_fn must be a callable that parses schemas
        Post-conditions:
            - Returns a valid IRSchema instance
            - The schema is registered in context.parsed_schemas
            - If no fallback succeeds, returns an unresolved schema
    """
    # Try ListResponse fallback
    list_response_schema = try_list_response_fallback(ref_name, ref_value, context, max_depth, parse_fn)
    if list_response_schema is not None:
        return list_response_schema

    # Try stripped suffix fallback
    stripped_schema = try_stripped_suffix_fallback(ref_name, ref_value, context, max_depth, parse_fn)
    if stripped_schema is not None:
        return stripped_schema

    # If all fallbacks fail, create an unresolved schema
    unresolved_schema = IRSchema(name=ref_name, _from_unresolved_ref=True)
    context.parsed_schemas[ref_name] = unresolved_schema
    return unresolved_schema
