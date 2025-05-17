"""
Module for handling new schema references.
"""

import logging
from typing import Any, Callable, Dict, Mapping, Optional

from pyopenapi_gen.ir import IRSchema

from ....context import ParsingContext
from .cyclic_properties import mark_cyclic_property_references

logger = logging.getLogger(__name__)


def parse_new_schema(
    ref_name: str,
    node_data: Dict[str, Any],
    context: ParsingContext,
    max_depth: int,
    parse_fn: Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema],
) -> IRSchema:
    """
    Parses a new schema from raw data.

    Contracts:
        Pre-conditions:
            - ref_name must be a valid schema name not already fully parsed
            - node_data must contain raw schema definition
            - parse_fn must be a callable that parses schemas
            - context must be a valid ParsingContext instance
        Post-conditions:
            - Returns a valid parsed IRSchema instance
            - The schema is registered in context.parsed_schemas
            - Cyclic property references are marked correctly
    """
    # Create stub to prevent infinite recursion during parsing
    stub_schema = IRSchema(name=ref_name)
    context.parsed_schemas[ref_name] = stub_schema

    # Parse the actual schema
    schema_obj = parse_fn(ref_name, node_data, context, max_depth)

    # Update the entry in parsed_schemas with the fully parsed schema
    context.parsed_schemas[ref_name] = schema_obj

    # Mark any property references involved in cycles
    mark_cyclic_property_references(schema_obj, ref_name, context)

    return schema_obj
