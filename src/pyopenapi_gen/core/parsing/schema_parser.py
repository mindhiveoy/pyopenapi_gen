"""
Core schema parsing logic, transforming a schema node into an IRSchema object.
"""

from __future__ import annotations

import logging  # For logger
import os  # For environment variables
from typing import Any, Callable, Dict, List, Mapping, Optional, Set, Tuple, cast  # Ensure all types are here

from pyopenapi_gen import IRSchema  # Assuming IRSchema is in the root pyopenapi_gen package
from pyopenapi_gen.core.utils import NameSanitizer  # Added import

from .context import ParsingContext

# Import the new cycle_helpers module
from .cycle_helpers import _handle_cycle_detection, _handle_max_depth_exceeded
from .keywords.all_of_parser import _process_all_of
from .keywords.any_of_parser import _parse_any_of_schemas
from .keywords.one_of_parser import _parse_one_of_schemas

# Import the new schema_finalizer

# Check for cycle detection environment variables
DEBUG_CYCLES = os.environ.get("PYOPENAPI_DEBUG_CYCLES", "0").lower() in ("1", "true", "yes")
try:
    MAX_CYCLES = int(os.environ.get("PYOPENAPI_MAX_CYCLES", "0"))
except ValueError:
    MAX_CYCLES = 0  # Default value if conversion fails
try:
    ENV_MAX_DEPTH = int(os.environ.get("PYOPENAPI_MAX_DEPTH", "100"))
except ValueError:
    ENV_MAX_DEPTH = 100  # Default value if conversion fails

# Configure logging
logger = logging.getLogger(__name__)
if DEBUG_CYCLES:
    logger.setLevel(logging.DEBUG)


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


