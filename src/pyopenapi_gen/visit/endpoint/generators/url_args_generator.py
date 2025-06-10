"""
Helper class for generating URL, query parameters, and header parameters for an endpoint method.
"""

from __future__ import annotations

import logging
import re  # For _build_url_with_path_vars
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.core.writers.code_writer import CodeWriter

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation  # IRParameter might be needed for op.parameters access
    from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)


class EndpointUrlArgsGenerator:
    """Generates URL, query, and header parameters for an endpoint method."""

    def __init__(self, schemas: Optional[Dict[str, Any]] = None) -> None:
        self.schemas: Dict[str, Any] = schemas or {}

    def _build_url_with_path_vars(self, path: str) -> str:
        """Builds the f-string for URL construction, substituting path variables."""
        # Ensure m.group(1) is treated as a string for NameSanitizer
        # Build the URL f-string by substituting path variables
        formatted_path = re.sub(
            r"{([^}]+)}", lambda m: f"{{{NameSanitizer.sanitize_method_name(str(m.group(1)))}}}", path
        )
        return f'f"{{self.base_url}}{formatted_path}"'

    def _write_query_params(
        self, writer: CodeWriter, op: IROperation, ordered_params: List[Dict[str, Any]], context: RenderContext
    ) -> None:
        """Writes query parameter dictionary construction."""
        # Logic from EndpointMethodGenerator._write_query_params
        query_params_to_write = [p for p in ordered_params if p.get("param_in") == "query"]
        if not query_params_to_write:
            # writer.write_line("# No query parameters to write") # Optional: for clarity during debugging
            return

        for i, p in enumerate(query_params_to_write):
            param_var_name = NameSanitizer.sanitize_method_name(p["name"])  # Ensure name is sanitized
            original_param_name = p["original_name"]
            line_end = ","  # Always add comma, let formatter handle final one if needed

            if p.get("required", False):
                writer.write_line(f'    "{original_param_name}": {param_var_name}{line_end}')
            else:
                # Using dict unpacking for conditional parameters
                writer.write_line(
                    f'    **({{"{original_param_name}": {param_var_name}}} '
                    f"if {param_var_name} is not None else {{}}){line_end}"
                )

    def _write_header_params(
        self, writer: CodeWriter, op: IROperation, ordered_params: List[Dict[str, Any]], context: RenderContext
    ) -> None:
        """Writes header parameter dictionary construction."""
        # Logic from EndpointMethodGenerator._write_header_params
        # Iterate through ordered_params to find header params, op.parameters may not be directly useful here
        # if ordered_params is the sole source of truth for method params.
        header_params_to_write = [p for p in ordered_params if p.get("param_in") == "header"]

        for p_info in header_params_to_write:
            param_var_name = NameSanitizer.sanitize_method_name(
                p_info["name"]
            )  # Sanitized name used in method signature
            original_header_name = p_info["original_name"]  # Actual header name for the request
            line_end = ","

            if p_info.get("required", False):
                writer.write_line(f'    "{original_header_name}": {param_var_name}{line_end}')
            else:
                # Conditional inclusion for optional headers
                # This assumes that if an optional header parameter is None, it should not be sent.
                # If specific behavior (e.g. empty string) is needed for None, logic would adjust.
                writer.write_line(
                    f'    **({{"{original_header_name}": {param_var_name}}} '
                    f"if {param_var_name} is not None else {{}}){line_end}"
                )

    def generate_url_and_args(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
        ordered_params: List[Dict[str, Any]],
        primary_content_type: Optional[str],
        resolved_body_type: Optional[str],
    ) -> bool:
        """Writes URL, query, and header parameters. Returns True if header params were written."""
        # Main logic from EndpointMethodGenerator._write_url_and_args
        url_expr = self._build_url_with_path_vars(op.path)
        writer.write_line(f"url = {url_expr}")
        writer.write_line("")  # Add a blank line for readability

        # Query Parameters
        # Check if any parameter in ordered_params is a query param, not just op.parameters
        has_spec_query_params = any(p.get("param_in") == "query" for p in ordered_params)
        if has_spec_query_params:
            context.add_import("typing", "Any")  # For Dict[str, Any]
            context.add_import("typing", "Dict")  # For Dict[str, Any]
            writer.write_line("params: Dict[str, Any] = {")
            # writer.indent() # Indentation should be handled by CodeWriter when writing lines
            self._write_query_params(writer, op, ordered_params, context)
            # writer.dedent()
            writer.write_line("}")
            writer.write_line("")  # Add a blank line

        # Header Parameters
        has_header_params = any(p.get("param_in") == "header" for p in ordered_params)
        if has_header_params:
            context.add_import("typing", "Any")  # For Dict[str, Any]
            context.add_import("typing", "Dict")  # For Dict[str, Any]
            writer.write_line("headers: Dict[str, Any] = {")
            # writer.indent()
            self._write_header_params(writer, op, ordered_params, context)
            # writer.dedent()
            writer.write_line("}")
            writer.write_line("")  # Add a blank line

        # Request Body related local variables (json_body, files_data, etc.)
        # This part was in _write_url_and_args in the original, it sets up variables used by _write_request
        if op.request_body:
            # Import DataclassSerializer for automatic conversion
            context.add_import(f"{context.core_package_name}.utils", "DataclassSerializer")

            if primary_content_type == "application/json":
                body_param_detail = next((p for p in ordered_params if p["name"] == "body"), None)
                if body_param_detail:
                    actual_body_type_from_signature = body_param_detail["type"]
                    context.add_typing_imports_for_type(actual_body_type_from_signature)
                    writer.write_line(
                        f"json_body: {actual_body_type_from_signature} = DataclassSerializer.serialize(body)"
                    )
                else:
                    logger.warning(
                        f"Operation {op.operation_id}: 'body' parameter not found in "
                        f"ordered_params for JSON. Defaulting to Any."
                    )
                    context.add_import("typing", "Any")
                    writer.write_line("json_body: Any = DataclassSerializer.serialize(body)  # param not found")
            elif primary_content_type == "multipart/form-data":
                files_param_details = next((p for p in ordered_params if p["name"] == "files"), None)
                if files_param_details:
                    actual_files_param_type = files_param_details["type"]
                    context.add_typing_imports_for_type(actual_files_param_type)
                    writer.write_line(f"files_data: {actual_files_param_type} = DataclassSerializer.serialize(files)")
                else:
                    logger.warning(
                        f"Operation {op.operation_id}: Could not find 'files' parameter details "
                        f"for multipart/form-data. Defaulting type."
                    )
                    context.add_import("typing", "Dict")
                    context.add_import("typing", "IO")  # For IO[Any]
                    context.add_import("typing", "Any")
                    writer.write_line(
                        "files_data: Dict[str, IO[Any]] = DataclassSerializer.serialize(files)  # type failed"
                    )
            elif primary_content_type == "application/x-www-form-urlencoded":
                # form_data is the expected parameter name from EndpointParameterProcessor
                # resolved_body_type should be Dict[str, Any]
                if resolved_body_type:
                    writer.write_line(
                        f"form_data_body: {resolved_body_type} = DataclassSerializer.serialize(form_data)"
                    )
                else:  # Should not happen if EndpointParameterProcessor sets it
                    context.add_import("typing", "Dict")
                    context.add_import("typing", "Any")
                    writer.write_line(
                        "form_data_body: Dict[str, Any] = DataclassSerializer.serialize(form_data)  # Fallback type"
                    )
            elif resolved_body_type == "bytes":  # e.g. application/octet-stream
                # bytes_content is the expected parameter name from EndpointParameterProcessor
                writer.write_line(f"bytes_body: bytes = bytes_content")
            writer.write_line("")  # Add a blank line after body var setup

        return has_header_params
