"""
Module for handling existing schema references.
"""

from pyopenapi_gen.ir import IRSchema

from ....context import ParsingContext


def handle_existing_schema(ref_name: str, context: ParsingContext) -> IRSchema:
    """
    Handles an existing schema reference.

    Contracts:
        Pre-conditions:
            - ref_name must be a valid schema name
            - context must be a valid ParsingContext instance
            - ref_name must exist in context.parsed_schemas
        Post-conditions:
            - Returns the existing schema from context.parsed_schemas
    """
    return context.parsed_schemas[ref_name]
