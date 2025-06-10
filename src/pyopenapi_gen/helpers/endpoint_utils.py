"""
Helpers for endpoint code generation: parameter/type analysis, code writing, etc.
Used by EndpointVisitor and related emitters.
"""

import logging
import re
from typing import Any, Dict, List, Optional

from pyopenapi_gen import IROperation, IRParameter, IRRequestBody, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.http_types import HTTPMethod

from ..core.utils import NameSanitizer
from ..types.services.type_service import UnifiedTypeService

logger = logging.getLogger(__name__)


def get_params(op: IROperation, context: RenderContext, schemas: Dict[str, IRSchema]) -> List[Dict[str, Any]]:
    """
    Returns a list of dicts with name, type, default, and required for template rendering.
    Requires the full schema dictionary for type resolution.
    """
    params = []
    for param in op.parameters:
        py_type = get_param_type(param, context, schemas)
        default = None if param.required else "None"
        params.append(
            {
                "name": NameSanitizer.sanitize_method_name(param.name),
                "type": py_type,
                "default": default,
                "required": param.required,
            }
        )
    return params


def get_param_type(param: IRParameter, context: RenderContext, schemas: Dict[str, IRSchema]) -> str:
    """Returns the Python type hint for a parameter, resolving references using the schemas dict."""
    # Use unified service for type resolution
    type_service = UnifiedTypeService(schemas)
    py_type = type_service.resolve_schema_type(param.schema, context, required=param.required)

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
        # Use unified service for type resolution
        type_service = UnifiedTypeService(schemas)
        py_type = type_service.resolve_schema_type(json_schema, context, required=body.required)
        if py_type.startswith(".") and not py_type.startswith(".."):
            py_type = "models" + py_type

        # If the resolved type is 'Any' for a JSON body, default to Dict[str, Any]
        if py_type == "Any":
            context.add_import("typing", "Dict")
            # context.add_import("typing", "Any") # Already added by the fallback or TypeHelper
            return "Dict[str, Any]"
        return py_type
    # Fallback for other content types (e.g., octet-stream)
    # TODO: Handle other types more specifically if needed
    context.add_import("typing", "Any")
    return "Any"


def get_return_type_unified(
    op: IROperation,
    context: RenderContext,
    schemas: Dict[str, IRSchema],
    responses: Optional[Dict[str, IRResponse]] = None,
) -> str:
    """
    Determines the primary return type hint for an operation using the unified type service.

    Args:
        op: The operation to resolve
        context: Render context for imports
        schemas: Dictionary of all schemas
        responses: Dictionary of all responses (optional)

    Returns:
        Python type string
    """
    type_service = UnifiedTypeService(schemas, responses)
    return type_service.resolve_operation_response_type(op, context)


def get_return_type(
    op: IROperation,
    context: RenderContext,
    schemas: Dict[str, IRSchema],
) -> tuple[str | None, bool]:
    """
    DEPRECATED: Use get_return_type_unified instead.

    Now delegates to the unified service for consistent type resolution.
    Falls back to path-based inference for backward compatibility.

    Returns:
        A tuple: (Python type hint string, boolean indicating if unwrapping occurred).
    """
    # Delegate to the unified service for all type resolution
    type_service = UnifiedTypeService(schemas)
    py_type: str | None = type_service.resolve_operation_response_type(op, context)

    # Backward compatibility: If unified service returns None or "None", try inference
    if py_type is None or py_type == "None":
        if op.method == HTTPMethod.GET:
            # For GET operations, try path-based inference
            inferred_schema = _infer_type_from_path(op.path, schemas)
            if inferred_schema and inferred_schema.name:
                py_type = inferred_schema.name
        elif op.method == HTTPMethod.PUT and op.request_body:
            # For PUT operations, try request body inference
            if op.request_body.content:
                # Get the first content type (usually application/json)
                first_content_type = next(iter(op.request_body.content.keys()))
                request_schema = op.request_body.content[first_content_type]
                if request_schema and request_schema.name:
                    # First try to find corresponding resource schema (e.g., TenantUpdate -> Tenant)
                    resource_schema = _find_resource_schema(request_schema.name, schemas)
                    if resource_schema and resource_schema.name:
                        py_type = resource_schema.name
                    else:
                        # Fall back to request body type
                        py_type = request_schema.name

    # Convert "None" string back to None for backward compatibility only for GET operations
    # For other operations, preserve "None" string as expected by tests
    if py_type == "None" and op.method == HTTPMethod.GET:
        py_type = None

    # For backward compatibility, return a tuple with unwrapping flag set to False
    # The unified service handles unwrapping internally
    return (py_type, False)


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


