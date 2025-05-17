"""Spec → IR Loader

Transforms a validated OpenAPI 3.1 (or 3.0) document (as a Python ``dict``)
into the internal IR dataclasses.  For now this implementation purposefully
covers only a *subset* of the OpenAPI surface—sufficient for the initial code
emitter prototypes:

* Components → Schemas (basic types, description, enum, properties, items)
* Paths → Operations (operation‑level parameters, request body, responses)

Dependencies on heavy libraries such as *openapi‑core* are avoided for this
minimal path to keep bootstrapping friction low.  Schema $ref resolution is
supported **only** for ``#/components/schemas/<Name>`` references for now.
"""

from __future__ import annotations

import copy
import os
import sys
import warnings
from typing import Any, Dict, List, Mapping, Optional, cast, Set

try:
    # Use the newer validate() API if available to avoid deprecation warnings
    from openapi_spec_validator import validate as validate_spec
except ImportError:
    try:
        from openapi_spec_validator import validate_spec  # type: ignore
    except ImportError:  # pragma: no cover – optional in early bootstrapping
        validate_spec = None  # type: ignore[assignment]
# Disable strict spec validation by default to allow lenient parsing

import logging

from pyopenapi_gen import (
    HTTPMethod,
    IROperation,
    IRParameter,
    IRRequestBody,
    IRResponse,
    IRSchema,
    IRSpec,
)
from pyopenapi_gen.core.utils import NameSanitizer

# Import helpers
from .parsing.common.type_parser import extract_primary_type_and_nullability

# Import ParsingContext from its new location
from .parsing.context import ParsingContext
from .parsing.schema_parser import _parse_schema

__all__ = ["load_ir_from_spec"]

logger = logging.getLogger(__name__)

# Check for cycle detection debug flags in environment
DEBUG_CYCLES = os.environ.get("PYOPENAPI_DEBUG_CYCLES", "0").lower() in ("1", "true", "yes")
MAX_CYCLES = int(os.environ.get("PYOPENAPI_MAX_CYCLES", "0"))

if DEBUG_CYCLES:
    logger.info(f"Cycle detection debugging enabled (MAX_CYCLES={MAX_CYCLES})")
    # Increase logging level for cycle detection
    logging.getLogger("pyopenapi_gen.core.parsing.context").setLevel(logging.DEBUG)
    logging.getLogger("pyopenapi_gen.core.parsing.schema_parser").setLevel(logging.DEBUG)
    logging.getLogger("pyopenapi_gen.core.parsing.ref_resolver").setLevel(logging.DEBUG)


# Helper function to resolve a parameter node if it's a reference
def _resolve_parameter_node_if_ref(param_node_data: Mapping[str, Any], context: ParsingContext) -> Mapping[str, Any]:
    if "$ref" in param_node_data and isinstance(param_node_data.get("$ref"), str):
        ref_path = param_node_data["$ref"]
        if ref_path.startswith("#/components/parameters/"):
            param_name = ref_path.split("/")[-1]
            # Access raw_spec_components from the context
            resolved_node = context.raw_spec_components.get("parameters", {}).get(param_name)
            if resolved_node:
                logger.debug(f"Resolved parameter $ref '{ref_path}' to '{param_name}'")
                # Important: Merge the original $ref into the resolved node
                # so that _parse_parameter can know it came from a ref if needed,
                # and to ensure the 'name' is from the resolved component if not on the ref itself.
                # However, the $ref node itself doesn't have 'name', 'in', etc.
                # The resolved node *is* the full definition.
                return cast(Mapping[str, Any], resolved_node)
            else:
                logger.warning(f"Could not resolve parameter $ref '{ref_path}'")
                return param_node_data  # Return original ref node if resolution fails
    return param_node_data  # Not a ref or not a component parameter ref


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _build_schemas(raw_schemas: Mapping[str, Any], raw_components: Mapping[str, Any]) -> ParsingContext:
    """Build all named schemas up front, populating a ParsingContext."""
    context = ParsingContext(raw_spec_schemas=raw_schemas, raw_spec_components=raw_components)
    for n, nd in raw_schemas.items():
        if n not in context.parsed_schemas:
            _parse_schema(n, nd, context)
    return context


def _parse_parameter(
    node: Mapping[str, Any],
    context: ParsingContext,
) -> IRParameter:
    """Convert an OpenAPI parameter node into IRParameter."""
    sch = node.get("schema")
    schema_ir = _parse_schema(None, sch, context) if sch else IRSchema(name=None)
    return IRParameter(
        name=node["name"],
        param_in=node.get("in", "query"),
        required=bool(node.get("required", False)),
        schema=schema_ir,
        description=node.get("description"),
    )


