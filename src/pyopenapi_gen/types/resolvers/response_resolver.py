"""Response type resolver implementation."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from pyopenapi_gen import IROperation, IRResponse, IRSchema

from ..contracts.protocols import ReferenceResolver, ResponseTypeResolver, SchemaTypeResolver, TypeContext
from ..contracts.types import ResolvedType

logger = logging.getLogger(__name__)


class OpenAPIResponseResolver(ResponseTypeResolver):
    """Resolves operation responses to Python types."""

    def __init__(self, ref_resolver: ReferenceResolver, schema_resolver: SchemaTypeResolver):
        """
        Initialize response resolver.

        Args:
            ref_resolver: Reference resolver for handling $ref
            schema_resolver: Schema resolver for handling schemas
        """
        self.ref_resolver = ref_resolver
        self.schema_resolver = schema_resolver

    def resolve_operation_response(self, operation: IROperation, context: TypeContext) -> ResolvedType:
        """
        Resolve an operation's primary response to a Python type.

        Args:
            operation: The operation to resolve
            context: Type resolution context

        Returns:
            Resolved Python type information
        """
        primary_response = self._get_primary_response(operation)

        if not primary_response:
            return ResolvedType(python_type="None")

        return self.resolve_specific_response(primary_response, context)

    def resolve_specific_response(self, response: IRResponse, context: TypeContext) -> ResolvedType:
        """
        Resolve a specific response to a Python type.

        Args:
            response: The response to resolve
            context: Type resolution context

        Returns:
            Resolved Python type information
        """
        # Handle response references
        if hasattr(response, "ref") and response.ref:
            return self._resolve_response_reference(response.ref, context)

        # Handle streaming responses (check before content validation)
        if hasattr(response, "stream") and response.stream:
            return self._resolve_streaming_response(response, context)

        # Handle responses without content (e.g., 204)
        if not hasattr(response, "content") or not response.content:
            return ResolvedType(python_type="None")

        # Get the content schema
        schema = self._get_response_schema(response)
        if not schema:
            return ResolvedType(python_type="None")

        # Resolve the schema directly (no unwrapping)
        resolved = self.schema_resolver.resolve_schema(schema, context, required=True)
        return resolved

    def _resolve_response_reference(self, ref: str, context: TypeContext) -> ResolvedType:
        """Resolve a response $ref."""
        target_response = self.ref_resolver.resolve_response_ref(ref)
        if not target_response:
            logger.warning(f"Could not resolve response reference: {ref}")
            return ResolvedType(python_type="None")

        return self.resolve_specific_response(target_response, context)

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

    def _resolve_streaming_response(self, response: IRResponse, context: TypeContext) -> ResolvedType:
        """
        Resolve a streaming response to an AsyncIterator type.

        Args:
            response: The streaming response
            context: Type resolution context

        Returns:
            ResolvedType with AsyncIterator type
        """
        # Add AsyncIterator import
        context.add_import("typing", "AsyncIterator")

        # Determine the item type for the stream
        if not response.content:
            # Binary stream with no specific content type
            return ResolvedType(python_type="AsyncIterator[bytes]")

        # Check for binary content types
        content_types = list(response.content.keys())
        is_binary = any(
            ct in ["application/octet-stream", "application/pdf"] or ct.startswith(("image/", "audio/", "video/"))
            for ct in content_types
        )

        if is_binary:
            return ResolvedType(python_type="AsyncIterator[bytes]")

        # For event streams (text/event-stream) or JSON streams
        is_event_stream = any("event-stream" in ct for ct in content_types)
        if is_event_stream:
            context.add_import("typing", "Dict")
            context.add_import("typing", "Any")
            return ResolvedType(python_type="AsyncIterator[Dict[str, Any]]")

        # For other streaming content, try to resolve the schema
        schema = self._get_response_schema(response)
        if schema:
            resolved = self.schema_resolver.resolve_schema(schema, context, required=True)
            return ResolvedType(python_type=f"AsyncIterator[{resolved.python_type}]")

        # Default to bytes if we can't determine the type
        return ResolvedType(python_type="AsyncIterator[bytes]")
