"""
Helpers for endpoint code generation: parameter/type analysis, code writing, etc.
Used by EndpointVisitor and related emitters.
"""

from typing import Any, Dict, List, Optional

from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext

from ..core.utils import NameSanitizer
from .type_helper import get_python_type_for_schema


def get_params(op: IROperation, context: RenderContext, schemas: Dict[str, IRSchema]) -> List[Dict[str, Any]]:
    """
    Returns a list of dicts with name, type, default, and required for template rendering.
    Requires the full schema dictionary for type resolution.
    """
    params = []
    for param in op.parameters:
        py_type = get_param_type(param, context, schemas)
        default = None if param.required else "None"
        params.append({
            "name": NameSanitizer.sanitize_method_name(param.name),
            "type": py_type,
            "default": default,
            "required": param.required,
        })
    return params


def get_param_type(param: IRParameter, context: RenderContext, schemas: Dict[str, IRSchema]) -> str:
    """Returns the Python type hint for a parameter, resolving references using the schemas dict."""
    py_type = get_python_type_for_schema(param.schema, schemas, context, required=param.required)

    # Adjust model import path for endpoints (expecting models.<module>)
    if py_type.startswith(".") and not py_type.startswith(".."):  # Simple relative import
        py_type = "models" + py_type

    # Special handling for file uploads in multipart/form-data
    if (
        getattr(param, "in_", None) == "formData"
        and getattr(param.schema, "type", None) == "string"
        and getattr(param.schema, "format", None) == "binary"
    ):
        context.add_import("typing", "IO")
        context.add_import("typing", "Any")
        return "IO[Any]"
    return py_type


def get_request_body_type(body: IRRequestBody, context: RenderContext, schemas: Dict[str, IRSchema]) -> str:
    """Returns the Python type hint for a request body, resolving references using the schemas dict."""
    # Prefer application/json schema if available
    json_schema = body.content.get("application/json")
    if json_schema:
        py_type = get_python_type_for_schema(json_schema, schemas, context, required=body.required)
        if py_type.startswith(".") and not py_type.startswith(".."):
            py_type = "models" + py_type
        return py_type
    # Fallback for other content types (e.g., octet-stream)
    # TODO: Handle other types more specifically if needed
    context.add_import("typing", "Any")
    return "Any"


def get_return_type(
    op: IROperation,
    context: RenderContext,
    schemas: Dict[str, IRSchema],  # Pass schemas dict
) -> str:
    """
    Determines the primary return type hint for an operation.
    Detects and handles response unwrapping if the success schema is an object
    with a single 'data' property.
    """
    # Find the best success response (200, 201, etc.)
    resp = _get_primary_response(op)

    if not resp or not resp.content or resp.status_code == "204":
        return "None"

    schema, mt = _get_response_schema_and_content_type(resp)

    if not schema:
        return "Any"  # Fallback if no schema found for content type

    # --- Unwrapping Logic ---
    should_unwrap = False
    data_schema: Optional[IRSchema] = None
    wrapper_type_str: Optional[str] = None

    if isinstance(schema, IRSchema) and getattr(schema, "type", None) == "object" and hasattr(schema, "properties"):
        properties = schema.properties
        if len(properties) == 1 and "data" in properties:
            should_unwrap = True
            data_schema = properties["data"]
            # Get the original wrapper type string BEFORE potentially unwrapping
            # This ensures the wrapper model (e.g., TenantResponse) is imported if needed for deserialization
            wrapper_type_str = get_python_type_for_schema(schema, schemas, context, required=True)
            if wrapper_type_str and wrapper_type_str != "Any" and "." in wrapper_type_str:
                # Ensure the wrapper type is imported even if we return the inner type
                # We might need it temporarily during parsing before accessing .data
                # Check if it's likely a model import (contains '.')
                if wrapper_type_str.startswith("models."):  # Already adjusted
                    context.add_import(wrapper_type_str.split(".")[0], wrapper_type_str.split(".")[1])
                elif wrapper_type_str.startswith("."):  # Needs adjustment
                    adjusted_wrapper_type = "models" + wrapper_type_str
                    context.add_import(adjusted_wrapper_type.split(".")[0], adjusted_wrapper_type.split(".")[1])
                else:  # Assume it's a model name directly
                    # This assumes ModelVisitor places models in <package_root>/models/<model_name>.py
                    model_module = f"models.{NameSanitizer.sanitize_module_name(wrapper_type_str)}"
                    context.add_import(model_module, wrapper_type_str)

    # Determine the final schema to use for type generation
    final_schema = data_schema if should_unwrap and data_schema else schema
    is_streaming = resp.stream and not should_unwrap  # Don't unwrap streams for now

    # Handle streaming response (if not unwrapped)
    if is_streaming:
        item_type = get_python_type_for_schema(final_schema, schemas, context, required=True)
        # Adjust import path if needed (relative model -> models.<module>)
        if item_type.startswith(".") and not item_type.startswith(".."):
            item_type = "models" + item_type
        context.add_import("typing", "AsyncIterator")
        context.add_plain_import("collections.abc")
        return f"AsyncIterator[{item_type}]"

    # Handle regular response schema (or unwrapped schema)
    py_type = get_python_type_for_schema(
        final_schema, schemas, context, required=True
    )  # Response implies required content

    # Adjust model import path for endpoints (expecting models.<module>)
    # This adjustment might be redundant if get_python_type_for_schema handles context correctly,
    # but kept for safety.
    if py_type.startswith(".") and not py_type.startswith(".."):
        py_type = "models" + py_type

    return py_type


