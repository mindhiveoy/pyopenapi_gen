"""Unified response handling strategy.

This module provides a single source of truth for how operation responses should be handled,
eliminating the scattered responsibility that was causing Data_ vs proper schema name issues.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.types.services.type_service import UnifiedTypeService

logger = logging.getLogger(__name__)


@dataclass
class ResponseStrategy:
    """Unified strategy for handling a specific operation's response.

    This class encapsulates all decisions about how to handle a response:
    - What type to use in method signatures (matches OpenAPI schema exactly)
    - Which schema to use for deserialization
    - How to generate the response handling code
    """

    return_type: str  # The Python type for method signature
    response_schema: IRSchema | None  # The response schema as defined in OpenAPI spec
    is_streaming: bool  # Whether this is a streaming response

    # Additional context for code generation
    response_ir: IRResponse | None  # The original response IR

    # Multi-content-type support
    content_type_mapping: dict[str, str] | None = None  # Maps content-type to Python type for Union responses


class ResponseStrategyResolver:
    """Single source of truth for response handling decisions.

    This resolver examines an operation and its responses to determine the optimal
    strategy for handling the response. It replaces the scattered logic that was
    previously spread across multiple components.
    """

    def __init__(self, schemas: dict[str, IRSchema]):
        self.schemas = schemas
        self.type_service = UnifiedTypeService(schemas)

    def resolve(self, operation: IROperation, context: RenderContext) -> ResponseStrategy:
        """Determine how to handle this operation's response.

        Uses the response schema exactly as defined in the OpenAPI spec,
        with no unwrapping logic. What you see in the spec is what you get.

        Args:
            operation: The operation to analyze
            context: Render context for type resolution

        Returns:
            A ResponseStrategy that all components should use consistently
        """
        primary_response = self._get_primary_response(operation)

        if not primary_response:
            return ResponseStrategy(return_type="None", response_schema=None, is_streaming=False, response_ir=None)

        # Handle responses without content (e.g., 204)
        if not hasattr(primary_response, "content") or not primary_response.content:
            return ResponseStrategy(
                return_type="None", response_schema=None, is_streaming=False, response_ir=primary_response
            )

        # Handle streaming responses
        if hasattr(primary_response, "stream") and primary_response.stream:
            return self._resolve_streaming_strategy(primary_response, context)

        # Check if response has multiple content types
        content_types = list(primary_response.content.keys()) if primary_response.content else []
        if len(content_types) > 1:
            return self._resolve_multi_content_type_strategy(primary_response, context)

        # Single content type - get the response schema
        response_schema = self._get_response_schema(primary_response)

        # If no schema provided, try to infer type from content-type
        if not response_schema:
            # Try to infer type from content-type (e.g., text/plain → str, application/pdf → bytes)
            if content_types:
                inferred_type = self._resolve_content_type_to_python_type(content_types[0], None, context)
                if inferred_type:
                    return ResponseStrategy(
                        return_type=inferred_type,
                        response_schema=None,
                        is_streaming=False,
                        response_ir=primary_response,
                    )

            # No schema and couldn't infer type
            return ResponseStrategy(
                return_type="None", response_schema=None, is_streaming=False, response_ir=primary_response
            )

        # Use the response schema as-is from the OpenAPI spec
        return_type = self.type_service.resolve_schema_type(response_schema, context, required=True)

        return ResponseStrategy(
            return_type=return_type, response_schema=response_schema, is_streaming=False, response_ir=primary_response
        )

    def _get_primary_response(self, operation: IROperation) -> IRResponse | None:
        """Get the primary success response from an operation."""
        if not operation.responses:
            return None

        # Priority order: 200, 201, 202, 204, other 2xx, default
        for code in ["200", "201", "202", "204"]:
            for response in operation.responses:
                if response.status_code == code:
                    return response

        # Other 2xx responses
        for response in operation.responses:
            if response.status_code.startswith("2"):
                return response

        # Default response
        for response in operation.responses:
            if response.status_code == "default":
                return response

        # First response as fallback
        return operation.responses[0] if operation.responses else None

    def _get_response_schema(self, response: IRResponse) -> IRSchema | None:
        """Get the schema from a response's content."""
        if not response.content:
            return None

        # Prefer application/json
        content_types = list(response.content.keys())
        content_type = None

        if "application/json" in content_types:
            content_type = "application/json"
        elif any("json" in ct for ct in content_types):
            content_type = next(ct for ct in content_types if "json" in ct)
        elif content_types:
            content_type = content_types[0]

        if not content_type:
            return None

        return response.content.get(content_type)

    def _resolve_streaming_strategy(self, response: IRResponse, context: RenderContext) -> ResponseStrategy:
        """Resolve strategy for streaming responses."""
        # Add AsyncIterator import
        context.add_import("typing", "AsyncIterator")

        # Determine the item type for the stream
        if not response.content:
            # Binary stream with no specific content type
            return ResponseStrategy(
                return_type="AsyncIterator[bytes]", response_schema=None, is_streaming=True, response_ir=response
            )

        # Check for binary content types
        content_types = list(response.content.keys())
        is_binary = any(
            ct in ["application/octet-stream", "application/pdf"] or ct.startswith(("image/", "audio/", "video/"))
            for ct in content_types
        )

        if is_binary:
            return ResponseStrategy(
                return_type="AsyncIterator[bytes]", response_schema=None, is_streaming=True, response_ir=response
            )

        # For event streams (text/event-stream) or JSON streams
        is_event_stream = any("event-stream" in ct for ct in content_types)
        if is_event_stream:
            context.add_import("typing", "Dict")
            context.add_import("typing", "Any")
            return ResponseStrategy(
                return_type="AsyncIterator[dict[str, Any]]",
                response_schema=None,
                is_streaming=True,
                response_ir=response,
            )

        # For other streaming content, try to resolve the schema
        schema = self._get_response_schema(response)
        if schema:
            schema_type = self.type_service.resolve_schema_type(schema, context, required=True)
            return ResponseStrategy(
                return_type=f"AsyncIterator[{schema_type}]",
                response_schema=schema,
                is_streaming=True,
                response_ir=response,
            )

        # Default to bytes if we can't determine the type
        return ResponseStrategy(
            return_type="AsyncIterator[bytes]", response_schema=None, is_streaming=True, response_ir=response
        )

    def _resolve_multi_content_type_strategy(self, response: IRResponse, context: RenderContext) -> ResponseStrategy:
        """Resolve strategy for responses with multiple content types.

        When a response defines multiple content types, generate a Union return type
        and store the mapping for content-type-based response handling.

        Args:
            response: The response with multiple content types
            context: Render context for type resolution

        Returns:
            ResponseStrategy with Union return type and content_type_mapping
        """
        if not response.content:
            return ResponseStrategy(return_type="None", response_schema=None, is_streaming=False, response_ir=response)

        content_types = list(response.content.keys())
        logger.info(f"Detected response with multiple content types: {content_types}")

        # Resolve each content type to its Python type
        content_type_mapping: dict[str, str] = {}
        resolved_types: list[str] = []

        for content_type in content_types:
            python_type = self._resolve_content_type_to_python_type(
                content_type, response.content[content_type], context
            )

            if python_type:
                content_type_mapping[content_type] = python_type
                if python_type not in resolved_types:  # Avoid duplicates in Union
                    resolved_types.append(python_type)

        # If no types were resolved, default to None
        if not resolved_types:
            return ResponseStrategy(return_type="None", response_schema=None, is_streaming=False, response_ir=response)

        # If only one unique type, no need for Union
        if len(resolved_types) == 1:
            return ResponseStrategy(
                return_type=resolved_types[0],
                response_schema=response.content.get(content_types[0]),
                is_streaming=False,
                response_ir=response,
                content_type_mapping=content_type_mapping,
            )

        # Create Union type
        context.add_import("typing", "Union")
        union_type = f"Union[{', '.join(resolved_types)}]"

        logger.info(f"Generated Union return type: {union_type}")

        return ResponseStrategy(
            return_type=union_type,
            response_schema=None,  # No single schema for Union
            is_streaming=False,
            response_ir=response,
            content_type_mapping=content_type_mapping,
        )

    def _resolve_content_type_to_python_type(
        self, content_type: str, schema: IRSchema | None, context: RenderContext
    ) -> str | None:
        """Resolve a content type and its schema to a Python type.

        Args:
            content_type: The HTTP content type (e.g., 'application/json')
            schema: The schema for this content type (may be None)
            context: Render context for type resolution

        Returns:
            Python type string or None if cannot be resolved
        """
        # Handle binary content types
        if content_type in ["application/octet-stream", "application/pdf"] or content_type.startswith(
            ("image/", "audio/", "video/")
        ):
            return "bytes"

        # Handle text content types
        if content_type.startswith("text/"):
            # text/html, text/plain, etc. can be either str or bytes depending on the schema
            if schema and hasattr(schema, "type"):
                if schema.type == "string" and hasattr(schema, "format") and schema.format == "binary":
                    return "bytes"
                return "str"
            # Text content without schema should be str by default (text is naturally string-based)
            return "str"

        # Handle JSON content types
        if "json" in content_type and schema:
            return self.type_service.resolve_schema_type(schema, context, required=True)

        # Handle other content types with schema
        if schema:
            return self.type_service.resolve_schema_type(schema, context, required=True)

        # Unknown content type
        logger.warning(f"Unknown content type '{content_type}', defaulting to bytes")
        return "bytes"
