"""
Dedicated parser for resolving $ref values to IRSchema objects.
"""

from __future__ import annotations

import copy
import os
import warnings
from typing import Any, Dict, List, Mapping, Optional  # Ensure all necessary types are here

from pyopenapi_gen import IRSchema

from .context import ParsingContext

# Get maximum recursion depth from environment variable or default to 100
ENV_MAX_DEPTH = int(os.environ.get('PYOPENAPI_MAX_DEPTH', '100'))

# DO NOT import _parse_schema at module level to avoid cycle
# from .schema_parser import _parse_schema


def _resolve_schema_ref(
    ref_value: str, current_schema_name_for_context: Optional[str], context: ParsingContext, max_depth: int = ENV_MAX_DEPTH
) -> IRSchema:
    """Resolves a $ref string to an IRSchema, handling cycles and fallbacks."""
    # Local import to break circular dependency
    from .schema_parser import _parse_schema
    import logging

    logger = logging.getLogger(__name__)

    if ref_value.startswith("#/components/schemas/"):
        ref_name = ref_value.rsplit("/", 1)[-1]

        # Enhanced cycle detection - check if ref is already in parsing path
        if ref_name in context.currently_parsing:
            cycle_path = " -> ".join(context.parsing_path + [ref_name])
            logger.warning(f"CYCLE DETECTED in _resolve_schema_ref: {cycle_path}")
            context.cycle_detected = True

            # Return a placeholder schema that indicates the circular reference
            circular_schema = IRSchema(
                name=ref_name,
                type="object",  # Assume object type for circular references
                description=f"[Circular reference detected: {cycle_path}]",
                _is_circular_ref=True,
                _circular_ref_path=cycle_path
            )

            # Store in parsed_schemas to prevent future cycles
            context.parsed_schemas[ref_name] = circular_schema
            return circular_schema

        # If schema is already parsed, return it
        if ref_name in context.parsed_schemas:
            return context.parsed_schemas[ref_name]

        # Legacy cycle detection using visited_refs
        if ref_name in context.visited_refs:
            logger.warning(f"CYCLE DETECTED (legacy visited_refs): {ref_name}")
            # Create and store a stub schema to break the cycle
            stub_schema = IRSchema(
                name=ref_name,
                _is_circular_ref=True,
                _circular_ref_path=f"Legacy visited_refs detection: {ref_name}"
            )
            context.parsed_schemas[ref_name] = stub_schema
            return stub_schema

        # Mark as visited for cycle detection
        context.visited_refs.add(ref_name)
        referenced_node_data = context.raw_spec_schemas.get(ref_name)
        resolved_schema_object = None

        if referenced_node_data is None:
            original_ref_name_for_fallback = ref_name
            list_response_suffix = "ListResponse"
            if ref_name.endswith(list_response_suffix):
                base_name = ref_name[: -len(list_response_suffix)]
                referenced_node_data_fallback = context.raw_spec_schemas.get(base_name)
                if referenced_node_data_fallback:
                    warning_msg = f"Resolved $ref: {ref_value} by falling back to LIST of base name '{base_name}'."
                    context.collected_warnings.append(warning_msg)
                    logger.info(warning_msg)
                    item_schema = _parse_schema(base_name, referenced_node_data_fallback, context, max_depth=max_depth)
                    if not item_schema._from_unresolved_ref:
                        resolved_schema_object = IRSchema(
                            name=original_ref_name_for_fallback, type="array", items=item_schema
                        )
                        context.parsed_schemas[original_ref_name_for_fallback] = resolved_schema_object

            if resolved_schema_object is None:
                stripped_name = ref_name
                for suffix in ["Response", "Create", "Update", "Request", "Input", "Output", "Data"]:
                    if stripped_name.endswith(suffix):
                        stripped_name = stripped_name[: -len(suffix)]
                        break

                if stripped_name != ref_name:
                    referenced_node_data_fallback = context.raw_spec_schemas.get(stripped_name)
                    if referenced_node_data_fallback:
                        warning_msg = f"Resolved $ref: {ref_value} by falling back to stripped name '{stripped_name}'."
                        context.collected_warnings.append(warning_msg)
                        logger.info(warning_msg)
                        base_schema_structure = _parse_schema(stripped_name, referenced_node_data_fallback, context, max_depth=max_depth)
                        if not base_schema_structure._from_unresolved_ref:
                            resolved_schema_object = copy.deepcopy(base_schema_structure)
                            resolved_schema_object.name = original_ref_name_for_fallback
                            context.parsed_schemas[original_ref_name_for_fallback] = resolved_schema_object
                        else:
                            resolved_schema_object = IRSchema(
                                name=original_ref_name_for_fallback, _from_unresolved_ref=True
                            )
                            context.parsed_schemas[original_ref_name_for_fallback] = resolved_schema_object

            if resolved_schema_object is None:
                warning_msg = f"Could not resolve $ref: {ref_value}. ref_name='{ref_name}'. Available (10): {list(context.raw_spec_schemas.keys())[:10]}..."
                context.collected_warnings.append(warning_msg)
                logger.warning(warning_msg)
                context.visited_refs.remove(ref_name)
                return IRSchema(name=ref_name, _from_unresolved_ref=True)
            else:
                context.visited_refs.remove(original_ref_name_for_fallback)
                return resolved_schema_object

        # Create stub schema before parsing to break potential cycles
        stub_schema = IRSchema(name=ref_name)
        context.parsed_schemas[ref_name] = stub_schema

        # Now parse the actual schema
        schema_obj_from_ref = _parse_schema(ref_name, referenced_node_data, context, max_depth=max_depth)

        # Replace stub with actual parsed schema
        context.parsed_schemas[ref_name] = schema_obj_from_ref

        context.visited_refs.remove(ref_name)
        return schema_obj_from_ref

    else:
        warning_msg = f"Unsupported or invalid $ref format: {ref_value}"
        context.collected_warnings.append(warning_msg)
        return IRSchema(name=current_schema_name_for_context, _from_unresolved_ref=True)
