"""Parameter parsers for OpenAPI IR transformation.

Provides functions to parse and transform OpenAPI parameters into IR format.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, cast

from pyopenapi_gen import IRParameter, IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


def resolve_parameter_node_if_ref(param_node_data: Mapping[str, Any], context: ParsingContext) -> Mapping[str, Any]:
    """Resolve a parameter node if it's a reference.

    Contracts:
        Preconditions:
            - param_node_data is a valid parameter node mapping
            - context contains the required components information
        Postconditions:
            - Returns the resolved parameter node or the original if not a ref
            - If a reference, the parameter is looked up in components
    """
    if not isinstance(param_node_data, Mapping):
        raise TypeError("param_node_data must be a Mapping")
    if not isinstance(context, ParsingContext):
        raise TypeError("context must be a ParsingContext")

    if "$ref" in param_node_data and isinstance(param_node_data.get("$ref"), str):
        ref_path = param_node_data["$ref"]
        if ref_path.startswith("#/components/parameters/"):
            param_name = ref_path.split("/")[-1]
            # Access raw_spec_components from the context
            resolved_node = context.raw_spec_components.get("parameters", {}).get(param_name)
            if resolved_node:
                logger.debug(f"Resolved parameter $ref '{ref_path}' to '{param_name}'")
                return cast(Mapping[str, Any], resolved_node)
            else:
                logger.warning(f"Could not resolve parameter $ref '{ref_path}'")
                return param_node_data  # Return original ref node if resolution fails

    return param_node_data  # Not a ref or not a component parameter ref


def parse_parameter(
    node: Mapping[str, Any],
    context: ParsingContext,
    operation_id_for_promo: str | None = None,
) -> IRParameter:
    """Convert an OpenAPI parameter node into IRParameter.

    Contracts:
        Preconditions:
            - node is a valid parameter node with required fields
            - context is properly initialized
            - If node has a schema, it is a valid schema definition
        Postconditions:
            - Returns a properly populated IRParameter
            - Complex parameter schemas are given appropriate names
    """
    if not isinstance(node, Mapping):
        raise TypeError("node must be a Mapping")
    if "name" not in node:
        raise ValueError("Parameter node must have a name")
    if not isinstance(context, ParsingContext):
        raise TypeError("context must be a ParsingContext")

    sch = node.get("schema")
    param_name = node["name"]

    name_for_inline_param_schema: str | None = None
    if (
        sch
        and isinstance(sch, Mapping)
        and "$ref" not in sch
        and (sch.get("type") == "object" or "properties" in sch or "allOf" in sch or "anyOf" in sch or "oneOf" in sch)
    ):
        base_param_promo_name = f"{operation_id_for_promo}Param" if operation_id_for_promo else ""
        name_for_inline_param_schema = f"{base_param_promo_name}{NameSanitizer.sanitize_class_name(param_name)}"

    # General rule: if a parameter is defined inline but a components parameter exists with the
    # same name and location, prefer the components schema (often richer: arrays/enums/refs).
    try:
        if isinstance(context, ParsingContext):
            components_params = context.raw_spec_components.get("parameters", {})
            if isinstance(components_params, Mapping):
                for comp_key, comp_param in components_params.items():
                    if not isinstance(comp_param, Mapping):
                        continue
                    if comp_param.get("name") == param_name and comp_param.get("in") == node.get("in"):
                        comp_schema = comp_param.get("schema")
                        if isinstance(comp_schema, Mapping):
                            # Prefer component schema if inline is missing or clearly less specific
                            inline_is_specific = isinstance(sch, Mapping) and (
                                sch.get("type") in {"array", "object"} or "$ref" in sch or "enum" in sch
                            )
                            if not inline_is_specific:
                                sch = comp_schema
                        break
    except Exception:
        # Be conservative on any unexpected structure
        pass

    # For parameters, we want to avoid creating complex schemas for simple enum arrays
    # Check if this is a simple enum array and handle it specially
    if (
        sch
        and isinstance(sch, Mapping)
        and sch.get("type") == "array"
        and "items" in sch
        and isinstance(sch["items"], Mapping)
        and sch["items"].get("type") == "string"
        and "enum" in sch["items"]
        and "$ref" not in sch["items"]
    ):
        # This is an array of string enums - create a proper enum schema for the items
        # Give it a name based on the parameter and operation
        enum_name = None
        if operation_id_for_promo and param_name:
            # Create a name for this inline enum when we have operation context
            enum_name = f"{operation_id_for_promo}Param{NameSanitizer.sanitize_class_name(param_name)}Item"
        elif param_name:
            # For component parameters without operation context, use just the parameter name
            enum_name = f"{NameSanitizer.sanitize_class_name(param_name)}Item"

        if enum_name:
            items_schema = IRSchema(
                name=enum_name,
                type="string",
                enum=sch["items"]["enum"],
                generation_name=enum_name,  # Mark it as promoted
                final_module_stem=NameSanitizer.sanitize_module_name(enum_name),  # Set module stem for imports
            )

            # Register this inline enum schema so it gets generated as a model file
            if isinstance(context, ParsingContext) and enum_name not in context.parsed_schemas:
                context.parsed_schemas[enum_name] = items_schema
                logger.debug(
                    f"Registered enum schema '{enum_name}' for array parameter '{param_name}' with values {sch['items']['enum'][:3]}..."
                )

            logger.debug(
                f"Created enum schema '{enum_name}' for array parameter '{param_name}' with values {sch['items']['enum'][:3]}..."
            )
        else:
            # Fallback if we don't have enough info to create a good name
            items_schema = IRSchema(name=None, type="string", enum=sch["items"]["enum"])
            logger.warning(
                f"Could not create proper enum name for parameter array items with values {sch['items']['enum'][:3]}... "
                f"This will generate a warning during type resolution."
            )

        schema_ir = IRSchema(
            name=None,
            type="array",
            items=items_schema,
            description=sch.get("description"),
        )
    else:
        schema_ir = (
            _parse_schema(name_for_inline_param_schema, sch, context, allow_self_reference=False)
            if sch
            else IRSchema(name=None)
        )

    param = IRParameter(
        name=node["name"],
        param_in=node.get("in", "query"),
        required=bool(node.get("required", False)),
        schema=schema_ir,
        description=node.get("description"),
    )

    # Post-condition check
    if param.name != node["name"]:
        raise RuntimeError("Parameter name mismatch")
    if param.schema is None:
        raise RuntimeError("Parameter schema must be created")

    return param
