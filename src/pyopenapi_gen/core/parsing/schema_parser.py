"""
Core schema parsing logic, transforming a schema node into an IRSchema object.
"""

from __future__ import annotations

import copy
import logging  # For logger
import os  # For environment variables
import warnings  # For warnings
from typing import Any, Dict, List, Mapping, Optional, Set, cast  # Ensure all types are here

from pyopenapi_gen import IRSchema  # Assuming IRSchema is in the root pyopenapi_gen package
from pyopenapi_gen.core.utils import NameSanitizer  # For name sanitization

# Check for cycle detection environment variables
DEBUG_CYCLES = os.environ.get('PYOPENAPI_DEBUG_CYCLES', '0').lower() in ('1', 'true', 'yes')
MAX_CYCLES = int(os.environ.get('PYOPENAPI_MAX_CYCLES', '0'))
ENV_MAX_DEPTH = int(os.environ.get('PYOPENAPI_MAX_DEPTH', '100'))

from .all_of_merger import _process_all_of
from .context import ParsingContext
from .inline_enum_extractor import _extract_enum_from_property_node, _process_standalone_inline_enum
from .inline_object_promoter import _attempt_promote_inline_object
from .ref_resolver import _resolve_schema_ref
from .type_parser import extract_primary_type_and_nullability

logger = logging.getLogger(__name__)  # Initialize logger for this module