def _find_resource_schema(update_schema_name: str, schemas: Dict[str, IRSchema]) -> Optional[IRSchema]:
    """
    Given an update schema name (e.g. 'TenantUpdate'), try to find the corresponding
    resource schema (e.g. 'Tenant') in the schemas dictionary.

    Args:
        update_schema_name: Name of the update schema (typically ends with 'Update')
        schemas: Dictionary of all available schemas

    Returns:
        Resource schema if found, None otherwise
    """
    if not update_schema_name or not update_schema_name.endswith("Update"):
        return None

    # Extract base resource name (e.g., "TenantUpdate" -> "Tenant")
    base_name = update_schema_name[:-6]  # Remove "Update" suffix

    # Look for a matching resource schema in the schemas dictionary
    for schema_name, schema in schemas.items():
        if schema_name == base_name or getattr(schema, "name", "") == base_name:
            return schema

    return None


def _infer_type_from_path(path: str, schemas: Dict[str, IRSchema]) -> Optional[IRSchema]:
    """
    Infers a response type from a path. This is used when a response schema is not specified.

    Example:
    - '/tenants/{tenant_id}/feedback' might infer a 'Feedback' or 'FeedbackResponse' type
    - '/users/{user_id}/settings' might infer a 'Settings' or 'SettingsResponse' type

    Args:
        path: The endpoint path
        schemas: Dictionary of all available schemas

    Returns:
        A schema that might be appropriate for the response, or None if no match found
    """
    # Extract resource name from the end of the path
    path_parts = path.rstrip("/").split("/")
    resource_name = path_parts[-1]  # Get the last part of the path

    # Check if the last part is an ID parameter (like {id} or {user_id})
    if resource_name.startswith("{") and resource_name.endswith("}"):
        # If the path ends with an ID, use the second-to-last part
        if len(path_parts) >= 2:
            resource_name = path_parts[-2]

    # Clean up and singularize the resource name
    # Remove any special characters and convert to camel case
    clean_name = "".join(word.title() for word in re.findall(r"[a-zA-Z0-9]+", resource_name))

    # If the resource name is plural (most common API convention), make it singular
    if clean_name.endswith("s") and len(clean_name) > 2:
        singular_name = clean_name[:-1]
    else:
        singular_name = clean_name

    # Common suffix patterns for response types
    candidates = [
        f"{singular_name}",
        f"{singular_name}Response",
        f"{singular_name}ListResponse" if path.endswith("/") or not resource_name.startswith("{") else None,
        f"{singular_name}Item",
        f"{singular_name}Data",
        f"{clean_name}",
        f"{clean_name}Response",
        f"{clean_name}ListResponse" if path.endswith("/") or not resource_name.startswith("{") else None,
        f"{clean_name}Item",
        f"{clean_name}Data",
    ]

    # Filter out None values
    candidates = [c for c in candidates if c]

    # Look for matching schemas
    for candidate in candidates:
        for schema_name, schema in schemas.items():
            if schema_name == candidate or getattr(schema, "name", "") == candidate:
                return schema

    # Try a more generic approach if no specific match found
    for schema_name, schema in schemas.items():
        schema_name_lower = schema_name.lower()
        resource_name_lower = resource_name.lower()

        if resource_name_lower in schema_name_lower and (
            "response" in schema_name_lower or "result" in schema_name_lower or "dto" in schema_name_lower
        ):
            return schema

    # Heuristic: if the path ends with a pluralized version of a known schema, infer list of that schema
    # Example: /users and a User schema -> List[User]
    if singular_name in schemas:
        # Create a temporary array schema for type resolution
        return IRSchema(type="array", items=schemas[singular_name])

    # Heuristic: if the path ends with a singular version of a known schema, infer that schema
    # Example: /user/{id} or /users/{id} and a User schema -> User
    # Covers /resource_name/{param} or /plural_resource_name/{param}
    # More robustly, check if any part of the path matches a schema name (singular or plural)
    # and if it has a path parameter immediately following it.
    path_parts = [part for part in path.split("/") if part]
    for i, part in enumerate(path_parts):
        # potential_schema_name_singular = NameSanitizer.pascal_case(NameSanitizer.singularize(part))
        # HACK: Use a simplified version until NameSanitizer.pascal_case and singularize are available
        # This is a placeholder and might not be correct for all cases.
        potential_schema_name_singular = part.capitalize()  # Simplified placeholder
        if potential_schema_name_singular in schemas and (
            i + 1 < len(path_parts) and path_parts[i + 1].startswith("{")
        ):
            return schemas[potential_schema_name_singular]

    return None


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
    schemas: Dict[str, IRSchema],
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

            # Use the unified service to get the type
            type_service = UnifiedTypeService(schemas)
            py_type = type_service.resolve_schema_type(pschema, context, required=True)
            if py_type.startswith(".") and not py_type.startswith(".."):
                py_type = "models" + py_type

            merged_params.append(
                {
                    "name": sanitized_name,
                    "type": py_type,
                    "default": None,
                    "required": True,
                }
            )
    return merged_params