def _parse_response(
    code: str,
    node: Mapping[str, Any],
    context: ParsingContext,
) -> IRResponse:
    """Convert an OpenAPI response node into IRResponse."""
    content: Dict[str, IRSchema] = {}
    STREAM_FORMATS = {
        "application/octet-stream": "octet-stream",
        "text/event-stream": "event-stream",
        "application/x-ndjson": "ndjson",
        "application/json-seq": "json-seq",
        "multipart/mixed": "multipart-mixed",
    }
    stream_flag = False
    stream_format = None
    for mt, mn in node.get("content", {}).items():
        if isinstance(mn, Mapping) and "$ref" in mn:
            ref = mn["$ref"]
            if not ref.startswith("#/components/schemas/"):
                content[mt] = IRSchema(name=None, _from_unresolved_ref=True)
            else:
                content[mt] = _parse_schema(None, {"$ref": ref}, context)
        else:
            content[mt] = _parse_schema(None, mn.get("schema"), context)
        fmt = STREAM_FORMATS.get(mt.lower())
        if fmt:
            stream_flag = True
            stream_format = fmt
    if not stream_flag:
        for mt_val, schema_val in content.items():
            if getattr(schema_val, "format", None) == "binary":
                stream_flag = True
                stream_format = "octet-stream"
    return IRResponse(
        status_code=code,
        description=node.get("description"),
        content=content,
        stream=stream_flag,
        stream_format=stream_format,
    )


def _parse_operations(
    paths: Mapping[str, Any],
    raw_parameters: Mapping[str, Any],
    raw_responses: Mapping[str, Any],
    raw_request_bodies: Mapping[str, Any],
    context: ParsingContext,
) -> List[IROperation]:
    """Iterate paths to build IROperation list."""
    ops: List[IROperation] = []
    for path, item in paths.items():
        if not isinstance(item, Mapping):
            continue
        entry = cast(Mapping[str, Any], item)
        base_params: List[IRParameter] = []
        for p_node_data_raw in cast(List[Mapping[str, Any]], entry.get("parameters", [])):
            # Resolve $ref before parsing
            resolved_p_node_data = _resolve_parameter_node_if_ref(p_node_data_raw, context)
            base_params.append(_parse_parameter(resolved_p_node_data, context))
        for method, on in entry.items():
            try:
                if method in {
                    "parameters",
                    "summary",
                    "description",
                    "servers",
                    "$ref",
                }:
                    continue
                mu = method.upper()
                if mu not in HTTPMethod.__members__:
                    continue
                node_op = cast(Mapping[str, Any], on)
                params: List[IRParameter] = list(base_params)
                for p_param_node_raw in cast(List[Mapping[str, Any]], node_op.get("parameters", [])):
                    # Resolve $ref before parsing
                    resolved_p_param_node = _resolve_parameter_node_if_ref(p_param_node_raw, context)
                    params.append(_parse_parameter(resolved_p_param_node, context))
                rb: Optional[IRRequestBody] = None
                if "requestBody" in node_op:
                    rb_node = cast(Mapping[str, Any], node_op["requestBody"])
                    if (
                        "$ref" in rb_node
                        and isinstance(rb_node.get("$ref"), str)
                        and rb_node["$ref"].startswith("#/components/requestBodies/")
                    ):
                        ref_name = rb_node["$ref"].split("/")[-1]
                        rb_node = raw_request_bodies.get(ref_name, {}) or rb_node
                    required_flag = bool(rb_node.get("required", False))
                    desc = rb_node.get("description")
                    content_map: Dict[str, IRSchema] = {}
                    for mt, media in rb_node.get("content", {}).items():
                        content_map[mt] = _parse_schema(None, media.get("schema"), context)
                    rb = IRRequestBody(required=required_flag, content=content_map, description=desc)
                resps: List[IRResponse] = []
                for sc, rn_node in cast(Mapping[str, Any], node_op.get("responses", {})).items():
                    if (
                        isinstance(rn_node, Mapping)
                        and "$ref" in rn_node
                        and isinstance(rn_node.get("$ref"), str)
                        and rn_node["$ref"].startswith("#/components/responses/")
                    ):
                        ref_name = rn_node["$ref"].split("/")[-1]
                        resp_node = raw_responses.get(ref_name, {}) or rn_node
                    else:
                        resp_node = rn_node
                    resps.append(_parse_response(sc, resp_node, context))
                if "operationId" in node_op:
                    operation_id = node_op["operationId"]
                else:
                    operation_id = NameSanitizer.sanitize_method_name(f"{mu}_{path}".strip("/"))
                op = IROperation(
                    operation_id=operation_id,
                    method=HTTPMethod[mu],
                    path=path,
                    summary=node_op.get("summary"),
                    description=node_op.get("description"),
                    parameters=params,
                    request_body=rb,
                    responses=resps,
                    tags=list(node_op.get("tags", [])),
                )
            except Exception as e:
                warnings.warn(
                    f"Skipping operation parsing for {method.upper()} {path}: {e}",
                    UserWarning,
                )
                continue
            else:
                if rb:
                    for _, sch_val in rb.content.items():
                        if not sch_val.name:
                            generated_rb_name = NameSanitizer.sanitize_class_name(
                                node_op.get("operationId", operation_id) + "Request"
                            )
                            sch_val.name = generated_rb_name
                            context.parsed_schemas[generated_rb_name] = sch_val
                        elif sch_val.name not in context.parsed_schemas:
                            context.parsed_schemas[sch_val.name] = sch_val

                for resp_val in resps:
                    for _, sch_resp_val in resp_val.content.items():
                        if sch_resp_val.name is None:
                            if getattr(sch_resp_val, "_from_unresolved_ref", False):
                                continue
                            is_streaming = getattr(resp_val, "stream", False)
                            if is_streaming:
                                continue

                            should_synthesize_name = False
                            if sch_resp_val.type == "object" and (
                                sch_resp_val.properties or sch_resp_val.additional_properties
                            ):
                                should_synthesize_name = True

                            if should_synthesize_name:
                                generated_name = NameSanitizer.sanitize_class_name(
                                    node_op.get("operationId", operation_id) + "Response"
                                )
                                sch_resp_val.name = generated_name
                                context.parsed_schemas[generated_name] = sch_resp_val

                        elif sch_resp_val.name and sch_resp_val.name not in context.parsed_schemas:
                            context.parsed_schemas[sch_resp_val.name] = sch_resp_val

                ops.append(op)
    return ops