def _parse_schema(
    name: Optional[str],
    node: Optional[Mapping[str, Any]],
    context: ParsingContext,
    max_depth: int = ENV_MAX_DEPTH,  # Use environment variable or default to 100
) -> IRSchema:
    """Recursively parse a schema node, resolving refs and composition keywords."""
    # Track schema parsing entry for cycle detection
    is_cycle, cycle_path = context.enter_schema(name)

    try:
        # Check if we've hit max recursion depth
        if context.recursion_depth > max_depth:
            depth_msg = f"Maximum recursion depth ({max_depth}) exceeded while parsing schema '{name}'"
            logger.warning(depth_msg)
            schema = IRSchema(
                name=name,
                type="object",  # Default to object type for excessive recursion
                description=f"[Excessive recursion: {depth_msg}]",
                _is_circular_ref=True,  # Mark as circular for consistent handling
                _circular_ref_path=f"MAX_DEPTH_EXCEEDED: {context.recursion_depth} > {max_depth}"
            )
            # Add to parsed_schemas to prevent further attempts
            if name:
                context.parsed_schemas[name] = schema
            return schema

        # If we detected a cycle, return a placeholder schema with cycle information
        if is_cycle and name:
            logger.warning(f"Cycle detected while parsing schema '{name}'. Returning placeholder.")
            schema = IRSchema(
                name=name,
                type="object",  # Assume object type for circular references
                description=f"[Circular reference detected: {cycle_path}]",
                _is_circular_ref=True,
                _circular_ref_path=cycle_path
            )
            # Add this circular ref schema to parsed_schemas to break the cycle
            if name and not schema._from_unresolved_ref:
                context.parsed_schemas[name] = schema
            return schema

        # Begin regular parsing (existing implementation)
        if node is None:
            return IRSchema(name=name)

        if "$ref" in node:
            return _resolve_schema_ref(node["$ref"], name, context)

        schema_type: Optional[str] = None
        is_nullable: bool = False
        any_of_schemas: Optional[List[IRSchema]] = None
        one_of_schemas: Optional[List[IRSchema]] = None
        parsed_all_of_components: Optional[List[IRSchema]] = None
        merged_properties: Dict[str, IRSchema] = {}
        merged_required: Set[str] = set()

        if "anyOf" in node:
            any_of_schemas = [_parse_schema(None, sub, context, max_depth=max_depth) for sub in node["anyOf"]]
            if any(isinstance(sub, dict) and sub.get("type") == "null" for sub in node["anyOf"]):
                is_nullable = True
                any_of_schemas = [
                    s for s in any_of_schemas if not (s.type is None and not s.properties and not s.items and not s.enum)
                ]
                if not any_of_schemas:
                    schema_type = None
                    any_of_schemas = None

        if "oneOf" in node:
            one_of_schemas = [_parse_schema(None, sub, context, max_depth=max_depth) for sub in node["oneOf"]]
            if any(s.type == "null" for s in one_of_schemas):
                is_nullable = True
                one_of_schemas = [s for s in one_of_schemas if s.type != "null"]
                if not one_of_schemas:
                    schema_type = None
                    one_of_schemas = None

        if "allOf" in node:
            merged_properties, merged_required, parsed_all_of_components = _process_all_of(
                node, name, context,
                lambda n, d, c, md=None: _parse_schema(n, d, c, max_depth=md if md is not None else max_depth),
                max_depth=max_depth
            )
            if merged_properties and schema_type is None:
                schema_type = "object"
        else:
            merged_required = set(node.get("required", []))

        raw_type_from_node = node.get("type")
        if schema_type is None and not any_of_schemas and not one_of_schemas:
            extracted_type, extracted_nullable, type_warnings = extract_primary_type_and_nullability(
                raw_type_from_node, name
            )
            schema_type = extracted_type
            is_nullable = extracted_nullable
            context.collected_warnings.extend(type_warnings)

        final_properties_map: Dict[str, IRSchema] = {}
        if "allOf" in node:
            final_properties_map = merged_properties
        elif "properties" in node:
            current_properties_dict: Dict[str, IRSchema] = {}
            for prop_key, prop_node_data in node["properties"].items():
                prop_schema_context_name = f"{name}.{prop_key}" if name else prop_key

                extracted_enum_property_ir = _extract_enum_from_property_node(
                    name, prop_key, prop_node_data, context, logger
                )

                if extracted_enum_property_ir:
                    current_properties_dict[prop_key] = extracted_enum_property_ir
                else:
                    parsed_prop_schema = _parse_schema(prop_schema_context_name, prop_node_data, context, max_depth=max_depth)

                    # Attempt to promote the parsed property schema if it's an inline object
                    promoted_ref_ir = _attempt_promote_inline_object(
                        name,  # Parent schema name (original name arg to _parse_schema)
                        prop_key,
                        parsed_prop_schema,
                        context,
                        logger,
                    )

                    if promoted_ref_ir:
                        current_properties_dict[prop_key] = promoted_ref_ir
                    else:
                        current_properties_dict[prop_key] = parsed_prop_schema

                    if prop_schema_context_name == "LogDocumentEventRequest.costs":  # Example debug line
                        logger.debug(
                            f"LOADER_PROP_DEBUG: Parsed '{prop_schema_context_name}' -> Name: {parsed_prop_schema.name}, Type: {parsed_prop_schema.type}, Props: {list(parsed_prop_schema.properties.keys()) if parsed_prop_schema.properties else []}, Enum: {parsed_prop_schema.enum is not None}"
                        )
            final_properties_map = current_properties_dict

        final_items_schema: Optional[IRSchema] = None
        if schema_type == "array" and "items" in node:
            items_node_data = node["items"]
            item_name_for_parse = f"{name}Item" if name else None
            if (
                isinstance(items_node_data, dict)
                and "$ref" in items_node_data
                and items_node_data["$ref"].startswith("#/components/schemas/")
            ):
                item_name_for_parse = items_node_data["$ref"].split("/")[-1]
            final_items_schema = _parse_schema(item_name_for_parse, items_node_data, context, max_depth=max_depth)

        final_enum_values: Optional[List[Any]] = node.get("enum") if isinstance(node.get("enum"), list) else None
        final_required_fields_list: List[str] = sorted(list(merged_required))
        raw_add_props = node.get("additionalProperties")
        final_additional_properties: Optional[bool | IRSchema] = None
        if isinstance(raw_add_props, bool):
            final_additional_properties = raw_add_props
        elif isinstance(raw_add_props, dict):
            final_additional_properties = _parse_schema(None, raw_add_props, context, max_depth=max_depth)

        final_schema_name_for_obj = NameSanitizer.sanitize_class_name(name) if name else None
        if (
            "_def" in node
            and isinstance(node.get("_def"), dict)
            and node["_def"].get("typeName") == "ZodObject"
            and "_standard" in node
            and isinstance(node.get("_standard"), dict)
        ):
            standard_node = cast(Dict[str, Any], node["_standard"])
            schema_type = standard_node.get("type", "object")
            if "properties" in standard_node and isinstance(standard_node["properties"], dict):
                final_properties_map = {
                    k: _parse_schema(
                        f"{final_schema_name_for_obj}.{k}" if final_schema_name_for_obj else k, v_data, context, max_depth=max_depth
                    )
                    for k, v_data in standard_node["properties"].items()
                }
            else:
                final_properties_map = {}
            final_required_fields_list = sorted(list(set(standard_node.get("required", []))))
            std_raw_type = standard_node.get("type")
            if isinstance(std_raw_type, list) and "null" in std_raw_type:
                is_nullable = True
            elif standard_node.get("nullable") is True:
                is_nullable = True

        if schema_type is None and final_properties_map:
            schema_type = "object"

        is_data_wrapper_flag = (
            schema_type == "object"
            and "data" in final_properties_map
            and "data" in final_required_fields_list
            and len(final_properties_map) == 1
        )

        schema_obj = IRSchema(
            name=final_schema_name_for_obj,
            type=schema_type,
            format=node.get("format"),
            description=node.get("description"),
            required=final_required_fields_list,
            properties=final_properties_map,
            items=final_items_schema,
            enum=final_enum_values,
            additional_properties=final_additional_properties,
            is_nullable=is_nullable,
            any_of=any_of_schemas,
            one_of=one_of_schemas,
            all_of=parsed_all_of_components,
            is_data_wrapper=is_data_wrapper_flag,
        )
        schema_obj._from_unresolved_ref = node.get("_from_unresolved_ref", False)

        if (
            schema_obj.name
            and schema_obj.name in context.parsed_schemas
            and schema_obj.type is None
            and schema_type is not None
        ):
            logger.debug(
                f"_parse_schema: Named schema '{schema_obj.name}' had no type, adopting current node type '{schema_type}'"
            )
            schema_obj.type = schema_type

        if schema_obj.type is None and (
            schema_obj.properties
            or (
                isinstance(node.get("_def"), dict)
                and node["_def"].get("typeName") == "ZodObject"
                and node["_def"].get("shape")
            )
        ):
            logger.debug(
                f"_parse_schema: Schema '{schema_obj.name or 'anonymous_inline'}' has props/ZodShape but no type, setting to 'object'."
            )
            schema_obj.type = "object"

        if name and "." in name:
            is_explicitly_simple_type_in_node = node.get("type") in ["string", "integer", "number", "boolean", "array"]
            is_explicitly_enum_in_node = "enum" in node
            if schema_obj.type is None and not is_explicitly_simple_type_in_node and not is_explicitly_enum_in_node:
                logger.debug(
                    f"_parse_schema: Inline property '{name}' has no explicit complex type, defaulting to 'object' for promotion check."
                )
                schema_obj.type = "object"

        if schema_obj.name and not schema_obj._from_unresolved_ref:
            context.parsed_schemas[schema_obj.name] = schema_obj

        # Process if the schema_obj itself represents a standalone inline enum
        if schema_obj:  # Ensure schema_obj is not None
            # Pass the original 'name' (which could be from components.schemas or a path) and the original 'node' data.
            schema_obj = _process_standalone_inline_enum(name, node, schema_obj, context, logger)

        # Final check to ensure the schema (potentially renamed by _process_standalone_inline_enum)
        # is in the context if it has a name.
        if schema_obj and schema_obj.name and context.parsed_schemas.get(schema_obj.name) is not schema_obj:
            context.parsed_schemas[schema_obj.name] = schema_obj
            logger.debug(
                f"Ensured schema '{schema_obj.name}' (after standalone enum processing) is in context.parsed_schemas."
            )

        # Check if the context overall has detected a cycle anywhere in the parsing process
        if context.cycle_detected:
            logger.warning(f"Note: Cycle detected during schema parsing (not necessarily at '{name}')")

        logger.debug(
            f"_parse_schema returning for name: '{name}', final schema_obj name: '{schema_obj.name if schema_obj else None}', type: '{schema_obj.type if schema_obj else None}', recursion_depth: {context.recursion_depth}"
        )
        return schema_obj

    finally:
        # Always clean up the context, even if an exception occurs
        context.exit_schema(name)
