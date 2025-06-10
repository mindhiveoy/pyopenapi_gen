"""Unified type resolution service."""

import logging
from typing import Dict, Optional

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext

from ..contracts.types import ResolvedType
from ..resolvers import OpenAPIReferenceResolver, OpenAPIResponseResolver, OpenAPISchemaResolver

logger = logging.getLogger(__name__)


class RenderContextAdapter:
    """Adapter to make RenderContext compatible with TypeContext protocol."""

    def __init__(self, render_context: RenderContext):
        self.render_context = render_context

    def add_import(self, module: str, name: str) -> None:
        """Add an import to the context."""
        self.render_context.add_import(module, name)

    def add_conditional_import(self, condition: str, module: str, name: str) -> None:
        """Add a conditional import (e.g., TYPE_CHECKING)."""
        self.render_context.add_conditional_import(condition, module, name)


class UnifiedTypeService:
    """
    Unified service for all type resolution needs.

    This is the main entry point for converting OpenAPI schemas, responses,
    and operations to Python type strings.
    """

    def __init__(self, schemas: Dict[str, IRSchema], responses: Optional[Dict[str, IRResponse]] = None):
        """
        Initialize the type service.

        Args:
            schemas: Dictionary of all schemas by name
            responses: Dictionary of all responses by name (optional)
        """
        self.ref_resolver = OpenAPIReferenceResolver(schemas, responses)
        self.schema_resolver = OpenAPISchemaResolver(self.ref_resolver)
        self.response_resolver = OpenAPIResponseResolver(self.ref_resolver, self.schema_resolver)

    def resolve_schema_type(
        self, schema: IRSchema, context: RenderContext, required: bool = True, resolve_underlying: bool = False
    ) -> str:
        """
        Resolve a schema to a Python type string.

        Args:
            schema: The schema to resolve
            context: Render context for imports
            required: Whether the field is required
            resolve_underlying: If True, resolve underlying type for aliases instead of schema name

        Returns:
            Python type string
        """
        # Check if the schema itself is nullable
        # If schema.is_nullable=True, it should be Optional regardless of required
        effective_required = required and not getattr(schema, "is_nullable", False)

        type_context = RenderContextAdapter(context)
        resolved = self.schema_resolver.resolve_schema(schema, type_context, effective_required, resolve_underlying)
        return self._format_resolved_type(resolved, context)

    def resolve_operation_response_type(self, operation: IROperation, context: RenderContext) -> str:
        """
        Resolve an operation's response to a Python type string.

        Args:
            operation: The operation to resolve
            context: Render context for imports

        Returns:
            Python type string
        """
        type_context = RenderContextAdapter(context)
        resolved = self.response_resolver.resolve_operation_response(operation, type_context)
        return self._format_resolved_type(resolved, context)

    def resolve_operation_response_with_unwrap_info(
        self, operation: IROperation, context: RenderContext
    ) -> tuple[str, bool]:
        """
        Resolve an operation's response to a Python type string with unwrapping information.

        Args:
            operation: The operation to resolve
            context: Render context for imports

        Returns:
            Tuple of (Python type string, was_unwrapped flag)
        """
        type_context = RenderContextAdapter(context)
        resolved = self.response_resolver.resolve_operation_response(operation, type_context)
        python_type = self._format_resolved_type(resolved, context)
        return python_type, resolved.was_unwrapped

    def resolve_response_type(self, response: IRResponse, context: RenderContext) -> str:
        """
        Resolve a specific response to a Python type string.

        Args:
            response: The response to resolve
            context: Render context for imports

        Returns:
            Python type string
        """
        type_context = RenderContextAdapter(context)
        resolved = self.response_resolver.resolve_specific_response(response, type_context)
        return self._format_resolved_type(resolved, context)

    def _format_resolved_type(self, resolved: ResolvedType, context: RenderContext = None) -> str:
        """Format a ResolvedType into a Python type string."""
        python_type = resolved.python_type

        if resolved.is_optional and not python_type.startswith("Optional["):
            if context:
                context.add_import("typing", "Optional")
            python_type = f"Optional[{python_type}]"

        if resolved.is_forward_ref and not python_type.startswith('"'):
            python_type = f'"{python_type}"'

        return python_type
