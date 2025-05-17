"""
Helper class for generating the docstring for an endpoint method.
"""

from __future__ import annotations

import logging
import textwrap  # For _wrap_docstring logic
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from pyopenapi_gen.core.writers.code_writer import CodeWriter
from pyopenapi_gen.core.writers.documentation_writer import DocumentationBlock, DocumentationWriter
from pyopenapi_gen.helpers.endpoint_utils import get_param_type, get_request_body_type, get_return_type

if TYPE_CHECKING:
    from pyopenapi_gen import IROperation, IRParameter, IRRequestBody
    from pyopenapi_gen.context.render_context import RenderContext

logger = logging.getLogger(__name__)


class EndpointDocstringGenerator:
    """Generates the Python docstring for an endpoint operation."""

    def __init__(self, schemas: Optional[Dict[str, Any]] = None) -> None:
        self.schemas: Dict[str, Any] = schemas or {}
        self.doc_writer = DocumentationWriter(width=88)

    def _wrap_docstring(self, prefix: str, text: str, width: int = 88) -> str:
        """Internal helper to wrap text for docstrings."""
        # This was a staticmethod in EndpointMethodGenerator, can be a helper here.
        if not text:
            return prefix.rstrip()
        initial_indent = prefix
        subsequent_indent = " " * len(prefix)
        wrapped = textwrap.wrap(text, width=width, initial_indent=initial_indent, subsequent_indent=subsequent_indent)
        # The original had "\n    ".join(wrapped), which might be too specific if prefix changes.
        # Let's ensure it joins with newline and respects the subsequent_indent for multi-lines.
        if not wrapped:
            return prefix.rstrip()
        # For single line, no complex join needed, just the wrapped line.
        if len(wrapped) == 1:
            return wrapped[0]
        # For multi-line, ensure proper joining. textwrap handles indent per line.
        return "\n".join(wrapped)

    def generate_docstring(
        self,
        writer: CodeWriter,
        op: IROperation,
        context: RenderContext,
        primary_content_type: Optional[str],
    ) -> None:
        """Writes the method docstring to the provided CodeWriter."""
        summary = op.summary or None
        description = op.description or None
        args: list[tuple[str, str, str] | tuple[str, str]] = []

        for param in op.parameters:
            param_type = get_param_type(param, context, self.schemas)
            desc = param.description or ""
            args.append((param.name, param_type, desc))

        if op.request_body and primary_content_type:
            body_desc = op.request_body.description or "Request body."
            # Standardized body parameter names based on content type
            if primary_content_type == "multipart/form-data":
                args.append(("files", "Dict[str, IO[Any]]", body_desc + " (multipart/form-data)"))
            elif primary_content_type == "application/x-www-form-urlencoded":
                # The type here could be more specific if schema is available, but Dict[str, Any] is a safe default.
                args.append(("form_data", "Dict[str, Any]", body_desc + " (x-www-form-urlencoded)"))
            elif primary_content_type == "application/json":
                body_type = get_request_body_type(op.request_body, context, self.schemas)
                args.append(("body", body_type, body_desc + " (json)"))
            else:  # Fallback for other types like application/octet-stream
                args.append(("bytes_content", "bytes", body_desc + f" ({primary_content_type})"))

        return_type, _ = get_return_type(op, context, self.schemas)
        response_desc = None
        # Prioritize 2xx success codes for the main response description
        for code in ("200", "201", "202", "default"):  # Include default as it might be the success response
            resp = next((r for r in op.responses if r.status_code == code), None)
            if resp and resp.description:
                response_desc = resp.description.strip()
                break
        if not response_desc:  # Fallback to any response description if no 2xx/default found
            for resp in op.responses:
                if resp.description:
                    response_desc = resp.description.strip()
                    break

        returns = (return_type, response_desc or "Response object.") if return_type and return_type != "None" else None

        error_codes = [r for r in op.responses if r.status_code.isdigit() and int(r.status_code) >= 400]
        raises = []
        if error_codes:
            for resp in error_codes:
                # Using a generic HTTPError, specific error classes could be mapped later
                code_to_raise = "HTTPError"
                desc = f"{resp.status_code}: {resp.description.strip() if resp.description else 'HTTP error.'}"
                raises.append((code_to_raise, desc))
        else:
            raises.append(("HTTPError", "If the server returns a non-2xx HTTP response."))

        doc_block = DocumentationBlock(
            summary=summary,
            description=description,
            args=args,
            returns=returns,
            raises=raises,
        )

        # The DocumentationWriter handles the actual formatting and wrapping.
        # The _wrap_docstring helper is not directly used here if DocumentationWriter handles it all.
        # However, DocumentationWriter.render_docstring itself might need indentation control.
        # Original called writer.write_line(line) for each line of docstring.
        docstring_str = self.doc_writer.render_docstring(
            doc_block, indent=0
        )  # indent=0 as CodeWriter handles method indent
        for line in docstring_str.splitlines():
            writer.write_line(line)
