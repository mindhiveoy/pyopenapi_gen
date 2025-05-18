"""Response parsers for OpenAPI IR transformation.

Provides functions to parse and transform OpenAPI responses into IR format.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping

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
    assert isinstance(code, str), "code must be a string"
    assert isinstance(node, Mapping), "node must be a Mapping"
    assert isinstance(context, ParsingContext), "context must be a ParsingContext"
    assert operation_id_for_promo, "operation_id_for_promo must be provided"

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

    # Construct a base name for promoting inline schemas within this response
    parent_promo_name_for_resp_body = f"{operation_id_for_promo}{code}Response"

    for mt, mn in node.get("content", {}).items():
        if isinstance(mn, Mapping) and "$ref" in mn and mn["$ref"].startswith("#/components/schemas/"):
            content[mt] = _parse_schema(None, mn, context)
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
                content[mt] = _parse_schema(parent_promo_name_for_resp_body, media_schema_node, context)
            else:
                content[mt] = _parse_schema(None, media_schema_node, context)
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
    assert response.status_code == code, "Response status code mismatch"
    assert response.content == content, "Response content mismatch"
    assert response.stream == stream_flag, "Response stream flag mismatch"

    return response
