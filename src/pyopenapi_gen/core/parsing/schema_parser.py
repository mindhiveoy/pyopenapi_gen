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

try:
    MAX_CYCLES = int(os.environ.get("PYOPENAPI_MAX_CYCLES", "0"))
except ValueError:
    MAX_CYCLES = 0
try:
    ENV_MAX_DEPTH = int(os.environ.get("PYOPENAPI_MAX_DEPTH", "100"))
except ValueError:
    ENV_MAX_DEPTH = 100

logger = logging.getLogger(__name__)


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
            assert schema_name is not None, "If is_cycle is True, schema_name must have been provided to enter_schema."
            assert cycle_path_str is not None, "If is_cycle is True, cycle_path_str must be populated."
            return _handle_cycle_detection(schema_name, cycle_path_str, context)

        if context.recursion_depth > ENV_MAX_DEPTH:
            return _handle_max_depth_exceeded(schema_name, context, ENV_MAX_DEPTH)

        if schema_node is None:
            return IRSchema(name=NameSanitizer.sanitize_class_name(schema_name) if schema_name else None)

        assert isinstance(schema_node, Mapping), (
            f"Schema node for '{schema_name or 'anonymous'}' must be a Mapping (e.g., dict), got {type(schema_node)}"
        )

        if "$ref" in schema_node:
            ref_path = schema_node["$ref"]
            ref_name_parts = ref_path.split("/")
            if ref_name_parts and ref_name_parts[-1]:
                ref_name = ref_name_parts[-1]
                if ref_name in context.raw_spec_schemas:
                    return _parse_schema(ref_name, context.raw_spec_schemas[ref_name], context, max_depth_override)
                else:
                    logger.warning(
                        f"Cannot resolve $ref '{ref_path}' for '{schema_name or 'anonymous'}'. Returning basic IRSchema as placeholder."
                    )
                    return IRSchema(
                        name=NameSanitizer.sanitize_class_name(schema_name) if schema_name else None,
                        _from_unresolved_ref=True,
                        description=f"Unresolved $ref: {ref_path}",
                    )
            else:
                logger.warning(f"Malformed $ref path '{ref_path}' for '{schema_name or 'anonymous'}'.")
                return IRSchema(
                    name=NameSanitizer.sanitize_class_name(schema_name) if schema_name else None,
                    description=f"Malformed $ref: {ref_path}",
                    _from_unresolved_ref=True,
                )

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
            final_required_set: Set[str] = set()
            if "properties" in schema_node:
                for prop_name, prop_schema_node in schema_node["properties"].items():
                    if not isinstance(prop_name, str) or not prop_name:
                        logger.warning(
                            f"Skipping property with invalid name '{prop_name}' in schema '{schema_name or 'anonymous'}'."
                        )
                        continue

                    if prop_name not in final_properties_for_ir:
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
                            is_inline_object_node = (
                                isinstance(prop_schema_node, Mapping)
                                and prop_schema_node.get("type") == "object"
                                and "$ref" not in prop_schema_node
                                and ("properties" in prop_schema_node or "description" in prop_schema_node)
                            )

                            if is_inline_object_node and schema_name:
                                promoted_schema_name = f"{schema_name}{NameSanitizer.sanitize_class_name(prop_name)}"
                                promoted_ir_schema = _parse_schema(
                                    promoted_schema_name, prop_schema_node, context, max_depth_override
                                )

                                final_properties_for_ir[prop_name] = IRSchema(
                                    name=prop_name,
                                    type=promoted_schema_name,
                                    description=promoted_ir_schema.description,
                                    is_nullable=prop_schema_node.get("nullable", False)
                                    or promoted_ir_schema.is_nullable,
                                    _refers_to_schema=promoted_ir_schema,
                                )
                                context.parsed_schemas[promoted_schema_name] = promoted_ir_schema
                            else:
                                prop_schema_context_name = NameSanitizer.sanitize_class_name(prop_name)

                                parsed_prop_schema_ir = _parse_schema(
                                    prop_schema_context_name,
                                    prop_schema_node,
                                    context,
                                    max_depth_override,
                                )

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
                                    prop_is_nullable = False
                                    if "nullable" in prop_schema_node:
                                        prop_is_nullable = prop_schema_node["nullable"]
                                    elif (
                                        isinstance(prop_schema_node.get("type"), list)
                                        and "null" in prop_schema_node["type"]
                                    ):
                                        prop_is_nullable = True
                                    elif parsed_prop_schema_ir.is_nullable:
                                        prop_is_nullable = True

                                    property_holder_ir = IRSchema(
                                        name=prop_name,
                                        type=parsed_prop_schema_ir.name,
                                        description=prop_schema_node.get(
                                            "description", parsed_prop_schema_ir.description
                                        ),
                                        is_nullable=prop_is_nullable,
                                        default=prop_schema_node.get("default"),
                                        example=prop_schema_node.get("example"),
                                        enum=prop_schema_node.get("enum") if not parsed_prop_schema_ir.enum else None,
                                        _refers_to_schema=parsed_prop_schema_ir,
                                    )
                                    if parsed_prop_schema_ir.enum and not property_holder_ir.enum:
                                        pass

                                    final_properties_for_ir[prop_name] = property_holder_ir
                                else:
                                    if parsed_prop_schema_ir.name != prop_name and not (
                                        parsed_prop_schema_ir.name
                                        and context.is_schema_parsed(parsed_prop_schema_ir.name)
                                        and context.get_parsed_schema(parsed_prop_schema_ir.name)
                                        is parsed_prop_schema_ir
                                    ):
                                        simple_prop_holder = IRSchema(
                                            name=prop_name,
                                            type=parsed_prop_schema_ir.type,
                                            description=prop_schema_node.get(
                                                "description", parsed_prop_schema_ir.description
                                            ),
                                            is_nullable=parsed_prop_schema_ir.is_nullable,
                                            default=prop_schema_node.get("default", parsed_prop_schema_ir.default),
                                            example=prop_schema_node.get("example", parsed_prop_schema_ir.example),
                                            enum=prop_schema_node.get("enum", parsed_prop_schema_ir.enum),
                                            format=parsed_prop_schema_ir.format,
                                        )
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

                                    else:
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

        items_ir: Optional[IRSchema] = None
        if current_final_type == "array":
            items_node = schema_node.get("items")
            if items_node:
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

        if schema_name and schema_name in context.parsed_schemas:
            existing_in_context = context.parsed_schemas[schema_name]

            if existing_in_context._is_circular_ref and existing_in_context is not schema_ir:
                return existing_in_context

        if schema_name:
            context.parsed_schemas[schema_name] = schema_ir

        if schema_name and not schema_ir._from_unresolved_ref and not schema_ir._max_depth_exceeded:
            context.parsed_schemas[schema_name] = schema_ir

        return schema_ir

    finally:
        context.exit_schema(schema_name)