def _parse_schema(
    schema_name: Optional[str],
    schema_node: Optional[Mapping[str, Any]],
    context: ParsingContext,
    max_depth_override: Optional[int] = None,
) -> IRSchema:
    """
    Parse a schema node and return an IRSchema object.
    """
    # Pre-conditions
    assert context is not None, "Context cannot be None for _parse_schema"

    # Always call enter_schema to track depth and named cycles. This must be balanced by exit_schema.
    is_cycle, cycle_path_str = context.enter_schema(schema_name)

    try:  # Ensure exit_schema is called
        if is_cycle:
            # is_cycle will only be true if schema_name was not None and a named cycle was found by context.enter_schema
            assert schema_name is not None, "If is_cycle is True, schema_name must have been provided to enter_schema."
            assert cycle_path_str is not None, "If is_cycle is True, cycle_path_str must be populated."
            return _handle_cycle_detection(schema_name, cycle_path_str, context)

        if DEBUG_CYCLES:
            logger.debug(
                f"PARSING '{schema_name or 'anonymous'}': current_depth={context.recursion_depth}, ENV_MAX_DEPTH={ENV_MAX_DEPTH}"
            )
        if context.recursion_depth > ENV_MAX_DEPTH:
            if DEBUG_CYCLES:
                logger.warning(
                    f"MAX DEPTH EXCEEDED for '{schema_name or 'anonymous'}' (depth {context.recursion_depth} > {ENV_MAX_DEPTH}). Calling handler."
                )
            return _handle_max_depth_exceeded(schema_name, context, ENV_MAX_DEPTH)

        if schema_node is None:
            if DEBUG_CYCLES:
                logger.debug(
                    f"_parse_schema called with schema_node=None for '{schema_name or 'anonymous'}. Returning basic IRSchema."
                )
            # Return a basic schema, but ensure it has a name if one was provided (for consistency with named placeholders)
            return IRSchema(name=NameSanitizer.sanitize_class_name(schema_name) if schema_name else None)

        assert isinstance(schema_node, Mapping), (
            f"Schema node for '{schema_name or 'anonymous'}' must be a Mapping (e.g., dict), got {type(schema_node)}"
        )

        # --- $ref resolution --- (Happens *after* initial cycle/depth checks for the current schema_name)
        if "$ref" in schema_node:
            ref_path = schema_node["$ref"]
            ref_name_parts = ref_path.split("/")
            if ref_name_parts and ref_name_parts[-1]:
                ref_name = ref_name_parts[-1]
                if ref_name in context.raw_spec_schemas:
                    if DEBUG_CYCLES:
                        logger.debug(f"Resolving $ref '{ref_path}' to schema '{ref_name}' via raw_spec_schemas.")
                    # Recursive call will do its own enter/exit and cycle/depth checks for ref_name
                    return _parse_schema(ref_name, context.raw_spec_schemas[ref_name], context, max_depth_override)
                else:
                    logger.warning(
                        f"Cannot resolve $ref '{ref_path}' for '{schema_name or 'anonymous'}. Returning basic IRSchema as placeholder."
                    )
                    return IRSchema(
                        name=NameSanitizer.sanitize_class_name(schema_name) if schema_name else None,
                        description=f"Unresolved $ref: {ref_path}",
                        _from_unresolved_ref=True,
                    )
            else:
                logger.warning(f"Malformed $ref path '{ref_path}' for '{schema_name or 'anonymous'}'.")
                return IRSchema(
                    name=NameSanitizer.sanitize_class_name(schema_name) if schema_name else None,
                    description=f"Malformed $ref: {ref_path}",
                    _from_unresolved_ref=True,
                )

        # --- Main parsing logic if not a $ref or if $ref was resolved by returning above ---
        # ... (rest of the parsing logic: _parse_composition_keywords, type extraction, properties, etc.)

        # [EXISTING PARSING LOGIC FOR COMPOSITION, TYPE, PROPERTIES, ETC. GOES HERE]
        # This includes: extracted_type, any_of_irs, one_of_irs, all_of_components_irs, props_from_comp, req_from_comp, etc.
        # And building the schema_ir object.
        # For brevity, this detailed logic is represented by the existing code that follows.

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
                    if DEBUG_CYCLES:
                        logger.debug(
                            f"Schema '{schema_name or 'anonymous'}' has multiple types: {non_null_types}. Using '{extracted_type}'."
                        )
            elif is_nullable_from_type_field:
                extracted_type = "null"

        any_of_irs, one_of_irs, all_of_components_irs, props_from_comp, req_from_comp, nullable_from_comp = (
            _parse_composition_keywords(schema_node, schema_name, context, ENV_MAX_DEPTH, _parse_schema)
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
            final_properties_for_ir = props_from_comp.copy()
            if "properties" in schema_node:
                for prop_name, prop_schema_node in schema_node["properties"].items():
                    if not isinstance(prop_name, str) or not prop_name:
                        logger.warning(
                            f"Skipping property with invalid name '{prop_name}' in schema '{schema_name or 'anonymous'}'."
                        )
                        continue

                    if prop_name not in final_properties_for_ir:
                        # If property schema is a direct $ref, parse the reference directly.
                        if isinstance(prop_schema_node, Mapping) and "$ref" in prop_schema_node:
                            ref_path = prop_schema_node["$ref"]
                            ref_name_parts = ref_path.split("/")
                            if ref_name_parts and ref_name_parts[-1]:
                                ref_name = ref_name_parts[-1]
                                if ref_name in context.raw_spec_schemas:
                                    if DEBUG_CYCLES:
                                        logger.debug(
                                            f"Property '{prop_name}' in schema '{schema_name or 'anonymous'}' is $ref to '{ref_name}'. Parsing ref directly."
                                        )
                                    final_properties_for_ir[prop_name] = _parse_schema(
                                        ref_name, context.raw_spec_schemas[ref_name], context, max_depth_override
                                    )
                                else:
                                    logger.warning(
                                        f"Property '{prop_name}' in schema '{schema_name or 'anonymous'}' has unresolvable $ref '{ref_path}'. Creating placeholder."
                                    )
                                    final_properties_for_ir[prop_name] = IRSchema(
                                        name=NameSanitizer.sanitize_class_name(prop_name),
                                        description=f"Unresolved $ref: {ref_path}",
                                        _from_unresolved_ref=True,
                                    )
                            else:
                                logger.warning(
                                    f"Property '{prop_name}' in schema '{schema_name or 'anonymous'}' has malformed $ref path '{ref_path}'."
                                )
                                final_properties_for_ir[prop_name] = IRSchema(
                                    name=NameSanitizer.sanitize_class_name(prop_name),
                                    description=f"Malformed $ref: {ref_path}",
                                    _from_unresolved_ref=True,
                                )
                        else:
                            # Original logic for non-$ref properties (inline objects, direct types, etc.)
                            is_inline_object_node = (
                                isinstance(prop_schema_node, Mapping)
                                and prop_schema_node.get("type") == "object"
                                and "$ref" not in prop_schema_node  # Ensure it's not also a $ref here
                                and ("properties" in prop_schema_node or "description" in prop_schema_node)
                            )

                            if is_inline_object_node and schema_name:  # Promote named inline objects
                                promoted_schema_name = f"{schema_name}{NameSanitizer.sanitize_class_name(prop_name)}"
                                actual_promoted_ir = _parse_schema(
                                    promoted_schema_name, prop_schema_node, context, max_depth_override
                                )
                                # >>> DIAGNOSTIC PRINT (REMOVED) <<<
                                # if schema_name == "DeepSchemaLevel1" and prop_name == "level2":
                                #     print(f"SCHEMA_PARSER_ASSIGNMENT_DEBUG for '{schema_name}.{prop_name}': Assigning to final_properties_for_ir. Promoted schema name: {promoted_schema_name}, actual_promoted_ir.name: {getattr(actual_promoted_ir, 'name', 'N/A')}")

                                final_properties_for_ir[prop_name] = IRSchema(
                                    name=prop_name,  # Property name remains original
                                    type=promoted_schema_name,  # Type is the name of the promoted schema
                                    description=actual_promoted_ir.description,
                                    is_nullable=prop_schema_node.get("nullable", False)
                                    or actual_promoted_ir.is_nullable,
                                    _refers_to_schema=actual_promoted_ir,
                                )
                                # >>> NEW PRINT 1 <<<
                                if schema_name == "DeepSchemaLevel1" and prop_name == "level2":
                                    print(
                                        f"SCHEMA_PARSER_POST_ASSIGN_DEBUG for '{schema_name}': final_properties_for_ir NOW: {final_properties_for_ir}"
                                    )
                            else:  # Non-promoted inline object or simple type
                                prop_schema_context_name: str
                                if schema_name:
                                    prop_schema_context_name = (
                                        f"{schema_name}{NameSanitizer.sanitize_class_name(prop_name)}"
                                    )
                                else:
                                    # For anonymous parent schema, base name on sanitized prop_name only
                                    prop_schema_context_name = NameSanitizer.sanitize_class_name(prop_name)

                                final_properties_for_ir[prop_name] = _parse_schema(
                                    prop_schema_context_name, prop_schema_node, context, max_depth_override
                                )
        final_required_fields_set = req_from_comp.copy()
        if "required" in schema_node and isinstance(schema_node["required"], list):
            final_required_fields_set.update(schema_node["required"])

        # Resolve array items if type is 'array'
        items_ir: Optional[IRSchema] = None
        if current_final_type == "array":
            items_node = schema_node.get("items")
            if items_node:
                # Construct a name for the items schema if it's an inline object/array that needs promotion/naming
                item_schema_name_context = f"{schema_name or 'AnonymousArray'}Item"
                items_ir = _parse_schema(item_schema_name_context, items_node, context, max_depth_override)
            else:
                if DEBUG_CYCLES:
                    logger.debug(
                        f"Array schema '{schema_name or 'anonymous'}' has no 'items' defined. Defaulting to 'Any'."
                    )
                # Create a placeholder IRSchema for type Any if items are not defined.
                items_ir = IRSchema(type="Any")  # Representing typing.Any

        # Build the main IRSchema object for the current schema_node (if not returned early)
        # The name attribute of schema_ir should be the SANITIZED version if schema_name was provided.
        schema_ir_name_attr = NameSanitizer.sanitize_class_name(schema_name) if schema_name else None

        schema_ir = IRSchema(
            name=schema_ir_name_attr,  # Use sanitized name
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
            is_nullable=is_nullable_overall,
            items=items_ir,
        )

        # If the schema is an array and its items field is a sub-schema (dict),
        # recursively parse it so depth/cycles in items are caught.
        if schema_ir.type == "array" and isinstance(schema_node.get("items"), Mapping):
            raw_items_node = schema_node["items"]  # Known to be Mapping here
            # Avoid re-parsing if items is a $ref that top-level $ref logic would handle,
            # but this deep items $ref needs its own parse if not caught by top-level.
            # For direct inline item objects, or $refs within items not caught by main $ref block:
            if isinstance(raw_items_node, Mapping):  # Redundant but for clarity
                if DEBUG_CYCLES:
                    logger.debug(
                        f"Recursively parsing items for array schema '{schema_name or 'anonymous'}'. Item node: {raw_items_node}"
                    )
                # Determine a name for the item schema for context, if possible
                item_schema_context_name: Optional[str] = None
                if schema_name:
                    item_schema_context_name = (
                        f"{NameSanitizer.sanitize_class_name(schema_name)}Item"  # Sanitize parent for name
                    )
                # else, it's an item of an anonymous array, pass None

                # Check if items node is a $ref itself, if so, parse it as such by passing it to _parse_schema directly
                # The main $ref block at the top of _parse_schema handles $refs for the *current* schema_node.
                # This here handles if schema_node.items is a $ref.
                if "$ref" in raw_items_node:  # Item itself is a $ref
                    # The main $ref logic at the top of _parse_schema should handle this if raw_items_node was the schema_node.
                    # Here, we are a sub-parser. We can directly call _parse_schema with the raw_items_node,
                    # and it will handle its $ref internally.
                    # The name passed here would be the contextual name for the item definition spot.
                    schema_ir.items = _parse_schema(
                        item_schema_context_name, raw_items_node, context, max_depth_override
                    )
                else:  # Item is an inline schema definition
                    schema_ir.items = _parse_schema(
                        item_schema_context_name, raw_items_node, context, max_depth_override
                    )

        # YIELDING LOGIC FOR EXISTING CYCLE PLACEHOLDER (applies if schema_name is not None):
        if schema_name and schema_name in context.parsed_schemas:
            existing_in_context = context.parsed_schemas[schema_name]
            if DEBUG_CYCLES:
                logger.debug(
                    f"YIELD CHECK for '{schema_name}': schema_ir id={id(schema_ir)}, name={getattr(schema_ir, 'name', 'N/A')}, circular={getattr(schema_ir, '_is_circular_ref', 'N/A')}"
                )
                logger.debug(
                    f"YIELD CHECK for '{schema_name}': existing_in_context id={id(existing_in_context)}, name={getattr(existing_in_context, 'name', 'N/A')}, circular={getattr(existing_in_context, '_is_circular_ref', 'N/A')}"
                )

            if existing_in_context._is_circular_ref and existing_in_context is not schema_ir:
                if DEBUG_CYCLES:
                    logger.debug(
                        f"Outer parse of '{schema_name}' yielding to existing cycle placeholder "
                        f"(id={id(existing_in_context)}) instead of its own build (id={id(schema_ir)})."
                    )
                return existing_in_context
            else:
                logger.debug(
                    f"YIELDING DECISION for '{schema_name}': Not yielding. existing._is_circular_ref={existing_in_context._is_circular_ref}, is_different_object={existing_in_context is not schema_ir}"
                )

        # Store the schema_ir we built (or obtained, e.g. from a $ref that resolved to a cycle placeholder)
        # in context, using original (un-sanitized) schema_name as key, if schema_name is not None.
        # This is important because _handle_cycle_detection and _handle_max_depth_exceeded also use
        # the original schema_name as the key when they store their placeholders.
        if schema_name:
            # If schema_ir came from _handle_cycle_detection or _handle_max_depth_exceeded (called at the start of *this* frame),
            # it would have already been stored in context.parsed_schemas[schema_name] by those functions.
            # So, only store if it's different from what might already be there due to those early returns.
            # This check `schema_ir is not context.parsed_schemas.get(schema_name)` handles that.
            # However, if those handlers ensure they store and return the exact same object, this might be simpler:
            # just context.parsed_schemas[schema_name] = schema_ir might be fine if schema_ir is always the definitive one for this frame.
            # For now, let's be explicit: if schema_ir is a new build, store it.
            # If schema_ir is a placeholder from this frame's early exit, it was already stored.
            # The YIELDING LOGIC above handles placeholders from *nested* calls.

            # Re-evaluating: _handle_... functions DO store in context.parsed_schemas[original_name].
            # So, if we returned from there, schema_ir *is* that placeholder.
            # If we built schema_ir fresh, or got it from $ref, then we store it.
            context.parsed_schemas[schema_name] = schema_ir

        return schema_ir

    finally:
        context.exit_schema(schema_name)  # Balance enter_schema for all paths
