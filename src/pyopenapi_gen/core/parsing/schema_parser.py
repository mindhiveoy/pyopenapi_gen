"""
Core schema parsing logic, transforming a schema node into an IRSchema object.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple

from pyopenapi_gen import IRSchema
from pyopenapi_gen.core.utils import NameSanitizer

from .context import ParsingContext
from .cycle_helpers import _handle_cycle_detection, _handle_max_depth_exceeded
from .keywords.all_of_parser import _process_all_of
from .keywords.any_of_parser import _parse_any_of_schemas
from .keywords.one_of_parser import _parse_one_of_schemas

# Environment variables for configurable limits, with defaults
try:
    MAX_CYCLES = int(os.environ.get("PYOPENAPI_MAX_CYCLES", "0"))  # Default 0 means no explicit cycle count limit
except ValueError:
    MAX_CYCLES = 0
try:
    ENV_MAX_DEPTH = int(os.environ.get("PYOPENAPI_MAX_DEPTH", "150"))  # Default 150
except ValueError:
    ENV_MAX_DEPTH = 150  # Fallback to 150 if env var is invalid
PYOPENAPI_DEBUG_CYCLES = os.environ.get("PYOPENAPI_DEBUG_CYCLES", "0") == "1"

logger = logging.getLogger(__name__)


def _resolve_ref(
    ref_path_str: str,
    parent_schema_name: Optional[str],  # Name of the schema containing this $ref
    context: ParsingContext,
    max_depth_override: Optional[int],  # Propagated from the main _parse_schema call
    allow_self_reference_for_parent: bool,
) -> IRSchema:
    """Resolves a $ref string, handling cycles and depth for the referenced schema."""
    ref_name_parts = ref_path_str.split("/")
    if not (ref_name_parts and ref_name_parts[-1]):
        logger.warning(
            f"Malformed $ref path '{ref_path_str}' encountered while parsing parent '{parent_schema_name or 'anonymous'}'."
        )
        return IRSchema(
            name=None,  # Anonymous placeholder for a bad ref
            description=f"Malformed $ref: {ref_path_str}",
            _from_unresolved_ref=True,
        )
    ref_name = ref_name_parts[-1]

    # 1. Check if already parsed (fully or as a placeholder)
    if ref_name in context.parsed_schemas and not context.parsed_schemas[ref_name]._max_depth_exceeded_marker:
        logger.debug(
            f"Re-using already parsed schema '{ref_name}' (not a depth placeholder) from context while resolving for '{parent_schema_name or 'anonymous'}'."
        )
        return context.parsed_schemas[ref_name]

    # 2. Get the raw schema node for the reference
    ref_node = context.raw_spec_schemas.get(ref_name)
    if ref_node is None:
        logger.warning(
            f"Cannot resolve $ref '{ref_path_str}' for parent '{parent_schema_name or 'anonymous'}'. Target '{ref_name}' not in raw_spec_schemas. Returning placeholder."
        )
        return IRSchema(
            name=NameSanitizer.sanitize_class_name(ref_name),
            _from_unresolved_ref=True,
            description=f"Unresolved $ref: {ref_path_str} (target not found)",
        )

    # 3. Enter context for the referenced schema
    is_cycle, cycle_path_for_ref = context.enter_schema(ref_name)

    try:  # Ensure exit_schema is called for ref_name
        # 4. Max depth check specifically for entering this ref_name
        if context.recursion_depth > ENV_MAX_DEPTH:
            return _handle_max_depth_exceeded(ref_name, context, ENV_MAX_DEPTH)

        # 5. Cycle check specifically for entering this ref_name
        if is_cycle:
            assert cycle_path_for_ref is not None, "Cycle path must be populated if is_cycle is True for ref"
            # If A refers to B, and B refers to A (or A->B->C->A):
            # When resolving B from A, if B is already in currently_parsing (due to A itself or an earlier part of A's parse path),
            # then it's a cycle. `allow_self_reference_for_parent` is about whether A can refer to A directly.
            # The new `allow_self_reference` for the _parse_schema call for `ref_name` should be True if `ref_name` IS the `parent_schema_name`.
            is_direct_self_ref_for_component = ref_name == parent_schema_name
            return _handle_cycle_detection(
                ref_name,
                cycle_path_for_ref,
                context,
                allow_self_reference_for_parent or is_direct_self_ref_for_component,
            )

        # 6. Recursively parse the referenced schema node
        # The `allow_self_reference` for this call should be true if the ref_name is the same as the parent_schema_name (direct recursion)
        # or if the original call to parse the parent allowed self-references generally.
        return _parse_schema(
            ref_name,
            ref_node,
            context,
            max_depth_override,
            allow_self_reference=(allow_self_reference_for_parent or (ref_name == parent_schema_name)),
        )

    finally:
        # 8. Exit context for the referenced schema
        context.exit_schema(ref_name)


def _parse_composition_keywords(
    node: Mapping[str, Any],
    name: Optional[str],
    context: ParsingContext,
    max_depth: int,
    parse_fn: Callable[[Optional[str], Optional[Mapping[str, Any]], ParsingContext, Optional[int]], IRSchema],
) -> Tuple[
    Optional[List[IRSchema]], Optional[List[IRSchema]], Optional[List[IRSchema]], Dict[str, IRSchema], Set[str], bool
]:
    """Parse composition keywords (anyOf, oneOf, allOf) from a schema node.

    Contracts:
        Pre-conditions:
            - node is a valid Mapping
            - context is a valid ParsingContext instance
            - max_depth >= 0
            - parse_fn is a callable for parsing schemas
        Post-conditions:
            - Returns a tuple of (any_of_schemas, one_of_schemas, all_of_components, properties, required_fields, is_nullable)
    """
    any_of_schemas: Optional[List[IRSchema]] = None
    one_of_schemas: Optional[List[IRSchema]] = None
    parsed_all_of_components: Optional[List[IRSchema]] = None
    merged_properties: Dict[str, IRSchema] = {}
    merged_required_set: Set[str] = set()
    is_nullable: bool = False

    if "anyOf" in node:
        parsed_sub_schemas, nullable_from_sub, _ = _parse_any_of_schemas(node["anyOf"], context, max_depth, parse_fn)
        any_of_schemas = parsed_sub_schemas
        is_nullable = is_nullable or nullable_from_sub

    if "oneOf" in node:
        parsed_sub_schemas, nullable_from_sub, _ = _parse_one_of_schemas(node["oneOf"], context, max_depth, parse_fn)
        one_of_schemas = parsed_sub_schemas
        is_nullable = is_nullable or nullable_from_sub

    if "allOf" in node:
        merged_properties, merged_required_set, parsed_all_of_components = _process_all_of(
            node, name, context, parse_fn, max_depth=max_depth
        )
    else:
        merged_required_set = set(node.get("required", []))

    return any_of_schemas, one_of_schemas, parsed_all_of_components, merged_properties, merged_required_set, is_nullable


def _parse_properties(
    properties_node: Mapping[str, Any],
    parent_schema_name: Optional[str],
    existing_properties: Dict[str, IRSchema],  # Properties already merged, e.g., from allOf
    context: ParsingContext,
    max_depth_override: Optional[int],
    allow_self_reference: bool,
) -> Dict[str, IRSchema]:
    """Parses the 'properties' block of a schema node."""
    parsed_props: Dict[str, IRSchema] = existing_properties.copy()

    for prop_name, prop_schema_node in properties_node.items():
        if not isinstance(prop_name, str) or not prop_name:
            logger.warning(
                f"Skipping property with invalid name '{prop_name}' in schema '{parent_schema_name or 'anonymous'}'."
            )
            continue

        if prop_name in parsed_props:  # Already handled by allOf or a previous definition, skip
            continue

        if isinstance(prop_schema_node, Mapping) and "$ref" in prop_schema_node:
            parsed_props[prop_name] = _resolve_ref(
                prop_schema_node["$ref"], parent_schema_name, context, max_depth_override, allow_self_reference
            )
        else:
            # Inline object promotion or direct parsing of property schema
            is_inline_object_node = (
                isinstance(prop_schema_node, Mapping)
                and prop_schema_node.get("type") == "object"
                and "$ref" not in prop_schema_node
                and (
                    "properties" in prop_schema_node or "description" in prop_schema_node
                )  # Heuristic for actual object def
            )

            if is_inline_object_node and parent_schema_name:
                # Promote inline object to its own schema
                promoted_schema_name = f"{parent_schema_name}{NameSanitizer.sanitize_class_name(prop_name)}"
                promoted_ir_schema = _parse_schema(
                    promoted_schema_name,
                    prop_schema_node,  # type: ignore
                    context,
                    max_depth_override,
                    allow_self_reference,
                )
                # The property itself becomes a reference to this new schema
                property_ref_ir = IRSchema(
                    name=prop_name,  # The actual property name
                    type=promoted_ir_schema.name,  # Type is the name of the promoted schema
                    description=promoted_ir_schema.description or prop_schema_node.get("description"),  # type: ignore
                    is_nullable=prop_schema_node.get("nullable", False) or promoted_ir_schema.is_nullable,  # type: ignore
                    _refers_to_schema=promoted_ir_schema,
                    default=prop_schema_node.get("default"),  # type: ignore
                    example=prop_schema_node.get("example"),  # type: ignore
                )
                parsed_props[prop_name] = property_ref_ir
                # Add the newly created promoted schema to parsed_schemas if it's not a placeholder from error/cycle
                if (
                    promoted_schema_name
                    and not promoted_ir_schema._from_unresolved_ref
                    and not promoted_ir_schema._max_depth_exceeded_marker
                    and not promoted_ir_schema._is_circular_ref
                ):
                    context.parsed_schemas[promoted_schema_name] = promoted_ir_schema
            else:
                # Directly parse other inline types (string, number, array of simple types, etc.)
                # or objects that are not being promoted (e.g. if parent_schema_name is None)
                # Use a sanitized version of prop_name as context name for this sub-parse if no better name exists.
                prop_context_name = NameSanitizer.sanitize_class_name(prop_name)
                parsed_prop_schema_ir = _parse_schema(
                    prop_context_name,  # Contextual name for this sub-parse
                    prop_schema_node,  # type: ignore
                    context,
                    max_depth_override,
                    allow_self_reference,
                )
                # If the parsed schema retained the contextual name and it was registered,
                # it implies it might be a complex anonymous type that got registered.
                # In such cases, the property should *refer* to it.
                # Otherwise, the parsed_prop_schema_ir *is* the property's schema directly.
                if (
                    parsed_prop_schema_ir.name == prop_context_name
                    and context.is_schema_parsed(prop_context_name)
                    and context.get_parsed_schema(prop_context_name) is parsed_prop_schema_ir
                    and (parsed_prop_schema_ir.type == "object" or parsed_prop_schema_ir.type == "array")
                    and not parsed_prop_schema_ir._from_unresolved_ref
                    and not parsed_prop_schema_ir._max_depth_exceeded_marker
                    and not parsed_prop_schema_ir._is_circular_ref
                ):
                    prop_is_nullable = False
                    if isinstance(prop_schema_node, Mapping):
                        if "nullable" in prop_schema_node:
                            prop_is_nullable = prop_schema_node["nullable"]
                        elif isinstance(prop_schema_node.get("type"), list) and "null" in prop_schema_node["type"]:
                            prop_is_nullable = True
                    elif parsed_prop_schema_ir.is_nullable:
                        prop_is_nullable = True

                    property_holder_ir = IRSchema(
                        name=prop_name,  # The actual property name
                        type=parsed_prop_schema_ir.name,  # Type is the name of the (potentially registered) anonymous schema
                        description=prop_schema_node.get("description", parsed_prop_schema_ir.description),  # type: ignore
                        is_nullable=prop_is_nullable,
                        default=prop_schema_node.get("default"),  # type: ignore
                        example=prop_schema_node.get("example"),  # type: ignore
                        enum=prop_schema_node.get("enum") if not parsed_prop_schema_ir.enum else None,  # type: ignore
                        items=parsed_prop_schema_ir.items if parsed_prop_schema_ir.type == "array" else None,
                        format=parsed_prop_schema_ir.format,
                        _refers_to_schema=parsed_prop_schema_ir,
                    )
                    parsed_props[prop_name] = property_holder_ir
                else:
                    # Simpler type, or error placeholder. Assign directly but ensure original prop_name is used.
                    # Also, try to respect original node's description, default, example, nullable if available.
                    final_prop_ir = parsed_prop_schema_ir
                    final_prop_ir.name = prop_name  # Ensure the property name in the dict is the original key
                    if isinstance(prop_schema_node, Mapping):
                        final_prop_ir.description = prop_schema_node.get(
                            "description", parsed_prop_schema_ir.description
                        )
                        final_prop_ir.default = prop_schema_node.get("default", parsed_prop_schema_ir.default)
                        final_prop_ir.example = prop_schema_node.get("example", parsed_prop_schema_ir.example)
                        current_prop_node_nullable = prop_schema_node.get("nullable", False)
                        type_list_nullable = (
                            isinstance(prop_schema_node.get("type"), list) and "null" in prop_schema_node["type"]
                        )
                        final_prop_ir.is_nullable = (
                            final_prop_ir.is_nullable or current_prop_node_nullable or type_list_nullable
                        )
                        # If the sub-parse didn't pick up an enum (e.g. for simple types), take it from prop_schema_node
                        if not final_prop_ir.enum and "enum" in prop_schema_node:
                            final_prop_ir.enum = prop_schema_node["enum"]

                    parsed_props[prop_name] = final_prop_ir
    return parsed_props


def _parse_schema(
    schema_name: Optional[str],
    schema_node: Optional[Mapping[str, Any]],
    context: ParsingContext,
    max_depth_override: Optional[int] = None,
    allow_self_reference: bool = False,
) -> IRSchema:
    """
    Parse a schema node and return an IRSchema object.
    """
    # Pre-conditions
    assert context is not None, "Context cannot be None for _parse_schema"

    # Always call enter_schema to track depth and named cycles. This must be balanced by exit_schema.
    is_cycle, cycle_path_str = context.enter_schema(schema_name)

    try:  # Ensure exit_schema is called
        # Max depth check first, as it's a hard stop regardless of named cycles.
        # enter_schema() increments recursion_depth, so check it immediately after.
        if context.recursion_depth > ENV_MAX_DEPTH:
            # _handle_max_depth_exceeded now returns the placeholder IRSchema
            return _handle_max_depth_exceeded(schema_name, context, ENV_MAX_DEPTH)

        if is_cycle:
            assert schema_name is not None, "If is_cycle is True, schema_name must have been provided to enter_schema."
            assert cycle_path_str is not None, "If is_cycle is True, cycle_path_str must be populated."
            # _handle_cycle_detection returns the placeholder IRSchema
            return _handle_cycle_detection(schema_name, cycle_path_str, context, allow_self_reference)

        if schema_node is None:
            return IRSchema(name=NameSanitizer.sanitize_class_name(schema_name) if schema_name else None)

        assert isinstance(schema_node, Mapping), (
            f"Schema node for '{schema_name or 'anonymous'}' must be a Mapping (e.g., dict), got {type(schema_node)}"
        )

        # If the current schema_node itself is a $ref, resolve it.
        if "$ref" in schema_node:
            # schema_name is the original name we are trying to parse (e.g., 'Pet')
            # schema_node is {"$ref": "#/components/schemas/ActualPet"}
            # We want to resolve "ActualPet", but the resulting IRSchema should ideally retain the name 'Pet' if appropriate,
            # or _resolve_ref handles naming if ActualPet itself is parsed.
            # The `parent_schema_name` for _resolve_ref here is `schema_name` itself.
            return _resolve_ref(schema_node["$ref"], schema_name, context, max_depth_override, allow_self_reference)

        extracted_type: Optional[str] = None
        is_nullable_from_type_field = False
        raw_type_field = schema_node.get("type")

        if isinstance(raw_type_field, str):
            extracted_type = raw_type_field
        elif isinstance(raw_type_field, list):
            if "null" in raw_type_field:
                is_nullable_from_type_field = True
            non_null_types = [t for t in raw_type_field if t != "null"]
            if non_null_types:
                extracted_type = non_null_types[0]
                if len(non_null_types) > 1:
                    pass
            elif is_nullable_from_type_field:
                extracted_type = "null"

        any_of_irs, one_of_irs, all_of_components_irs, props_from_comp, req_from_comp, nullable_from_comp = (
            _parse_composition_keywords(
                schema_node,
                schema_name,
                context,
                ENV_MAX_DEPTH,
                lambda n, sn, c, md: _parse_schema(n, sn, c, md, allow_self_reference),
            )
        )

        is_nullable_overall = is_nullable_from_type_field or nullable_from_comp
        final_properties_for_ir: Dict[str, IRSchema] = {}
        current_final_type = extracted_type
        if not current_final_type:
            if props_from_comp or "allOf" in schema_node or "properties" in schema_node:
                current_final_type = "object"
            elif any_of_irs or one_of_irs:
                current_final_type = None

        if current_final_type == "null":
            current_final_type = None

        if current_final_type == "object":
            # Properties from allOf have already been handled by _parse_composition_keywords
            # and are in props_from_comp. We pass these as existing_properties.
            if "properties" in schema_node:
                final_properties_for_ir = _parse_properties(
                    schema_node["properties"],
                    schema_name,
                    props_from_comp,  # these are from allOf merge
                    context,
                    max_depth_override,
                    allow_self_reference,
                )
            else:
                final_properties_for_ir = props_from_comp.copy()  # No direct properties, only from allOf

            # final_required_set: Set[str] = set() # This was old logic, req_from_comp covers allOf
            # if "properties" in schema_node: # This loop is now inside _parse_properties effectively
            # ... existing property parsing loop removed ...
        final_required_fields_set = req_from_comp.copy()
        if "required" in schema_node and isinstance(schema_node["required"], list):
            final_required_fields_set.update(schema_node["required"])

        items_ir: Optional[IRSchema] = None
        if current_final_type == "array":
            items_node = schema_node.get("items")
            if items_node:
                base_name_for_item = schema_name or "AnonymousArray"
                item_schema_name_for_recursive_parse = NameSanitizer.sanitize_class_name(f"{base_name_for_item}Item")

                actual_item_ir = _parse_schema(
                    item_schema_name_for_recursive_parse, items_node, context, max_depth_override, allow_self_reference
                )

                is_promoted_inline_object = (
                    isinstance(items_node, Mapping)
                    and items_node.get("type") == "object"
                    and "$ref" not in items_node
                    and actual_item_ir.name == item_schema_name_for_recursive_parse
                )

                if is_promoted_inline_object:
                    ref_holder_ir = IRSchema(
                        name=None,
                        type=actual_item_ir.name,
                        description=actual_item_ir.description or items_node.get("description"),
                    )
                    ref_holder_ir._refers_to_schema = actual_item_ir
                    items_ir = ref_holder_ir
                else:
                    items_ir = actual_item_ir
            else:
                items_ir = IRSchema(type="Any")

        schema_ir_name_attr = NameSanitizer.sanitize_class_name(schema_name) if schema_name else None

        schema_ir = IRSchema(
            name=schema_ir_name_attr,
            type=current_final_type,
            properties=final_properties_for_ir,
            any_of=any_of_irs,
            one_of=one_of_irs,
            all_of=all_of_components_irs,
            required=sorted(list(final_required_fields_set)),
            description=schema_node.get("description"),
            format=schema_node.get("format") if isinstance(schema_node.get("format"), str) else None,
            enum=schema_node.get("enum") if isinstance(schema_node.get("enum"), list) else None,
            default=schema_node.get("default"),
            example=schema_node.get("example"),
            is_nullable=is_nullable_overall,
            items=items_ir,
        )

        if schema_ir.type == "array" and isinstance(schema_node.get("items"), Mapping):
            raw_items_node = schema_node["items"]
            item_schema_context_name_for_reparse: Optional[str]
            base_name_for_reparse_item = schema_name or "AnonymousArray"
            item_schema_context_name_for_reparse = NameSanitizer.sanitize_class_name(
                f"{base_name_for_reparse_item}Item"
            )

            direct_reparsed_item_ir = _parse_schema(
                item_schema_context_name_for_reparse, raw_items_node, context, max_depth_override, allow_self_reference
            )

            is_promoted_inline_object_in_reparse_block = (
                isinstance(raw_items_node, Mapping)
                and raw_items_node.get("type") == "object"
                and "$ref" not in raw_items_node
                and direct_reparsed_item_ir.name == item_schema_context_name_for_reparse
            )

            if is_promoted_inline_object_in_reparse_block:
                ref_holder_for_reparse_ir = IRSchema(
                    name=None,
                    type=direct_reparsed_item_ir.name,
                    description=direct_reparsed_item_ir.description or raw_items_node.get("description"),
                )
                ref_holder_for_reparse_ir._refers_to_schema = direct_reparsed_item_ir
                schema_ir.items = ref_holder_for_reparse_ir
            else:
                schema_ir.items = direct_reparsed_item_ir

        if schema_name and schema_name in context.parsed_schemas:
            existing_in_context = context.parsed_schemas[schema_name]

            if existing_in_context._is_circular_ref and existing_in_context is not schema_ir:
                return existing_in_context

        if schema_name:
            context.parsed_schemas[schema_name] = schema_ir

        if schema_name and not schema_ir._from_unresolved_ref and not schema_ir._max_depth_exceeded_marker:
            context.parsed_schemas[schema_name] = schema_ir

        # Ensure generation_name and final_module_stem are set if the schema has a name
        if schema_ir.name:
            schema_ir.generation_name = NameSanitizer.sanitize_class_name(schema_ir.name)
            schema_ir.final_module_stem = NameSanitizer.sanitize_module_name(schema_ir.name)

        return schema_ir

    finally:
        context.exit_schema(schema_name)
