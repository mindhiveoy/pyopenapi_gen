"""Parameter parsers for OpenAPI IR transformation.

Provides functions to parse and transform OpenAPI parameters into IR format.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional, cast

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
    assert isinstance(param_node_data, Mapping), "param_node_data must be a Mapping"
    assert isinstance(context, ParsingContext), "context must be a ParsingContext"

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
    operation_id_for_promo: Optional[str] = None,
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
    assert isinstance(node, Mapping), "node must be a Mapping"
    assert "name" in node, "Parameter node must have a name"
    assert isinstance(context, ParsingContext), "context must be a ParsingContext"

    sch = node.get("schema")
    param_name = node["name"]

    name_for_inline_param_schema: Optional[str] = None
    if (
        sch
        and isinstance(sch, Mapping)
        and "$ref" not in sch
        and (sch.get("type") == "object" or "properties" in sch or "allOf" in sch or "anyOf" in sch or "oneOf" in sch)
    ):
        base_param_promo_name = f"{operation_id_for_promo}Param" if operation_id_for_promo else ""
        name_for_inline_param_schema = f"{base_param_promo_name}{NameSanitizer.sanitize_class_name(param_name)}"

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
        # This is an array of string enums - for parameters, we can treat this as List[str]
        # rather than creating complex named schemas
        schema_ir = IRSchema(
            name=None,
            type="array",
            items=IRSchema(name=None, type="string", enum=sch["items"]["enum"]),
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
    assert param.name == node["name"], "Parameter name mismatch"
    assert param.schema is not None, "Parameter schema must be created"

    return param
