"""
Implementation of the visitor pattern for OpenAPI IR model traversal.

This module provides the core visitor pattern implementation used throughout the PyOpenAPI
Generator to transform IR (Intermediate Representation) nodes into Python code. It defines
the base Visitor class that all specific visitors inherit from, and a Registry class for
managing visitor method registration.
"""

from typing import Callable, Generic, Type, TypeVar

from ..context.render_context import RenderContext

# Type variables for node and return type
tNode = TypeVar("tNode")  # Type variable for IR node types
tRet = TypeVar("tRet")  # Type variable for visitor return types


class Visitor(Generic[tNode, tRet]):
    """
    Base class for all visitors implementing the visitor pattern.

    This class provides the foundation for traversing and transforming IR nodes
    into Python code representations. Subclasses should implement visit_<NodeType>
    methods for each IR node type they want to handle.

    Type parameters:
        tNode: The type of node being visited
        tRet: The return type of the visitor methods
    """

    def visit(self, node: tNode, context: "RenderContext") -> tRet:
        """
        Visit a node and dispatch to the appropriate visit_* method.

        Args:
            node: The IR node to visit
            context: The rendering context containing state for the code generation

        Returns:
            The result of visiting the node, type depends on the specific visitor
        """
        method_name = f"visit_{type(node).__name__}"
        visitor: Callable[[tNode, "RenderContext"], tRet] = getattr(self, method_name, self.generic_visit)
        return visitor(node, context)

    def generic_visit(self, node: tNode, context: "RenderContext") -> tRet:
        """
        Default handler for node types without a specific visitor method.

        Args:
            node: The IR node to visit
            context: The rendering context containing state for the code generation

        Raises:
            NotImplementedError: Always raised to indicate missing visitor implementation
        """
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined.")


class Registry(Generic[tNode, tRet]):
    """
    Registry for associating IR node types with visitor handler functions.

    This registry allows for plugins or extensions to register custom handlers
    for specific IR node types, enabling extensibility in the code generation process.

    Type parameters:
        tNode: The type of node being visited
        tRet: The return type of the visitor methods
    """

    def __init__(self) -> None:
        """Initialize an empty visitor registry."""
        self._registry: dict[Type[tNode], Callable[[tNode, "RenderContext"], tRet]] = {}

    def register(self, node_type: Type[tNode], visitor: Callable[[tNode, "RenderContext"], tRet]) -> None:
        """
        Register a visitor function for a specific node type.

        Args:
            node_type: The IR node type to register a handler for
            visitor: The function that will handle visiting nodes of this type
        """
        self._registry[node_type] = visitor

    def get_visitor(self, node_type: Type[tNode]) -> Callable[[tNode, "RenderContext"], tRet] | None:
        """
        Retrieve the visitor function for a specific node type.

        Args:
            node_type: The IR node type to get a handler for

        Returns:
            The registered visitor function or None if no handler is registered
        """
        return self._registry.get(node_type)
