"""
Helper class for generating the HTTP request call for an endpoint method.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pyopenapi_gen.core.writers.code_writer import CodeWriter

# No specific utils needed yet, but NameSanitizer might be if param names are manipulated here

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation
    from pyopenapi_gen.context.render_context import RenderContext  # For context.add_import if needed

logger = logging.getLogger(__name__)


class EndpointRequestGenerator:
    """Generates the self._transport.request(...) call for an endpoint method."""

    def __init__(self, schemas: Optional[Dict[str, Any]] = None) -> None:
        self.schemas: Dict[str, Any] = schemas or {}

    def generate_request_call(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,  # Pass context for potential import needs
        has_header_params: bool,
        primary_content_type: Optional[str],
        # resolved_body_type: Optional[str], # May not be directly needed here if logic relies on var names
    ) -> None:
        """Writes the self._transport.request call to the CodeWriter."""
        # Logic from EndpointMethodGenerator._write_request
        args_list = []

        # Determine if 'params' argument is needed for query parameters
        # This relies on UrlArgsGenerator having created a 'params' dict if query params exist.
        # A more robust way could be to check op.parameters directly, but this keeps coupling loose.
        if any(p.param_in == "query" for p in op.parameters):  # Check IROperation directly for query params
            args_list.append("params=params")
        else:
            args_list.append("params=None")

        # Determine 'json' and 'data' arguments based on request body
        if op.request_body:
            if primary_content_type == "application/json":
                args_list.append("json=json_body")  # Assumes json_body is defined
                # args_list.append("data=None") # Not strictly needed if json is present, httpx handles it
            elif primary_content_type and "multipart/form-data" in primary_content_type:
                # For multipart, httpx uses 'files' or 'data' depending on content.
                # UrlArgsGenerator created 'files_data'. Httpx typically uses 'files=' for file uploads.
                # Let's assume 'files_data' is a dict suitable for 'files=' or 'data='
                # If 'files_data' is specifically for file-like objects, 'files=files_data' is better.
                # If it can also contain plain data, 'data=files_data' might be used by httpx.
                # For simplicity and common use with files:
                args_list.append("files=files_data")  # Assumes files_data is defined
            elif primary_content_type == "application/x-www-form-urlencoded":
                args_list.append("data=form_data_body")  # Assumes form_data_body is defined
            elif primary_content_type:  # Other types, like application/octet-stream
                args_list.append("data=bytes_body")  # Assumes bytes_body is defined
            # else: # No specific content type handled, might mean no body or unhandled type
            #     args_list.append("json=None")
            #     args_list.append("data=None")
        else:  # No request body
            args_list.append("json=None")
            args_list.append("data=None")

        # Determine 'headers' argument
        if has_header_params:  # This flag comes from UrlArgsGenerator
            args_list.append("headers=headers")  # Assumes headers dict is defined
        else:
            args_list.append("headers=None")

        positional_args_str = f'"{op.method.upper()}", url'  # url variable is assumed to be defined
        keyword_args_str = ", ".join(args_list)

        # Check length for formatting (120 is a common line length limit)
        # Account for "response = await self._transport.request(" and ")" and surrounding spaces/indentation
        # A rough estimate, effective line length for arguments should be less than ~120 - ~40 = 80
        effective_args_len = len(positional_args_str) + len(", ") + len(keyword_args_str)

        base_call_len = len("response = await self._transport.request()") + 2  # +2 for (,)

        if base_call_len + effective_args_len <= 100:  # Adjusted for typical black formatting preference
            writer.write_line(f"response = await self._transport.request({positional_args_str}, {keyword_args_str})")
        else:
            writer.write_line(f"response = await self._transport.request(")
            writer.indent()
            writer.write_line(f"{positional_args_str},")
            # Filter out "*=None" for cleaner multi-line calls if they are truly None and not just assigned None
            # This might be overly complex here; httpx handles None correctly.
            # Sticking to original logic for now.
            num_args = len(args_list)
            for i, arg in enumerate(args_list):
                line_end = "," if i < num_args - 1 else ""
                writer.write_line(f"{arg}{line_end}")
            writer.dedent()
            writer.write_line(")")
        writer.write_line("")  # Add a blank line for readability after the request call
