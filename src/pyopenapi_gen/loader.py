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

from typing import Any, Dict, List, Mapping, Optional, cast
import warnings

try:
    # Use the newer validate() API if available to avoid deprecation warnings
    from openapi_spec_validator import validate as validate_spec
except ImportError:
    try:
        from openapi_spec_validator import validate_spec  # type: ignore
    except ImportError:  # pragma: no cover – optional in early bootstrapping
        validate_spec = None  # type: ignore[assignment]
# Disable strict spec validation by default to allow lenient parsing
validate_spec = None  # override imported validate_spec

from . import (
    HTTPMethod,
    IRParameter,
    IRResponse,
    IRRequestBody,
    IROperation,
    IRSchema,
    IRSpec,
)
from .utils import NameSanitizer  # Import for naming inline response schemas

__all__ = ["load_ir_from_spec"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _parse_schema(
    name: Optional[str],
    node: Optional[Mapping[str, Any]],
    raw_schemas: Mapping[str, Any],
    schemas: Dict[str, IRSchema],
    _visited: Optional[set[str]] = None,
) -> IRSchema:
    """Recursively parse a schema node, resolving limited $ref links."""
    if _visited is None:
        _visited = set()
    if node is None:
        return IRSchema(name=name)
    # Handle allOf composition before $ref resolution to merge sub-schemas' properties
    if "allOf" in node:
        # Determine name: use provided name or derive from first $ref
        comp_name = name
        for sub in node["allOf"]:
            if (
                isinstance(sub, Mapping)
                and "$ref" in sub
                and sub["$ref"].startswith("#/components/schemas/")
            ):
                comp_name = sub["$ref"].rsplit("/", 1)[-1]
                break
        combined_required: List[str] = []
        combined_properties: Dict[str, IRSchema] = {}
        combined_items = None
        combined_enum = None
        combined_description = node.get("description")
        for sub in node["allOf"]:
            sub_schema = _parse_schema(None, sub, raw_schemas, schemas, _visited)
            # Merge required and properties
            combined_required.extend(sub_schema.required)
            combined_properties.update(sub_schema.properties)
            # Merge items
            if sub_schema.items:
                combined_items = sub_schema.items
            # Merge enum
            if sub_schema.enum is not None:
                combined_enum = sub_schema.enum
            # Merge description if missing
            if not combined_description and sub_schema.description:
                combined_description = sub_schema.description
        # Deduplicate
        combined_required = list(dict.fromkeys(combined_required))
        # Construct composed schema
        composed = IRSchema(
            name=comp_name,
            type="object",
            format=None,
            required=combined_required,
            properties=combined_properties,
            items=combined_items,
            enum=combined_enum,
            description=combined_description,
        )
        # Update schemas mapping for named compositions
        if comp_name:
            schemas[comp_name] = composed
        return composed
    if "$ref" in node:
        ref = node["$ref"]
        if ref.startswith("#/components/schemas/"):
            ref_name = ref.rsplit("/", 1)[-1]
            if ref_name in schemas:
                return schemas[ref_name]
            if ref_name in _visited:
                return IRSchema(name=ref_name)
            _visited.add(ref_name)
            referenced = raw_schemas.get(ref_name, {})
            schema_obj = _parse_schema(
                ref_name, referenced, raw_schemas, schemas, _visited
            )
            schemas[ref_name] = schema_obj
            return schema_obj
        return IRSchema(name=name)
    raw_required = node.get("required")
    required_fields = (
        cast(List[str], raw_required) if isinstance(raw_required, list) else []
    )
    properties = {
        key: _parse_schema(None, val, raw_schemas, schemas, _visited)
        for key, val in node.get("properties", {}).items()
    }
    items = node.get("items")
    items_schema = (
        _parse_schema(None, items, raw_schemas, schemas, _visited)
        if items is not None
        else None
    )
    return IRSchema(
        name=name,
        type=node.get("type"),
        format=node.get("format"),
        required=required_fields,
        properties=properties,
        items=items_schema,
        enum=node.get("enum"),
        description=node.get("description"),
    )


def _build_schemas(raw_schemas: Mapping[str, Any]) -> Dict[str, IRSchema]:
    """Build all named schemas up front for $ref resolution."""
    schemas: Dict[str, IRSchema] = {}
    for n, nd in raw_schemas.items():
        schemas[n] = _parse_schema(n, nd, raw_schemas, schemas)
    return schemas


def _parse_parameter(
    node: Mapping[str, Any],
    raw_schemas: Mapping[str, Any],
    schemas: Dict[str, IRSchema],
) -> IRParameter:
    """Convert an OpenAPI parameter node into IRParameter."""
    sch = node.get("schema")
    schema = (
        _parse_schema(None, sch, raw_schemas, schemas) if sch else IRSchema(name=None)
    )
    return IRParameter(
        name=node["name"],
        in_=node.get("in", "query"),
        required=bool(node.get("required", False)),
        schema=schema,
        description=node.get("description"),
    )


def _parse_response(
    code: str,
    node: Mapping[str, Any],
    raw_schemas: Mapping[str, Any],
    schemas: Dict[str, IRSchema],
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
        content[mt] = _parse_schema(None, mn.get("schema"), raw_schemas, schemas)
        fmt = STREAM_FORMATS.get(mt.lower())
        if fmt:
            stream_flag = True
            stream_format = fmt
    # Also support OpenAPI 'format: binary' for legacy compatibility
    if not stream_flag:
        for mt, schema in content.items():
            if getattr(schema, "format", None) == "binary":
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
    raw_schemas: Mapping[str, Any],
    raw_parameters: Mapping[str, Any],
    raw_responses: Mapping[str, Any],
    raw_request_bodies: Mapping[str, Any],
    schemas: Dict[str, IRSchema],
) -> List[IROperation]:
    """Iterate paths to build IROperation list."""
    ops: List[IROperation] = []
    for path, item in paths.items():
        if not isinstance(item, Mapping):
            continue
        entry = cast(Mapping[str, Any], item)
        base_params: List[IRParameter] = []
        for p in cast(List[Mapping[str, Any]], entry.get("parameters", [])):
            # Resolve parameter $ref if present (skip if unresolved)
            if (
                "$ref" in p
                and isinstance(p.get("$ref"), str)
                and p["$ref"].startswith("#/components/parameters/")
            ):
                ref_name = p["$ref"].split("/")[-1]
                if ref_name in raw_parameters:
                    p_node = raw_parameters[ref_name]
                else:
                    warnings.warn(
                        f"Unable to resolve parameter reference {p['$ref']}, skipping",
                        UserWarning,
                    )
                    continue
            else:
                p_node = p
            base_params.append(_parse_parameter(p_node, raw_schemas, schemas))
        for method, on in entry.items():
            # Attempt to parse operation; on error, emit warning and skip
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
                node = cast(Mapping[str, Any], on)
                # Build parameters list
                params: List[IRParameter] = list(base_params)
                for p in cast(List[Mapping[str, Any]], node.get("parameters", [])):
                    # Resolve parameter $ref if present (skip if unresolved)
                    if (
                        "$ref" in p
                        and isinstance(p.get("$ref"), str)
                        and p["$ref"].startswith("#/components/parameters/")
                    ):
                        ref_name = p["$ref"].split("/")[-1]
                        if ref_name in raw_parameters:
                            p_node = raw_parameters[ref_name]
                        else:
                            warnings.warn(
                                f"Unable to resolve parameter reference {p['$ref']}, skipping",
                                UserWarning,
                            )
                            continue
                    else:
                        p_node = p
                    params.append(_parse_parameter(p_node, raw_schemas, schemas))
                # Build request body
                rb: Optional[IRRequestBody] = None
                if "requestBody" in node:
                    rb_node = cast(Mapping[str, Any], node["requestBody"])
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
                        content_map[mt] = _parse_schema(
                            None, media.get("schema"), raw_schemas, schemas
                        )
                    rb = IRRequestBody(
                        required=required_flag, content=content_map, description=desc
                    )
                # Build responses
                resps: List[IRResponse] = []
                for sc, rn in cast(
                    Mapping[str, Any], node.get("responses", {})
                ).items():
                    if (
                        isinstance(rn, Mapping)
                        and "$ref" in rn
                        and isinstance(rn.get("$ref"), str)
                        and rn["$ref"].startswith("#/components/responses/")
                    ):
                        ref_name = rn["$ref"].split("/")[-1]
                        resp_node = raw_responses.get(ref_name, {}) or rn
                    else:
                        resp_node = rn
                    resps.append(_parse_response(sc, resp_node, raw_schemas, schemas))
                # Create operation object and append
                op = IROperation(
                    operation_id=node.get("operationId", f"{mu}_{path}".strip("/")),
                    method=HTTPMethod[mu],
                    path=path,
                    summary=node.get("summary"),
                    description=node.get("description"),
                    parameters=params,
                    request_body=rb,
                    responses=resps,
                    tags=list(node.get("tags", [])),
                )
            except Exception as e:
                warnings.warn(
                    f"Skipping operation parsing for {method.upper()} {path}: {e}",
                    UserWarning,
                )
                continue
            else:
                # Assign names to inline request body schemas for model generation
                if rb:
                    for mt, sch in rb.content.items():
                        if not sch.name:
                            generated_rb_name = NameSanitizer.sanitize_class_name(
                                op.operation_id + "Request"
                            )
                            sch.name = generated_rb_name
                            schemas[generated_rb_name] = sch

                # Assign names to inline response schemas for model generation
                for resp in resps:
                    for mt, sch in resp.content.items():
                        if not sch.name:
                            generated_name = NameSanitizer.sanitize_class_name(
                                op.operation_id + "Response"
                            )
                            sch.name = generated_name
                            schemas[generated_name] = sch
                ops.append(op)
    return ops


def load_ir_from_spec(spec: Mapping[str, Any]) -> IRSpec:
    """Orchestrate the transformation of a spec dict into IRSpec."""
    # Validate OpenAPI spec but continue on errors
    if validate_spec is not None:
        try:
            validate_spec(spec)
        except Exception as e:
            warnings.warn(f"OpenAPI spec validation error: {e}", UserWarning)
    if "openapi" not in spec:
        raise ValueError("Missing 'openapi' field in the specification.")
    if "paths" not in spec:
        raise ValueError("Missing 'paths' section in the specification.")
    info = spec.get("info", {})
    title = info.get("title", "API Client")
    version = info.get("version", "0.0.0")
    raw_schemas = spec.get("components", {}).get("schemas", {})
    raw_parameters = spec.get("components", {}).get("parameters", {})
    raw_responses = spec.get("components", {}).get("responses", {})
    raw_request_bodies = spec.get("components", {}).get("requestBodies", {})
    schemas = _build_schemas(raw_schemas)
    paths = spec["paths"]
    operations = _parse_operations(
        paths,
        raw_schemas,
        raw_parameters,
        raw_responses,
        raw_request_bodies,
        schemas,
    )
    servers = [s.get("url") for s in spec.get("servers", []) if "url" in s]
    return IRSpec(
        title=title,
        version=version,
        schemas=schemas,
        operations=operations,
        servers=servers,
    )