def get_type_for_specific_response(
    operation_path: str,
    resp_ir: IRResponse,
    all_schemas: dict[str, IRSchema],
    ctx: RenderContext,
    return_unwrap_data_property: bool = False,
) -> str:
    """Get the Python type for a specific response."""
    # If the response content is empty or None, return None
    if not hasattr(resp_ir, "content") or not resp_ir.content:
        return "None"

    # Unwrap data property if needed
    final_py_type = get_python_type_for_response_body(resp_ir, all_schemas, ctx)

    if return_unwrap_data_property:
        wrapper_schema = get_schema_from_response(resp_ir, all_schemas)
        if wrapper_schema and hasattr(wrapper_schema, "properties") and wrapper_schema.properties.get("data"):
            # We have a data property we can unwrap
            data_schema = wrapper_schema.properties["data"]

            wrapper_type_str = final_py_type

            # Handle array unwrapping
            if hasattr(data_schema, "type") and data_schema.type == "array" and hasattr(data_schema, "items"):
                # Need to unwrap array in data property

                # Extract the item type from the array items
                parent_schema_name = (
                    getattr(wrapper_schema, "name", "") + "Data" if hasattr(wrapper_schema, "name") else ""
                )

                # Make sure items is not None before passing to type service
                if data_schema.items:
                    type_service = UnifiedTypeService(all_schemas)
                    item_type = type_service.resolve_schema_type(data_schema.items, ctx, required=True)
                else:
                    ctx.add_import("typing", "Any")
                    item_type = "Any"

                # Handle problematic array item types
                if not item_type or item_type == "Any":
                    # Try to get a better type from the item schema directly
                    parent_schema_name = (
                        getattr(wrapper_schema, "name", "") + "DataItem" if hasattr(wrapper_schema, "name") else ""
                    )

                    # Make sure items is not None before passing to type service
                    if data_schema.items:
                        type_service = UnifiedTypeService(all_schemas)
                        item_type = type_service.resolve_schema_type(data_schema.items, ctx, required=True)
                    else:
                        ctx.add_import("typing", "Any")
                        item_type = "Any"

                # Build the final List type
                ctx.add_import("typing", "List")
                final_type = f"List[{item_type}]"
                return final_type

            else:
                # Unwrap non-array data property
                parent_schema_name = (
                    getattr(wrapper_schema, "name", "") + "Data" if hasattr(wrapper_schema, "name") else ""
                )
                type_service = UnifiedTypeService(all_schemas)
                return type_service.resolve_schema_type(data_schema, ctx, required=True)

    # For AsyncIterator/streaming handlers, add appropriate type annotation
    if getattr(resp_ir, "is_stream", False):
        if _is_binary_stream_content(resp_ir):
            # Binary stream returns bytes chunks
            ctx.add_import("typing", "AsyncIterator")
            return "AsyncIterator[bytes]"

        # If it's not a binary stream, try to determine the item type for the event stream
        item_type_opt = _get_item_type_from_schema(resp_ir, all_schemas, ctx)
        if item_type_opt:
            ctx.add_import("typing", "AsyncIterator")
            return f"AsyncIterator[{item_type_opt}]"

        # Default for unknown event streams
        ctx.add_import("typing", "AsyncIterator")
        ctx.add_import("typing", "Dict")
        ctx.add_import("typing", "Any")
        return "AsyncIterator[Dict[str, Any]]"

    return final_py_type


def _is_binary_stream_content(resp_ir: IRResponse) -> bool:
    """Check if the response is a binary stream based on content type."""
    if not hasattr(resp_ir, "content") or not resp_ir.content:
        return False

    content_types = resp_ir.content.keys()
    return any(
        ct in ("application/octet-stream", "application/pdf", "image/", "audio/", "video/")
        or ct.startswith("image/")
        or ct.startswith("audio/")
        or ct.startswith("video/")
        for ct in content_types
    )


def _get_item_type_from_schema(
    resp_ir: IRResponse, all_schemas: dict[str, IRSchema], ctx: RenderContext
) -> Optional[str]:
    """Extract item type from schema for streaming responses."""
    schema, _ = _get_response_schema_and_content_type(resp_ir)
    if not schema:
        return None

    # For event streams, we want the schema type
    type_service = UnifiedTypeService(all_schemas)
    return type_service.resolve_schema_type(schema, ctx, required=True)


def get_python_type_for_response_body(resp_ir: IRResponse, all_schemas: dict[str, IRSchema], ctx: RenderContext) -> str:
    """Get the Python type for a response body without unwrapping."""
    schema, _ = _get_response_schema_and_content_type(resp_ir)
    if not schema:
        ctx.add_import("typing", "Any")
        return "Any"

    type_service = UnifiedTypeService(all_schemas)
    return type_service.resolve_schema_type(schema, ctx, required=True)


def get_schema_from_response(resp_ir: IRResponse, all_schemas: dict[str, IRSchema]) -> Optional[IRSchema]:
    """Get the schema from a response object."""
    schema, _ = _get_response_schema_and_content_type(resp_ir)
    return schema
