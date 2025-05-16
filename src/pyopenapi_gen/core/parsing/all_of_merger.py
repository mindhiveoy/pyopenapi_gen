"""
Handles the 'allOf' keyword in an OpenAPI schema, merging properties and required fields.
"""

from __future__ import annotations

import os
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext

# Get maximum recursion depth from environment variable or default to 100
ENV_MAX_DEPTH = int(os.environ.get('PYOPENAPI_MAX_DEPTH', '100'))

# The _parse_schema_func will be _parse_schema from schema_parser.py, passed as an argument.


def _process_all_of(
    node: Mapping[str, Any],  # The schema node containing 'allOf'
    current_schema_name: Optional[str],  # Name of the current schema being processed (for context in recursive calls)
    context: ParsingContext,  # The global parsing context
    _parse_schema_func: Callable[  # The main schema parsing function
        [Optional[str], Optional[Mapping[str, Any]], ParsingContext, Optional[int]], IRSchema
    ],
    max_depth: int = ENV_MAX_DEPTH,  # Maximum recursion depth to prevent infinite loops
) -> Tuple[Dict[str, IRSchema], Set[str], List[IRSchema]]:
    """
    Processes the 'allOf' keyword in a schema node.

    Merges properties and required fields from all sub-schemas listed in 'allOf'
    and also from any direct 'properties' defined at the same level as 'allOf'.

    Args:
        node: The schema node, expected to contain an 'allOf' key.
        current_schema_name: The name of the schema being processed (e.g., "ComposedSchema").
        context: The parsing context.
        _parse_schema_func: A callable (typically _parse_schema itself) to parse sub-schemas.

    Returns:
        A tuple containing:
        - merged_properties: A dictionary of property names to their IRSchema.
        - merged_required: A set of required property names.
        - parsed_all_of_components: A list of IRSchema objects for each item in the 'allOf' array.
    """
    parsed_all_of_components: List[IRSchema] = []
    # Initialize with required fields from the current node level (if any)
    # This ensures that 'required' fields defined alongside 'allOf' are included.
    merged_required: Set[str] = set(node.get("required", []))
    merged_properties: Dict[str, IRSchema] = {}

    if "allOf" not in node:
        # This function should ideally only be called if 'allOf' is present.
        # However, if called without it, process direct properties if any.
        current_node_direct_properties = node.get("properties", {})
        for prop_name, prop_data in current_node_direct_properties.items():
            prop_schema_name_context = f"{current_schema_name}.{prop_name}" if current_schema_name else prop_name
            # Direct properties override any previous (though none in this branch)
            merged_properties[prop_name] = _parse_schema_func(prop_schema_name_context, prop_data, context)
        return merged_properties, merged_required, parsed_all_of_components

    for sub_node in node["allOf"]:
        # Sub-schemas in allOf are typically anonymous in the context of allOf processing itself.
        # Their names are resolved if they are $refs by _parse_schema_func.
        sub_schema_ir = _parse_schema_func(None, sub_node, context)
        parsed_all_of_components.append(sub_schema_ir)

        if sub_schema_ir.properties:
            for prop_name, prop_schema_val in sub_schema_ir.properties.items():
                # First one wins for properties from allOf components
                if prop_name not in merged_properties:
                    merged_properties[prop_name] = prop_schema_val
        if sub_schema_ir.required:
            merged_required.update(sub_schema_ir.required)

    # Properties defined directly in the node (sibling to 'allOf') override those from 'allOf'.
    current_node_direct_properties = node.get("properties", {})
    for prop_name, prop_data in current_node_direct_properties.items():
        prop_schema_name_context = f"{current_schema_name}.{prop_name}" if current_schema_name else prop_name
        # Direct properties override
        merged_properties[prop_name] = _parse_schema_func(prop_schema_name_context, prop_data, context)

    return merged_properties, merged_required, parsed_all_of_components
