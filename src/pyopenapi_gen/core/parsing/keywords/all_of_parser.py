"""
Handles the 'allOf' keyword in an OpenAPI schema, merging properties and required fields.
Renamed from all_of_merger to all_of_parser for consistency.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Callable, List, Mapping, Set, Tuple

from pyopenapi_gen import IRSchema

from ..context import ParsingContext

ENV_MAX_DEPTH = int(os.environ.get("PYOPENAPI_MAX_DEPTH", "100"))

if TYPE_CHECKING:
    pass


def _process_all_of(
    node: Mapping[str, Any],
    current_schema_name: str | None,
    context: ParsingContext,
    _parse_schema_func: Callable[[str | None, Mapping[str, Any] | None, ParsingContext, int | None], IRSchema],
    max_depth: int = ENV_MAX_DEPTH,
) -> Tuple[dict[str, IRSchema], Set[str], List[IRSchema]]:
    """Processes the 'allOf' keyword in a schema node.

    Merges properties and required fields from all sub-schemas listed in 'allOf'
    and also from any direct 'properties' defined at the same level as 'allOf'.

    Contracts:
        Pre-conditions:
            - node is a non-empty mapping representing an OpenAPI schema node.
            - context is a valid ParsingContext instance.
            - _parse_schema_func is a callable function.
            - max_depth is a non-negative integer.
        Post-conditions:
            - Returns a tuple containing:
                - merged_properties: Dict of property names to IRSchema.
                - merged_required: Set of required property names.
                - parsed_all_of_components: List of IRSchema for each item in 'allOf' (empty if 'allOf' not present).
    """
    # Pre-conditions
    if not (isinstance(node, Mapping) and node):
        raise TypeError("node must be a non-empty Mapping")
    if not isinstance(context, ParsingContext):
        raise TypeError("context must be a ParsingContext instance")
    if not callable(_parse_schema_func):
        raise TypeError("_parse_schema_func must be callable")
    if not (isinstance(max_depth, int) and max_depth >= 0):
        raise ValueError("max_depth must be a non-negative integer")

    parsed_all_of_components: List[IRSchema] = []
    merged_required: Set[str] = set(node.get("required", []))
    merged_properties: dict[str, IRSchema] = {}

    if "allOf" not in node:
        current_node_direct_properties = node.get("properties", {})
        for prop_name, prop_data in current_node_direct_properties.items():
            prop_schema_name_context = f"{current_schema_name}.{prop_name}" if current_schema_name else prop_name
            merged_properties[prop_name] = _parse_schema_func(prop_schema_name_context, prop_data, context, max_depth)
        return merged_properties, merged_required, parsed_all_of_components

    for sub_node in node["allOf"]:
        sub_schema_ir = _parse_schema_func(None, sub_node, context, max_depth)
        parsed_all_of_components.append(sub_schema_ir)
        if sub_schema_ir.properties:
            for prop_name, prop_schema_val in sub_schema_ir.properties.items():
                if prop_name not in merged_properties:
                    merged_properties[prop_name] = prop_schema_val
        if sub_schema_ir.required:
            merged_required.update(sub_schema_ir.required)

    current_node_direct_properties = node.get("properties", {})
    for prop_name, prop_data in current_node_direct_properties.items():
        prop_schema_name_context = f"{current_schema_name}.{prop_name}" if current_schema_name else prop_name
        merged_properties[prop_name] = _parse_schema_func(prop_schema_name_context, prop_data, context, max_depth)

    return merged_properties, merged_required, parsed_all_of_components