def extract_inline_enums(schemas: Dict[str, IRSchema]) -> Dict[str, IRSchema]:
    """Extract inline property enums as unique schemas and update property references."""
    new_enums = {}
    for schema_name, schema in list(schemas.items()):
        for prop_name, prop_schema in list(schema.properties.items()):
            if prop_schema.enum and not prop_schema.name:
                enum_name = f"{NameSanitizer.sanitize_class_name(schema_name)}{NameSanitizer.sanitize_class_name(prop_name)}Enum"
                base_enum_name = enum_name
                i = 1
                while enum_name in schemas or enum_name in new_enums:
                    enum_name = f"{base_enum_name}{i}"
                    i += 1

                enum_schema = IRSchema(
                    name=enum_name,
                    type=prop_schema.type,
                    enum=copy.deepcopy(prop_schema.enum),
                    description=prop_schema.description or f"Enum for {schema_name}.{prop_name}",
                )
                new_enums[enum_name] = enum_schema
                prop_schema.name = enum_name
    schemas.update(new_enums)
    return schemas


def load_ir_from_spec(spec: Mapping[str, Any]) -> IRSpec:
    """Orchestrate the transformation of a spec dict into IRSpec."""
    # Validate OpenAPI spec but continue on errors
    if validate_spec is not None:
        try:
            from typing import Hashable

            validate_spec(cast(Mapping[Hashable, Any], spec))
        except Exception as e:
            warnings.warn(f"OpenAPI spec validation error: {e}", UserWarning)
    if "openapi" not in spec:
        raise ValueError("Missing 'openapi' field in the specification.")
    if "paths" not in spec:
        raise ValueError("Missing 'paths' section in the specification.")
    info = spec.get("info", {})
    title = info.get("title", "API Client")
    version = info.get("version", "0.0.0")
    description = info.get("description")
    raw_components = spec.get("components", {})
    raw_schemas = raw_components.get("schemas", {})
    raw_parameters = raw_components.get("parameters", {})
    raw_responses = raw_components.get("responses", {})
    raw_request_bodies = raw_components.get("requestBodies", {})

    # Pass raw_components when building schemas / creating context
    context = _build_schemas(raw_schemas, raw_components)

    # Extract schemas dict from the context for further processing
    schemas_dict = context.parsed_schemas
    schemas_dict = extract_inline_enums(schemas_dict)

    paths = spec["paths"]
    # Pass the populated context to _parse_operations
    operations = _parse_operations(
        paths,
        raw_parameters,
        raw_responses,
        raw_request_bodies,
        context,
    )
    servers = [s.get("url") for s in spec.get("servers", []) if "url" in s]

    # Emit collected warnings after all parsing is done
    for warning_msg in context.collected_warnings:
        warnings.warn(warning_msg, UserWarning)

    return IRSpec(
        title=title,
        version=version,
        description=description,
        schemas=schemas_dict,
        operations=operations,
        servers=servers,
    )
