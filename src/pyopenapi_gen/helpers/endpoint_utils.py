"""
Helpers for endpoint code generation: parameter/type analysis, code writing, etc.
Used by EndpointVisitor and related emitters.
"""

from typing import Any, Dict, List, Optional

from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext

from ..core.utils import NameSanitizer


def get_params(op: IROperation, context: RenderContext) -> List[Dict[str, Any]]:
    """
    Returns a list of dicts with name, type, default, and required for template rendering.
    """
    params = []
    for param in op.parameters:
        py_type = get_param_type(param, context)
        default = None if param.required else "None"
        params.append({
            "name": NameSanitizer.sanitize_method_name(param.name),
            "type": py_type,
            "default": default,
            "required": param.required,
        })
    return params


def get_param_type(param: IRParameter, context: RenderContext) -> str:
    s = param.schema
    # If schema is a named model, use the class name
    if getattr(s, "name", None):
        class_name = NameSanitizer.sanitize_class_name(s.name)
        # Use correct module path for models from endpoints
        model_module = f"models.{NameSanitizer.sanitize_module_name(s.name)}"
        context.add_import(model_module, class_name)
        py_type = class_name
    elif s.type == "array" and s.items:
        item_type = get_param_type(IRParameter(name="", in_="", required=False, schema=s.items), context)
        py_type = f"List[{item_type}]"
    elif s.type == "object" and s.properties:
        py_type = "Dict[str, Any]"
    elif s.type in ("integer", "number", "boolean", "string"):
        py_type = {
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "string": "str",
        }[s.type]
    else:
        py_type = "Any"
    if not param.required:
        py_type = f"Optional[{py_type}]"
    return py_type


def get_request_body_type(body: IRRequestBody, context: RenderContext) -> str:
    """
    Determine the Python type for a request body schema (prefer model class if available).
    """
    for mt, sch in body.content.items():
        if "json" in mt.lower():
            # If schema is a named model, use the class name
            if getattr(sch, "name", None):
                class_name = NameSanitizer.sanitize_class_name(sch.name)
                model_module = f"models.{NameSanitizer.sanitize_module_name(sch.name)}"
                context.add_import(model_module, class_name)
                return class_name
            # If array of models
            if sch.type == "array" and getattr(sch.items, "name", None):
                item_class = NameSanitizer.sanitize_class_name(sch.items.name)
                model_module = f"models.{NameSanitizer.sanitize_module_name(sch.items.name)}"
                context.add_import(model_module, item_class)
                return f"List[{item_class}]"
            # If generic object
            if sch.type == "object":
                return "Dict[str, Any]"
            # Otherwise, fallback
            return get_param_type(
                IRParameter(
                    name="body",
                    in_="body",
                    required=body.required,
                    schema=sch,
                ),
                context,
            )
    return "Dict[str, Any]"


def get_return_type(
    op: IROperation,
    context: RenderContext,
    schemas: dict = None,
) -> str:
    """
    Determine the Python return type for the endpoint method based on the operation's responses.
    - Prefer 200/2xx responses, then default, then any.
    - If the response schema is a primitive, use the correct Python type.
    - If the response schema is a model, use the model class name and add import.
    - If the response is a list, use List[Model] or List[Type].
    - If the response is a stream, use AsyncIterator[Type].
    - If no schema, fallback to Any.
    """
    schemas = schemas or {}

    def schema_to_pytype(schema, context):
        if not schema:
            return "Any"
        # Only treat as model if name is present in schemas
        if getattr(schema, "name", None) and schema.name in schemas:
            class_name = NameSanitizer.sanitize_class_name(schema.name)
            model_module = f"models.{NameSanitizer.sanitize_module_name(schema.name)}"
            context.add_import(model_module, class_name)
            return class_name
        if schema.type == "array" and getattr(schema.items, "name", None) and schema.items.name in schemas:
            item_class = NameSanitizer.sanitize_class_name(schema.items.name)
            context.add_import(
                f"models.{NameSanitizer.sanitize_module_name(schema.items.name)}",
                item_class,
            )
            return f"List[{item_class}]"
        if schema.type == "array" and schema.items:
            item_type = schema_to_pytype(schema.items, context)
            return f"List[{item_type}]"
        # PATCH: For binary streaming, return bytes
        if schema.type == "string" and getattr(schema, "format", None) == "binary":
            return "bytes"
        # PATCH: For inline object schemas, only use Dict[str, Any] if no name and no properties
        if schema.type == "object":
            if getattr(schema, "properties", None):
                return "Dict[str, Any]"
            # If no properties and no name, fallback to Any
            return "Any"
        if schema.type in ("integer", "number", "boolean", "string"):
            return {
                "integer": "int",
                "number": "float",
                "boolean": "bool",
                "string": "str",
            }[schema.type]
        return "Any"

    # Prefer 200, then first 2xx, then default, then any
    resp: Optional[IRResponse] = None
    for code in (
        ["200"]
        + [r.status_code for r in op.responses if r.status_code.startswith("2") and r.status_code != "200"]
        + ["default"]
    ):
        resp = next((r for r in op.responses if r.status_code == code), None)
        if resp:
            break
    if not resp and op.responses:
        resp = op.responses[0]
    if not resp or not resp.content:
        return "Any"
    # Pick first content type (prefer application/json, then event-stream, then any)
    content_types = list(resp.content.keys())
    mt = next(
        (ct for ct in content_types if "json" in ct),
        next((ct for ct in content_types if "event-stream" in ct), content_types[0]),
    )
    schema = resp.content[mt]
    # Streaming response
    if getattr(resp, "stream", False):
        # Only use a named model if schema is a global, named schema (present in schemas)
        is_global_named_model = getattr(schema, "name", None) and schema.name in schemas
        if is_global_named_model:
            item_type = schema_to_pytype(schema, context)
            return f"AsyncIterator[{item_type}]"
        # For all inline object schemas (even with properties), use Dict[str, Any]
        if schema.type == "object":
            return "AsyncIterator[Dict[str, Any]]"
        # If binary
        if schema.type == "string" and getattr(schema, "format", None) == "binary":
            return "AsyncIterator[bytes]"
        # Fallback
        return "AsyncIterator[Any]"
    # List response
    if schema.type == "array" and getattr(schema.items, "name", None) and schema.items.name in schemas:
        item_class = NameSanitizer.sanitize_class_name(schema.items.name)
        context.add_import(
            f"models.{NameSanitizer.sanitize_module_name(schema.items.name)}",
            item_class,
        )
        return f"List[{item_class}]"
    if schema.type == "array" and schema.items:
        item_type = schema_to_pytype(schema.items, context)
        return f"List[{item_type}]"
    # Model or primitive
    return schema_to_pytype(schema, context)


