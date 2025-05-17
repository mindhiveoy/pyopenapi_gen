"""
Parser for 'anyOf' keyword in OpenAPI schemas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, List, Mapping, Optional, Tuple

from pyopenapi_gen import IRSchema  # Main IR model
from ..context import ParsingContext  # Context object - MOVED

if TYPE_CHECKING:
    # from ..context import ParsingContext # No longer here
    # No direct import of _parse_schema from schema_parser to avoid circularity
    pass


def _parse_any_of_schemas(
    any_of_nodes: List[Mapping[str, Any]],
    context: ParsingContext,
    max_depth: int,
    parse_fn: Callable[  # Accepts the main schema parsing function
        [Optional[str], Optional[Mapping[str, Any]], ParsingContext, int], IRSchema
    ],
) -> tuple[Optional[List[IRSchema]], bool, Optional[str]]:
    """Parses 'anyOf' sub-schemas using a provided parsing function.

    Contracts:
        Pre-conditions:
            - any_of_nodes is a list of schema node mappings.
            - context is a valid ParsingContext instance.
            - max_depth >= 0.
            - parse_fn is a callable that can parse a schema node.
        Post-conditions:
            - Returns a tuple: (parsed_schemas, is_nullable, effective_schema_type)
            - parsed_schemas: List of IRSchema for non-null sub-schemas, or None.
            - is_nullable: True if a null type was present.
            - effective_schema_type: Potential schema_type if list becomes empty/None (currently always None).
    """
    assert isinstance(any_of_nodes, list), "any_of_nodes must be a list"
    assert all(isinstance(n, Mapping) for n in any_of_nodes), "all items in any_of_nodes must be Mappings"
    assert isinstance(context, ParsingContext), "context must be a ParsingContext instance"
    assert max_depth >= 0, "max_depth must be non-negative"
    assert callable(parse_fn), "parse_fn must be a callable"

    parsed_schemas_list: List[IRSchema] = []  # Renamed to avoid confusion with module name
    is_nullable_from_any_of = False
    effective_schema_type: Optional[str] = None

    for sub_node in any_of_nodes:
        if isinstance(sub_node, dict) and sub_node.get("type") == "null":
            is_nullable_from_any_of = True
            continue

        parsed_schemas_list.append(parse_fn(None, sub_node, context, max_depth))

    filtered_schemas = [
        s
        for s in parsed_schemas_list
        if not (
            s.type is None
            and not s.properties
            and not s.items
            and not s.enum
            and not s.any_of
            and not s.one_of
            and not s.all_of
        )
    ]

    if not filtered_schemas:
        effective_schema_type = None
        return None, is_nullable_from_any_of, effective_schema_type

    return filtered_schemas, is_nullable_from_any_of, effective_schema_type


# ... existing code ...
