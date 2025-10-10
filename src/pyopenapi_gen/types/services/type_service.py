"""Unified type resolution service."""

import logging

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

    def __init__(self, schemas: dict[str, IRSchema], responses: dict[str, IRResponse] | None = None):
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

        # DEBUG: Log resolved type before formatting
        if resolved.python_type and "[" in resolved.python_type:
            bracket_count_open = resolved.python_type.count("[")
            bracket_count_close = resolved.python_type.count("]")
            if bracket_count_open != bracket_count_close:
                logger.warning(
                    f"BRACKET MISMATCH BEFORE FORMAT: '{resolved.python_type}', "
                    f"schema_name: {getattr(schema, 'name', 'anonymous')}, "
                    f"schema_type: {getattr(schema, 'type', None)}, "
                    f"is_optional: {resolved.is_optional}"
                )

        formatted = self._format_resolved_type(resolved, context)

        # DEBUG: Log final formatted type
        if formatted and "[" in formatted:
            bracket_count_open = formatted.count("[")
            bracket_count_close = formatted.count("]")
            if bracket_count_open != bracket_count_close:
                logger.warning(f"BRACKET MISMATCH AFTER FORMAT: '{formatted}', " f"original: '{resolved.python_type}'")

        return formatted

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

    def _format_resolved_type(self, resolved: ResolvedType, context: RenderContext | None = None) -> str:
        """Format a ResolvedType into a Python type string.

        Architecture Guarantee: This method produces ONLY modern Python 3.10+ syntax (X | None).
        Optional[X] is NEVER generated - unified type system uses | None exclusively.
        """
        python_type = resolved.python_type

        # SANITY CHECK: Unified system should never produce Optional[X] internally
        if python_type.startswith("Optional["):
            logger.error(
                f"❌ ARCHITECTURE VIOLATION: Resolver produced legacy Optional[X]: {python_type}. "
                f"Unified type system must generate X | None directly. "
                f"This indicates a bug in schema/response/reference resolver."
            )
            # This should never happen in our unified system
            raise ValueError(
                f"Type resolver produced legacy Optional[X] syntax: {python_type}. "
                f"Unified type system must use X | None exclusively."
            )

        # Quote forward references BEFORE adding | None so we get: "DataSource" | None not "DataSource | None"
        if resolved.is_forward_ref and not python_type.startswith('"'):
            python_type = f'"{python_type}"'

        # Add modern | None syntax if needed
        # Modern Python 3.10+ uses | None syntax without needing Optional import
        if resolved.is_optional and not python_type.endswith("| None"):
            python_type = f"{python_type} | None"

            # DEBUG: Check for malformed type strings
            if python_type.count("[") != python_type.count("]"):
                logger.warning(
                    f"MALFORMED TYPE: Bracket mismatch in '{python_type}'. "
                    f"Original: '{resolved.python_type}', is_optional: {resolved.is_optional}"
                )

        return python_type
