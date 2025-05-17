"""
Module for handling direct cycle detection.
"""

import logging

from pyopenapi_gen.ir import IRSchema

from ....context import ParsingContext

logger = logging.getLogger(__name__)


def handle_direct_cycle(ref_name: str, context: ParsingContext) -> IRSchema:
    """
    Handles a direct cycle in schema references.

    Contracts:
        Pre-conditions:
            - ref_name must be a valid schema name
            - context must be a valid ParsingContext instance
            - ref_name must exist in context.parsed_schemas
        Post-conditions:
            - Returns the existing schema from context.parsed_schemas
            - The schema's _from_unresolved_ref flag is set to True
            - The schema's _is_circular_ref flag is set to True (for harmonized cycle detection)
    """
    existing_schema = context.parsed_schemas[ref_name]
    existing_schema._from_unresolved_ref = True
    existing_schema._is_circular_ref = True  # Harmonize with cycle detection contract
    context.cycle_detected = True  # Mark cycle in context
    logger.debug(f"Direct cycle detected for schema '{ref_name}'")
    return existing_schema
