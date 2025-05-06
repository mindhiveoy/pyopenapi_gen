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
import sys
import warnings
from typing import Any, Dict, List, Mapping, Optional, cast

try:
    # Use the newer validate() API if available to avoid deprecation warnings
    from openapi_spec_validator import validate as validate_spec
except ImportError:
    try:
        from openapi_spec_validator import validate_spec  # type: ignore
    except ImportError:  # pragma: no cover – optional in early bootstrapping
        validate_spec = None  # type: ignore[assignment]
# Disable strict spec validation by default to allow lenient parsing

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
    """Recursively parse a schema node, resolving refs and composition keywords."""
    if _visited is None:
        _visited = set()
    if node is None:
        # Handle cases where a schema node might be null (e.g., invalid spec)
        return IRSchema(name=name)

    # --- Handle $ref --- (Prioritize over other keywords)
    if "$ref" in node:
        ref = node["$ref"]
        if ref.startswith("#/components/schemas/"):
            ref_name = ref.rsplit("/", 1)[-1]
            if ref_name in schemas:
                # Already parsed or being parsed (cycle)
                return schemas[ref_name]
            if ref_name in _visited:
                # Cycle detected, return placeholder to break recursion
                return IRSchema(name=ref_name)  # Mark as placeholder?

            _visited.add(ref_name)
            referenced = raw_schemas.get(ref_name)
            if referenced is None:
                warnings.warn(f"Could not resolve $ref: {ref}", UserWarning)
                return IRSchema(name=ref_name, _from_unresolved_ref=True)

            schema_obj = _parse_schema(ref_name, referenced, raw_schemas, schemas, _visited)
            # Store the fully parsed schema only if it's not just a cycle placeholder
            if not schema_obj._from_unresolved_ref:
                schemas[ref_name] = schema_obj
            _visited.remove(ref_name)
            return schema_obj
        else:
            # Non-schema ref or invalid ref format
            warnings.warn(f"Unsupported or invalid $ref format: {ref}", UserWarning)
            return IRSchema(name=None, _from_unresolved_ref=True)

    # --- Initialize IRSchema fields --- (Defaults)
    schema_type: Optional[str] = None
    is_nullable: bool = False
    any_of_schemas: Optional[List[IRSchema]] = None
    one_of_schemas: Optional[List[IRSchema]] = None
    all_of_schemas: Optional[List[IRSchema]] = None

    # --- Handle Composition Keywords (anyOf, oneOf, allOf) ---
    if "anyOf" in node:
        any_of_schemas = [_parse_schema(None, sub, raw_schemas, schemas, _visited) for sub in node["anyOf"]]
        # Check for nullability within anyOf
        # Explicitly check the raw sub-schema for {type: "null"}
        if any(isinstance(sub, dict) and sub.get("type") == "null" for sub in node["anyOf"]):
            is_nullable = True
            # Filter out the null type schema from the parsed list
            # Note: This assumes the parsed null schema will have schema.type == None or similar
            # We might need a more robust way to identify the parsed null schema if type becomes Any
            any_of_schemas = [
                s
                for s in any_of_schemas
                if not (
                    s.type is None
                    and not s.properties
                    and not s.items
                    and not s.enum
                    and not s.any_of
                    and not s.one_of
                    and not s.all_of
                )
            ]  # Heuristic to find the parsed null

            # If only null was present, it's just a nullable type, not a Union
            if not any_of_schemas:
                # What should the base type be? Use 'Any' or try to infer?
                # For now, let's just mark nullable and maybe visitor uses 'Any'
                schema_type = None  # Or 'Any'?
                any_of_schemas = None  # Reset as it's not a Union anymore

    if "oneOf" in node:
        one_of_schemas = [_parse_schema(None, sub, raw_schemas, schemas, _visited) for sub in node["oneOf"]]
        # Nullability check for oneOf might be less common but possible
        if any(s.type == "null" for s in one_of_schemas):
            is_nullable = True
            one_of_schemas = [s for s in one_of_schemas if s.type != "null"]
            if not one_of_schemas:
                schema_type = None
                one_of_schemas = None

    if "allOf" in node:
        # Store sub-schemas, delegate merging/interpretation to visitor
        all_of_schemas = [_parse_schema(None, sub, raw_schemas, schemas, _visited) for sub in node["allOf"]]

    # --- Determine Primary Type and Nullability --- (if not set by composition)
    raw_type = node.get("type")
    if schema_type is None and not any_of_schemas and not one_of_schemas:
        if isinstance(raw_type, list):
            # Handles `type: ["string", "null"]`
            if "null" in raw_type:
                is_nullable = True
            # Find the first non-null type as the primary type
            primary_types = [t for t in raw_type if t != "null"]
            if primary_types:
                schema_type = primary_types[0]
                if len(primary_types) > 1:
                    warnings.warn(
                        f"Schema '{name or 'anonymous'}' has multiple non-null types ({primary_types}) "
                        f"in 'type' array. Using first type '{schema_type}'.",
                        UserWarning,
                    )
            else:
                # Only "null" was present
                schema_type = None  # Represent as nullable Any
        elif isinstance(raw_type, str):
            if raw_type == "null":
                is_nullable = True
                schema_type = None  # Represent as nullable Any
            else:
                schema_type = raw_type

    # --- Parse other standard keywords ---
    raw_required = node.get("required")
    required_fields = cast(List[str], raw_required) if isinstance(raw_required, list) else []
    properties = {
        key: _parse_schema(None, val, raw_schemas, schemas, _visited) for key, val in node.get("properties", {}).items()
    }
    items = node.get("items")
    items_schema = _parse_schema(None, items, raw_schemas, schemas, _visited) if items is not None else None
    enum_values = node.get("enum")

    # <<< Start: Parse additionalProperties >>>
    raw_add_props = node.get("additionalProperties")
    add_props_value: Optional[bool | IRSchema] = None
    if isinstance(raw_add_props, bool):
        add_props_value = raw_add_props
    elif isinstance(raw_add_props, dict):
        add_props_value = _parse_schema(None, raw_add_props, raw_schemas, schemas, _visited)
    # <<< End: Parse additionalProperties >>>

    # --- Data wrapper detection --- (Keep existing logic)
    is_data_wrapper = schema_type == "object" and "data" in properties and "data" in required_fields

    # --- Construct final IRSchema --- (using potentially updated fields)
    return IRSchema(
        name=name,
        type=schema_type,
        format=node.get("format"),
        required=required_fields,
        properties=properties,
        items=items_schema,
        enum=enum_values,
        description=node.get("description"),
        # New fields
        is_nullable=is_nullable,
        any_of=any_of_schemas,
        one_of=one_of_schemas,
        all_of=all_of_schemas,
        additional_properties=add_props_value,
        # Other flags
        is_data_wrapper=is_data_wrapper,
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
    schema = _parse_schema(None, sch, raw_schemas, schemas) if sch else IRSchema(name=None)
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
        # Handle $ref directly in the content object (not just in the schema)
        if isinstance(mn, Mapping) and "$ref" in mn:
            # If the $ref cannot be resolved, treat as unresolved
            ref = mn["$ref"]
            # Only handle unresolved $ref (not #/components/schemas/)
            if not ref.startswith("#/components/schemas/"):
                content[mt] = IRSchema(name=None, _from_unresolved_ref=True)
            else:
                # If it's a schema ref, parse as schema
                content[mt] = _parse_schema(None, {"$ref": ref}, raw_schemas, schemas)
        else:
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
            if "$ref" in p and isinstance(p.get("$ref"), str) and p["$ref"].startswith("#/components/parameters/"):
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
                        content_map[mt] = _parse_schema(None, media.get("schema"), raw_schemas, schemas)
                    rb = IRRequestBody(required=required_flag, content=content_map, description=desc)
                # Build responses
                resps: List[IRResponse] = []
                for sc, rn in cast(Mapping[str, Any], node.get("responses", {})).items():
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
                if "operationId" in node:
                    operation_id = node["operationId"]
                else:
                    operation_id = NameSanitizer.sanitize_method_name(f"{mu}_{path}".strip("/"))
                op = IROperation(
                    operation_id=operation_id,
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
                            # Use the raw operation_id (not sanitized) + 'Request', then sanitize once
                            generated_rb_name = NameSanitizer.sanitize_class_name(
                                node.get("operationId", operation_id) + "Request"
                            )
                            sch.name = generated_rb_name
                            schemas[generated_rb_name] = sch
                        else:
                            # Ensure all referenced request body schemas are in schemas dict
                            if sch.name not in schemas:
                                schemas[sch.name] = sch

                # Assign names to inline response schemas for model generation
                for resp in resps:
                    for mt, sch in resp.content.items():
                        # Only assign a name if sch.name is None and not from unresolved $ref
                        if sch.name is None:
                            if getattr(sch, "_from_unresolved_ref", False):
                                # Defensive: never assign a name to unresolved $ref schemas
                                continue
                            is_streaming = getattr(resp, "stream", False)
                            # PATCH: Only assign a name for streaming responses if schema is a global, named schema
                            if is_streaming:
                                # If this schema is not a global component (i.e., not in schemas), skip naming
                                # Inline objects (even with properties) should not get a name for streaming
                                continue
                            # Use the raw operation_id (not sanitized) + 'Response', then sanitize once
                            generated_name = NameSanitizer.sanitize_class_name(
                                node.get("operationId", operation_id) + "Response"
                            )
                            sch.name = generated_name
                            schemas[generated_name] = sch
                        else:
                            # Ensure all referenced response schemas are in schemas dict
                            if sch.name not in schemas:
                                schemas[sch.name] = sch
                ops.append(op)
    return ops


def extract_inline_enums(schemas: Dict[str, IRSchema]) -> Dict[str, IRSchema]:
    """Extract inline property enums as unique schemas and update property references."""
    new_enums = {}
    for schema_name, schema in list(schemas.items()):
        for prop_name, prop_schema in list(schema.properties.items()):
            if prop_schema.enum and not prop_schema.name:
                # Generate a unique name
                enum_name = f"{NameSanitizer.sanitize_class_name(schema_name)}{NameSanitizer.sanitize_class_name(prop_name)}Enum"
                # Avoid collision
                base_enum_name = enum_name
                i = 1
                while enum_name in schemas or enum_name in new_enums:
                    enum_name = f"{base_enum_name}{i}"
                    i += 1

                # Create a new IRSchema for the enum
                enum_schema = IRSchema(
                    name=enum_name,
                    type=prop_schema.type,
                    enum=copy.deepcopy(prop_schema.enum),
                    description=prop_schema.description or f"Enum for {schema_name}.{prop_name}",
                )
                new_enums[enum_name] = enum_schema
                # Update the property to reference the new enum
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
    raw_schemas = spec.get("components", {}).get("schemas", {})
    raw_parameters = spec.get("components", {}).get("parameters", {})
    raw_responses = spec.get("components", {}).get("responses", {})
    raw_request_bodies = spec.get("components", {}).get("requestBodies", {})
    schemas = _build_schemas(raw_schemas)
    schemas = extract_inline_enums(schemas)
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
        description=description,
        schemas=schemas,
        operations=operations,
        servers=servers,
    )
