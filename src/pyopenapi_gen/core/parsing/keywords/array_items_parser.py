"""
Dedicated parser for handling 'items' within an array schema.
Renamed from array_parser.py for clarity.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Mapping, Optional

from pyopenapi_gen import IRSchema

from ..context import ParsingContext

if TYPE_CHECKING:
    # from pyopenapi_gen import IRSchema # Already above or handled by context
    # from ..context import ParsingContext # No longer here
    pass


def _parse_array_items_schema(
    parent_schema_name: Optional[str],
    items_node_data: Mapping[str, Any],
    context: ParsingContext,
    parse_fn: Callable[  # Accepts the main schema parsing function
        [Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema
    ],
    max_depth: int,
) -> Optional[IRSchema]:
    """Parses the 'items' sub-schema of an array.

    Args:
        parent_schema_name: The name of the parent array schema (if any).
        items_node_data: The raw dictionary of the 'items' schema.
        context: The parsing context.
        parse_fn: The main schema parsing function to call recursively (_parse_schema from schema_parser.py).
        max_depth: Maximum recursion depth.

    Returns:
        The parsed IRSchema for the items, or None if items_node_data is not suitable.

    Contracts:
        Pre-conditions:
            - items_node_data is a mapping representing the items schema.
            - context is a valid ParsingContext instance.
            - parse_fn is a callable function.
            - max_depth is a non-negative integer.
        Post-conditions:
            - Returns an IRSchema if items_node_data is a valid schema mapping.
            - Returns None if items_node_data is not a mapping.
            - Calls parse_fn with an appropriate name for the item schema.
    """
    # Pre-conditions
    # items_node_data is checked later, as it can be non-Mapping to return None
    assert isinstance(context, ParsingContext), "context must be a ParsingContext instance"
    assert callable(parse_fn), "parse_fn must be callable"
    assert isinstance(max_depth, int) and max_depth >= 0, "max_depth must be a non-negative integer"

    item_name_for_parse = f"{parent_schema_name}Item" if parent_schema_name else None
    if (
        isinstance(items_node_data, dict)
        and "$ref" in items_node_data
        and items_node_data["$ref"].startswith("#/components/schemas/")
    ):
        item_name_for_parse = items_node_data["$ref"].split("/")[-1]

    if not isinstance(items_node_data, Mapping):
        return None

    return parse_fn(item_name_for_parse, items_node_data, context, max_depth)
