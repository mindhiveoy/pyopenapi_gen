"""Response parsers for OpenAPI IR transformation.

Provides functions to parse and transform OpenAPI responses into IR format.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from pyopenapi_gen import IRResponse, IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema

logger = logging.getLogger(__name__)


def parse_response(
    code: str,
    node: Mapping[str, Any],
    context: ParsingContext,
    operation_id_for_promo: str,
) -> IRResponse:
    """Convert an OpenAPI response node into IRResponse.

    Contracts:
        Preconditions:
            - code is a valid HTTP status code as string
            - node is a valid response node
            - context is properly initialized
            - operation_id_for_promo is provided for naming inline schemas
        Postconditions:
            - Returns a properly populated IRResponse
            - All content media types are properly mapped to schemas
            - Stream flags are correctly set based on media types
    """
    if not isinstance(code, str):
        raise TypeError("code must be a string")
    if not isinstance(node, Mapping):
        raise TypeError("node must be a Mapping")
    if not isinstance(context, ParsingContext):
        raise TypeError("context must be a ParsingContext")
    if not operation_id_for_promo:
        raise ValueError("operation_id_for_promo must be provided")

    content: dict[str, IRSchema] = {}
    STREAM_FORMATS = {
        "application/octet-stream": "octet-stream",
        "text/event-stream": "event-stream",
        "application/x-ndjson": "ndjson",
        "application/json-seq": "json-seq",
        "multipart/mixed": "multipart-mixed",
    }
    stream_flag = False
    stream_format = None

    # Construct a base name for promoting inline schemas within this response
    parent_promo_name_for_resp_body = f"{operation_id_for_promo}{code}Response"

    for mt, mn in node.get("content", {}).items():
        if isinstance(mn, Mapping) and "$ref" in mn and mn["$ref"].startswith("#/components/schemas/"):
            content[mt] = _parse_schema(None, mn, context, allow_self_reference=False)
        elif isinstance(mn, Mapping) and "schema" in mn:
            media_schema_node = mn["schema"]
            if (
                isinstance(media_schema_node, Mapping)
                and "$ref" not in media_schema_node
                and (
                    media_schema_node.get("type") == "object"
                    or "properties" in media_schema_node
                    or "allOf" in media_schema_node
                    or "anyOf" in media_schema_node
                    or "oneOf" in media_schema_node
                )
            ):
                content[mt] = _parse_schema(
                    parent_promo_name_for_resp_body, media_schema_node, context, allow_self_reference=False
                )
            else:
                content[mt] = _parse_schema(None, media_schema_node, context, allow_self_reference=False)
        else:
            content[mt] = IRSchema(name=None, _from_unresolved_ref=True)

        fmt = STREAM_FORMATS.get(mt.lower())
        if fmt:
            stream_flag = True
            stream_format = fmt

    if not stream_flag:
        for mt_val, schema_val in content.items():
            if getattr(schema_val, "format", None) == "binary":
                stream_flag = True
                stream_format = "octet-stream"

    response = IRResponse(
        status_code=code,
        description=node.get("description"),
        content=content,
        stream=stream_flag,
        stream_format=stream_format,
    )

    # Post-condition checks
    if response.status_code != code:
        raise RuntimeError("Response status code mismatch")
    if response.content != content:
        raise RuntimeError("Response content mismatch")
    if response.stream != stream_flag:
        raise RuntimeError("Response stream flag mismatch")

    return response