def _get_primary_response(op: IROperation) -> Optional[IRResponse]:
    """Helper to find the best primary success response."""
    resp = None
    # Prioritize 200, 201, 202, 204
    for code in ["200", "201", "202", "204"]:
        resp = next((r for r in op.responses if r.status_code == code), None)
        if resp:
            return resp
    # Then other 2xx
    for r in op.responses:
        if r.status_code.startswith("2"):
            return r
    # Then default
    resp = next((r for r in op.responses if r.status_code == "default"), None)
    if resp:
        return resp
    # Finally, the first listed response if any
    if op.responses:
        return op.responses[0]
    return None


def _get_response_schema_and_content_type(resp: IRResponse) -> tuple[Optional[IRSchema], Optional[str]]:
    """Helper to get the schema and content type from a response."""
    if not resp.content:
        return None, None

    content_types = list(resp.content.keys())
    # Prefer application/json, then event-stream, then any other json, then first
    mt = next((ct for ct in content_types if ct == "application/json"), None)
    if not mt:
        mt = next((ct for ct in content_types if "event-stream" in ct), None)
    if not mt:
        mt = next((ct for ct in content_types if "json" in ct), None)  # Catch application/vnd.api+json etc.
    if not mt and content_types:
        mt = content_types[0]

    if not mt:
        return None, None

    return resp.content.get(mt), mt


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
    schemas: Dict[str, IRSchema],  # Pass schemas dict
) -> List[Dict[str, Any]]:
    """
    Merge endpoint parameters with required model fields for function signatures.
    - Ensures all required model fields are present as parameters (without duplication).
    - Endpoint parameters take precedence if names overlap.
    - Returns a list of dicts: {name, type, default, required}.

    Args:
        op: The IROperation (endpoint operation).
        model_schema: The IRSchema for the model (request body or return type).
        context: The RenderContext for imports/type resolution.
        schemas: Dictionary of all named schemas.

    Returns:
        List of parameter dicts suitable for use in endpoint method signatures.
    """
    # Get endpoint parameters (already sanitized)
    endpoint_params = get_params(op, context, schemas)
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

            # Use the helper function to get the type
            py_type = get_python_type_for_schema(pschema, schemas, context, required=True)
            if py_type.startswith(".") and not py_type.startswith(".."):
                py_type = "models" + py_type

            merged_params.append({
                "name": sanitized_name,
                "type": py_type,
                "default": None,
                "required": True,
            })
    return merged_params
