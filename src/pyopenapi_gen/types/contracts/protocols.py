"""Protocols for type resolution components."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Protocol, runtime_checkable

from pyopenapi_gen import IROperation, IRResponse, IRSchema
from pyopenapi_gen.context.render_context import RenderContext

from .types import ResolvedType


@runtime_checkable
class TypeContext(Protocol):
    """Context for type resolution operations."""

    def add_import(self, module: str, name: str) -> None:
        """Add an import to the context."""
        ...

    def add_conditional_import(self, condition: str, module: str, name: str) -> None:
        """Add a conditional import (e.g., TYPE_CHECKING)."""
        ...


class ReferenceResolver(ABC):
    """Resolves OpenAPI $ref references to target schemas."""

    @abstractmethod
    def resolve_ref(self, ref: str) -> Optional[IRSchema]:
        """
        Resolve a $ref string to the target schema.

        Args:
            ref: Reference string like "#/components/schemas/User"

        Returns:
            Target schema or None if not found
        """
        pass

    @abstractmethod
    def resolve_response_ref(self, ref: str) -> Optional[IRResponse]:
        """
        Resolve a response $ref to the target response.

        Args:
            ref: Reference string like "#/components/responses/UserResponse"

        Returns:
            Target response or None if not found
        """
        pass


class SchemaTypeResolver(ABC):
    """Resolves IRSchema objects to Python types."""

    @abstractmethod
    def resolve_schema(self, schema: IRSchema, context: TypeContext, required: bool = True) -> ResolvedType:
        """
        Resolve a schema to a Python type.

        Args:
            schema: The schema to resolve
            context: Type resolution context
            required: Whether the field is required

        Returns:
            Resolved Python type information
        """
        pass


class ResponseTypeResolver(ABC):
    """Resolves operation responses to Python types."""

    @abstractmethod
    def resolve_operation_response(self, operation: IROperation, context: TypeContext) -> ResolvedType:
        """
        Resolve an operation's primary response to a Python type.

        Args:
            operation: The operation to resolve
            context: Type resolution context

        Returns:
            Resolved Python type information
        """
        pass

    @abstractmethod
    def resolve_specific_response(self, response: IRResponse, context: TypeContext) -> ResolvedType:
        """
        Resolve a specific response to a Python type.

        Args:
            response: The response to resolve
            context: Type resolution context

        Returns:
            Resolved Python type information
        """
        pass