def format_method_args(params: list[dict[str, Any]]) -> str:
    """
    Format a list of parameter dicts into a Python function argument string (excluding
    'self'). Each dict must have: name, type, default (None or string), required (bool).
    Required params come first, then optional params with defaults.
    """
    required = [p for p in params if p.get("required", True)]
    optional = [p for p in params if not p.get("required", True)]
    arg_strs = []
    for p in required:
        arg_strs.append(f"{p['name']}: {p['type']}")
    for p in optional:
        default = p["default"]
        arg_strs.append(f"{p['name']}: {p['type']} = {default}")
    return ", ".join(arg_strs)


def get_model_stub_args(schema: IRSchema, context: RenderContext, present_args: set[str]) -> str:
    """
    Generate a string of arguments for instantiating a model.
    For each required field, use the variable if present in present_args, otherwise use
    a safe default. For optional fields, use None.
    """
    if not hasattr(schema, "properties") or not schema.properties:
        return ""
    args = []
    for prop, pschema in schema.properties.items():
        is_required = prop in getattr(schema, "required", [])
        py_type = pschema.type if hasattr(pschema, "type") else None
        if prop in present_args:
            args.append(f"{prop}={prop}")
        elif is_required:
            # Safe defaults for required fields
            if py_type == "string":
                args.append(f'{prop}=""')
            elif py_type == "integer":
                args.append(f"{prop}=0")
            elif py_type == "number":
                args.append(f"{prop}=0.0")
            elif py_type == "boolean":
                args.append(f"{prop}=False")
            else:
                args.append(f"{prop}=...")
        else:
            args.append(f"{prop}=None")
    return ", ".join(args)


def merge_params_with_model_fields(
    op: IROperation,
    model_schema: IRSchema,
    context: RenderContext,
) -> list[dict]:
    """
    Merge endpoint parameters with required model fields for function signatures.
    - Ensures all required model fields are present as parameters (without duplication).
    - Endpoint parameters take precedence if names overlap.
    - Returns a list of dicts: {name, type, default, required}.

    Args:
        op: The IROperation (endpoint operation).
        model_schema: The IRSchema for the model (request body or return type).
        context: The RenderContext for imports/type resolution.

    Returns:
        List of parameter dicts suitable for use in endpoint method signatures.
    """
    # Get endpoint parameters (already sanitized)
    endpoint_params = get_params(op, context)
    endpoint_param_names = {p["name"] for p in endpoint_params}
    merged_params = list(endpoint_params)

    # Add required model fields not already present
    if hasattr(model_schema, "properties") and model_schema.properties:
        for prop, pschema in model_schema.properties.items():
            is_required = prop in getattr(model_schema, "required", [])
            if not is_required:
                continue  # Only add required fields
            sanitized_name = NameSanitizer.sanitize_method_name(prop)
            if sanitized_name in endpoint_param_names:
                continue  # Already present as endpoint param
            py_type = get_param_type(
                IRParameter(name=prop, in_="body", required=True, schema=pschema),
                context,
            )
            merged_params.append({
                "name": sanitized_name,
                "type": py_type,
                "default": None,
                "required": True,
            })
    return merged_params
