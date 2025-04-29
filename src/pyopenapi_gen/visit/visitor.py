from typing import Any, Dict, Type, Callable, TypeVar, Generic, Set, Optional
from pyopenapi_gen import (
    IRSpec,
    IRSchema,
    IROperation,
    IRParameter,
    IRResponse,
    IRRequestBody,
)
from ..context.render_context import RenderContext
from ..core.utils import NameSanitizer

# Type variables for node and return type
tNode = TypeVar("tNode")
tRet = TypeVar("tRet")


class Visitor(Generic[tNode, tRet]):
    """Base class for all visitors. Subclass and implement visit_<NodeType> methods."""

    def visit(self, node: tNode, context: "RenderContext") -> tRet:
        method_name = f"visit_{type(node).__name__}"
        visitor: Callable[[tNode, "RenderContext"], tRet] = getattr(
            self, method_name, self.generic_visit
        )
        return visitor(node, context)

    def generic_visit(self, node: tNode, context: "RenderContext") -> tRet:
        raise NotImplementedError(f"No visit_{type(node).__name__} method defined.")


class Registry(Generic[tNode, tRet]):
    """Registry for associating IR node types with visitor classes."""

    def __init__(self) -> None:
        self._registry: Dict[Type[tNode], Callable[[tNode, "RenderContext"], tRet]] = {}

    def register(
        self, node_type: Type[tNode], visitor: Callable[[tNode, "RenderContext"], tRet]
    ) -> None:
        self._registry[node_type] = visitor

    def get_visitor(
        self, node_type: Type[tNode]
    ) -> Optional[Callable[[tNode, "RenderContext"], tRet]]:
        return self._registry.get(node_type)
