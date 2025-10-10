"""
Module for handling stripped suffix fallback strategy.
"""

import logging
from typing import Any, Callable, Mapping

from pyopenapi_gen.ir import IRSchema

from ....context import ParsingContext

logger = logging.getLogger(__name__)


def try_stripped_suffix_fallback(
    ref_name: str,
    ref_value: str,
    context: ParsingContext,
    max_depth: int,
    parse_fn: Callable[[str | None, Mapping[str, Any] | None, ParsingContext, int], IRSchema],
) -> IRSchema | None:
    """
    Attempts to resolve a reference by stripping common suffixes.

    Contracts:
        Pre-conditions:
            - ref_name must be a valid schema name
            - parse_fn must be a callable that parses schemas
            - context must be a valid ParsingContext instance
        Post-conditions:
            - If successful, returns the resolved IRSchema
            - If unsuccessful, returns None
            - Successful resolutions are added to context.parsed_schemas
    """
    suffixes = ["Response", "Request", "Input", "Output"]

    for suffix in suffixes:
        if ref_name.endswith(suffix):
            base_name = ref_name[: -len(suffix)]
            referenced_node_data_fallback = context.raw_spec_schemas.get(base_name)

            if referenced_node_data_fallback:
                resolved_schema = parse_fn(base_name, referenced_node_data_fallback, context, max_depth)
                if not resolved_schema._from_unresolved_ref:
                    warning_msg = f"Resolved $ref: {ref_value} by falling back to base name '{base_name}'."
                    context.collected_warnings.append(warning_msg)

                    context.parsed_schemas[ref_name] = resolved_schema
                    return resolved_schema

    return None
