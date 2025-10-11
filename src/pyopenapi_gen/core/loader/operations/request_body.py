"""Request body parsers for OpenAPI IR transformation.

Provides functions to parse and transform OpenAPI request bodies into IR format.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from pyopenapi_gen import IRRequestBody, IRSchema
from pyopenapi_gen.core.parsing.context import ParsingContext
from pyopenapi_gen.core.parsing.schema_parser import _parse_schema

logger = logging.getLogger(__name__)


def parse_request_body(
    rb_node: Mapping[str, Any],
    raw_request_bodies: Mapping[str, Any],
    context: ParsingContext,
    operation_id: str,
) -> IRRequestBody | None:
    """Parse a request body node into an IRRequestBody.

    Contracts:
        Preconditions:
            - rb_node is a valid request body node
            - raw_request_bodies contains component request bodies
            - context is properly initialized
            - operation_id is provided for naming
        Postconditions:
            - Returns a properly populated IRRequestBody or None if invalid
            - All content media types are properly mapped to schemas
    """
    if not isinstance(rb_node, Mapping):
        raise TypeError("rb_node must be a Mapping")
    if not isinstance(raw_request_bodies, Mapping):
        raise TypeError("raw_request_bodies must be a Mapping")
    if not isinstance(context, ParsingContext):
        raise TypeError("context must be a ParsingContext")
    if not operation_id:
        raise ValueError("operation_id must be provided")

    # Handle $ref in request body
    if (
        "$ref" in rb_node
        and isinstance(rb_node.get("$ref"), str)
        and rb_node["$ref"].startswith("#/components/requestBodies/")
    ):
        ref_name = rb_node["$ref"].split("/")[-1]
        resolved_rb_node = raw_request_bodies.get(ref_name, {}) or rb_node
    else:
        resolved_rb_node = rb_node

    required_flag = bool(resolved_rb_node.get("required", False))
    desc = resolved_rb_node.get("description")
    content_map: dict[str, IRSchema] = {}

    parent_promo_name_for_req_body = f"{operation_id}RequestBody"

    for mt, media in resolved_rb_node.get("content", {}).items():
        media_schema_node = media.get("schema")
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
            content_map[mt] = _parse_schema(
                parent_promo_name_for_req_body, media_schema_node, context, allow_self_reference=False
            )
        else:
            content_map[mt] = _parse_schema(None, media_schema_node, context, allow_self_reference=False)

    if not content_map:
        return None

    request_body = IRRequestBody(required=required_flag, content=content_map, description=desc)

    # Post-condition check
    if request_body.content != content_map:
        raise RuntimeError("Request body content mismatch")

    return request_body
