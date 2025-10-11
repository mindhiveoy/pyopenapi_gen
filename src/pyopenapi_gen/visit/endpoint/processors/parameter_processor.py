"""
Helper class for processing parameters for an endpoint method.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, Tuple

from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.helpers.endpoint_utils import get_param_type, get_request_body_type
from pyopenapi_gen.helpers.url_utils import extract_url_variables

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation
    from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)


class EndpointParameterProcessor:
    """
    Processes IROperation parameters and request body to prepare a list of
    method parameters for the endpoint signature and further processing.
    """

    def __init__(self, schemas: dict[str, Any] | None = None) -> None:
        self.schemas: dict[str, Any] = schemas or {}

    def process_parameters(
        self, op: IROperation, context: RenderContext
    ) -> Tuple[List[dict[str, Any]], str | None, str | None]:
        """
        Prepares and orders parameters for an endpoint method, including path,
        query, header, and request body parameters.

        Returns:
            A tuple containing:
            - ordered_params: List of parameter dictionaries for method signature.
            - primary_content_type: The dominant content type for the request body.
            - resolved_body_type: The Python type hint for the request body.
        """
        ordered_params: List[dict[str, Any]] = []
        param_details_map: dict[str, dict[str, Any]] = {}

        for param in op.parameters:
            param_name_sanitized = NameSanitizer.sanitize_method_name(param.name)
            param_info = {
                "name": param_name_sanitized,
                "type": get_param_type(param, context, self.schemas),
                "required": param.required,
                "default": param.schema.default if param.schema else None,
                "param_in": param.param_in,
                "original_name": param.name,
            }
            ordered_params.append(param_info)
            param_details_map[param_name_sanitized] = param_info

        primary_content_type: str | None = None
        resolved_body_type: str | None = None

        if op.request_body:
            content_types = op.request_body.content.keys()
            body_param_name = "body"  # Default name
            context.add_import("typing", "Any")  # General fallback
            body_specific_param_info: dict[str, Any] | None = None

            if "multipart/form-data" in content_types:
                primary_content_type = "multipart/form-data"
                body_param_name = "files"
                context.add_import("typing", "Dict")
                context.add_import("typing", "IO")
                resolved_body_type = "dict[str, IO[Any]]"
                body_specific_param_info = {
                    "name": body_param_name,
                    "type": resolved_body_type,
                    "required": op.request_body.required,
                    "default": None,
                    "param_in": "body",
                    "original_name": body_param_name,
                }
            elif "application/json" in content_types:
                primary_content_type = "application/json"
                body_param_name = "body"
                resolved_body_type = get_request_body_type(op.request_body, context, self.schemas)
                body_specific_param_info = {
                    "name": body_param_name,
                    "type": resolved_body_type,
                    "required": op.request_body.required,
                    "default": None,
                    "param_in": "body",
                    "original_name": body_param_name,
                }
            elif "application/x-www-form-urlencoded" in content_types:
                primary_content_type = "application/x-www-form-urlencoded"
                body_param_name = "form_data"
                context.add_import("typing", "Dict")
                resolved_body_type = "dict[str, Any]"
                body_specific_param_info = {
                    "name": body_param_name,
                    "type": resolved_body_type,
                    "required": op.request_body.required,
                    "default": None,
                    "param_in": "body",
                    "original_name": body_param_name,
                }
            elif content_types:  # Fallback for other content types
                primary_content_type = list(content_types)[0]
                body_param_name = "bytes_content"  # e.g. for application/octet-stream
                resolved_body_type = "bytes"
                body_specific_param_info = {
                    "name": body_param_name,
                    "type": resolved_body_type,
                    "required": op.request_body.required,
                    "default": None,
                    "param_in": "body",
                    "original_name": body_param_name,
                }

            if body_specific_param_info:
                if body_specific_param_info["name"] not in param_details_map:
                    ordered_params.append(body_specific_param_info)
                    param_details_map[body_specific_param_info["name"]] = body_specific_param_info
                else:
                    logger.warning(
                        f"Request body parameter name '{body_specific_param_info['name']}' "
                        f"for operation '{op.operation_id}'"
                        f"collides with an existing path/query/header parameter. Check OpenAPI spec."
                    )

        final_ordered_params = self._ensure_path_variables_as_params(op, ordered_params, param_details_map)

        # Sort parameters: required first, then optional.
        # We use a stable sort by negating 'required' (True becomes -1, False becomes 0).
        # Parameters with the same required status maintain their relative order.
        final_ordered_params.sort(key=lambda p: not p["required"])

        return final_ordered_params, primary_content_type, resolved_body_type

    def _ensure_path_variables_as_params(
        self, op: IROperation, current_params: List[dict[str, Any]], param_details_map: dict[str, dict[str, Any]]
    ) -> List[dict[str, Any]]:
        """
        Ensures that all variables in the URL path are present in the list of parameters.
        If a path variable is not already defined as a parameter, it's added as a required string type.
        This also updates the param_details_map.
        """
        url_vars = extract_url_variables(op.path)

        # Make a copy to modify if necessary
        updated_params = list(current_params)

        for var in url_vars:
            sanitized_var_name = NameSanitizer.sanitize_method_name(var)
            if sanitized_var_name not in param_details_map:
                path_var_param_info = {
                    "name": sanitized_var_name,
                    "type": "str",  # Path variables are typically strings
                    "required": True,  # Path variables are always required
                    "default": None,
                    "param_in": "path",
                    "original_name": var,
                }
                updated_params.append(path_var_param_info)
                param_details_map[sanitized_var_name] = path_var_param_info
                # logger.debug(
                #     f"Added missing path variable '{sanitized_var_name}' "
                #     f"to parameters for operation '{op.operation_id}'."
                # )

        return updated_params
