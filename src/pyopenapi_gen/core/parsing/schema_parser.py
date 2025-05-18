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
            final_required_set: Set[str] = set()  # Initialize final_required_set here
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
                                promoted_ir_schema = _parse_schema(
                                    promoted_schema_name, prop_schema_node, context, max_depth_override
                                )

                                final_properties_for_ir[prop_name] = IRSchema(
                                    name=prop_name,  # Property name remains original
                                    type=promoted_schema_name,  # Type is the name of the promoted schema
                                    description=promoted_ir_schema.description,
                                    is_nullable=prop_schema_node.get("nullable", False)
                                    or promoted_ir_schema.is_nullable,
                                    _refers_to_schema=promoted_ir_schema,
                                )
                                context.parsed_schemas[promoted_schema_name] = promoted_ir_schema  # Ensure it's stored
                            else:  # Non-promoted inline object or simple type
                                # This helps in tracking but doesn't guarantee a globally unique schema name if not promoted.
                                # If this inline schema is complex enough to be promoted, its name will be based on this.
                                prop_schema_context_name = NameSanitizer.sanitize_class_name(prop_name)

                                # This is the IR of the (potentially) promoted schema for the property
                                parsed_prop_schema_ir = _parse_schema(
                                    prop_schema_context_name,
                                    prop_schema_node,
                                    context,
                                    max_depth_override,
                                )

                                # Check if the property's schema was an inline object/array that got promoted
                                # (i.e., its parsed name matches the context name we gave it, and it's now a global schema)
                                original_prop_node_type = (
                                    prop_schema_node.get("type") if isinstance(prop_schema_node, Mapping) else None
                                )

                                if (
                                    isinstance(prop_schema_node, Mapping)
                                    and (original_prop_node_type == "object" or original_prop_node_type == "array")
                                    and parsed_prop_schema_ir.name == prop_schema_context_name
                                    and context.is_schema_parsed(parsed_prop_schema_ir.name)
                                    and context.get_parsed_schema(parsed_prop_schema_ir.name) is parsed_prop_schema_ir
                                ):
                                    # It's a promoted inline object/array. Create a holder IR for the property slot.
                                    # The holder's 'type' will be the NAME of the promoted schema.
                                    # The holder's 'name' will be the original property name.

                                    # Determine nullability for the property reference itself based on the property's node
                                    prop_is_nullable = False
                                    if "nullable" in prop_schema_node:  # OpenAPI v3
                                        prop_is_nullable = prop_schema_node["nullable"]
                                    elif (
                                        isinstance(prop_schema_node.get("type"), list)
                                        and "null" in prop_schema_node["type"]
                                    ):  # OpenAPI v2 style for type: [..., null]
                                        prop_is_nullable = True
                                    elif (
                                        parsed_prop_schema_ir.is_nullable
                                    ):  # Fallback to promoted schema's nullability if not on prop node
                                        prop_is_nullable = True

                                    property_holder_ir = IRSchema(
                                        name=prop_name,  # Original property name (e.g., "config")
                                        type=parsed_prop_schema_ir.name,  # Type is the *name* of the promoted schema (e.g., "ParentConfig")
                                        description=prop_schema_node.get(
                                            "description", parsed_prop_schema_ir.description
                                        ),
                                        is_nullable=prop_is_nullable,
                                        default=prop_schema_node.get(
                                            "default"
                                        ),  # Default comes from property definition
                                        example=prop_schema_node.get(
                                            "example"
                                        ),  # Example comes from property definition
                                        enum=prop_schema_node.get("enum")
                                        if not parsed_prop_schema_ir.enum
                                        else None,  # Enum on prop node takes precedence
                                        _refers_to_schema=parsed_prop_schema_ir,  # Link to the actual promoted schema definition
                                    )
                                    # If the promoted schema itself had an enum, and prop node didn't, it's part of the type, not this ref
                                    if parsed_prop_schema_ir.enum and not property_holder_ir.enum:
                                        # This indicates the enum is on the referenced type.
                                        # The property_holder_ir.type already points to its name.
                                        pass

                                    final_properties_for_ir[prop_name] = property_holder_ir
                                else:
                                    # Not a promoted complex type, or some other scenario.
                                    # Assign directly, but ensure its name is prop_name if it's not a global ref.
                                    if parsed_prop_schema_ir.name != prop_name and not (
                                        parsed_prop_schema_ir.name
                                        and context.is_schema_parsed(parsed_prop_schema_ir.name)
                                        and context.get_parsed_schema(parsed_prop_schema_ir.name)
                                        is parsed_prop_schema_ir
                                    ):
                                        # This case is tricky: parsed_prop_schema_ir might have a generated name.
                                        # For simple types (string, int), parsed_prop_schema_ir.name is often None or based on context.
                                        # We want the IR stored in parent's properties to have the correct 'prop_name'.
                                        # Let's create a new simple IR holder for this property if its name doesn't match.
                                        # This typically applies to anonymous simple types.
                                        simple_prop_holder = IRSchema(
                                            name=prop_name,
                                            type=parsed_prop_schema_ir.type,
                                            description=prop_schema_node.get(
                                                "description", parsed_prop_schema_ir.description
                                            ),
                                            is_nullable=parsed_prop_schema_ir.is_nullable,  # Should be derived from prop_schema_node ideally
                                            default=prop_schema_node.get("default", parsed_prop_schema_ir.default),
                                            example=prop_schema_node.get("example", parsed_prop_schema_ir.example),
                                            enum=prop_schema_node.get("enum", parsed_prop_schema_ir.enum),
                                            format=parsed_prop_schema_ir.format,
                                            # No _refers_to_schema for simple types not in global context
                                        )
                                        # Re-check nullability from prop_schema_node
                                        prop_node_nullable = False
                                        if isinstance(prop_schema_node, Mapping):
                                            if "nullable" in prop_schema_node:
                                                prop_node_nullable = prop_schema_node["nullable"]
                                            elif (
                                                isinstance(prop_schema_node.get("type"), list)
                                                and "null" in prop_schema_node["type"]
                                            ):
                                                prop_node_nullable = True
                                        simple_prop_holder.is_nullable = (
                                            prop_node_nullable or parsed_prop_schema_ir.is_nullable
                                        )

                                        final_properties_for_ir[prop_name] = simple_prop_holder

                                    else:  # Is a global ref by its name, or name already matches prop_name
                                        final_properties_for_ir[prop_name] = parsed_prop_schema_ir

                        required_from_prop = (
                            set(prop_schema_node.get("required", []))
                            if isinstance(prop_schema_node, Mapping)
                            else set()
                        )
                        final_required_set.update(required_from_prop)
        final_required_fields_set = req_from_comp.copy()
        if "required" in schema_node and isinstance(schema_node["required"], list):
            final_required_fields_set.update(schema_node["required"])

        # Resolve array items if type is 'array'
        items_ir: Optional[IRSchema] = None
        if current_final_type == "array":
            items_node = schema_node.get("items")
            if items_node:
                # Construct a name for the items schema if it's an inline object/array that needs promotion/naming
                # Ensure sanitize_class_name gets a valid string.
                base_name_for_item = schema_name or "AnonymousArray"
                item_schema_name_for_recursive_parse = NameSanitizer.sanitize_class_name(f"{base_name_for_item}Item")

                actual_item_ir = _parse_schema(
                    item_schema_name_for_recursive_parse, items_node, context, max_depth_override
                )

                is_promoted_inline_object = (
                    isinstance(items_node, Mapping)
                    and items_node.get("type") == "object"
                    and "$ref" not in items_node
                    and actual_item_ir.name == item_schema_name_for_recursive_parse
                )

                if is_promoted_inline_object:
                    # Check if the context actually contains the promoted item by its name, RIGHT NOW.
                    # This is crucial because ModelsEmitter later fetches from context.parsed_schemas.

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
            raw_items_node = schema_node["items"]
            item_schema_context_name_for_reparse: Optional[str]
            base_name_for_reparse_item = schema_name or "AnonymousArray"  # Fallback for anonymous parent array
            item_schema_context_name_for_reparse = NameSanitizer.sanitize_class_name(
                f"{base_name_for_reparse_item}Item"
            )

            direct_reparsed_item_ir = _parse_schema(
                item_schema_context_name_for_reparse, raw_items_node, context, max_depth_override
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

        # YIELDING LOGIC FOR EXISTING CYCLE PLACEHOLDER (applies if schema_name is not None):
        if schema_name and schema_name in context.parsed_schemas:
            existing_in_context = context.parsed_schemas[schema_name]

            if existing_in_context._is_circular_ref and existing_in_context is not schema_ir:
                return existing_in_context

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

        # Store the fully parsed schema (unless it's a placeholder for an unresolved ref or max depth hit)
        # Aliases with simple types are also stored here if they have a schema_name.
        if schema_name and not schema_ir._from_unresolved_ref and not schema_ir._max_depth_exceeded:
            context.parsed_schemas[schema_name] = schema_ir

        return schema_ir

    finally:
        context.exit_schema(schema_name)  # Balance enter_schema for all paths
