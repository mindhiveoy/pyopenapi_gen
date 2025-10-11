"""Resolves IRSchema to Python List types."""

import logging
from typing import TYPE_CHECKING

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

if TYPE_CHECKING:
    from .resolver import SchemaTypeResolver  # Avoid circular import

logger = logging.getLogger(__name__)


class ArrayTypeResolver:
    """Resolves IRSchema instances of type 'array'."""

    def __init__(self, context: RenderContext, all_schemas: dict[str, IRSchema], main_resolver: "SchemaTypeResolver"):
        self.context = context
        self.all_schemas = all_schemas
        self.main_resolver = main_resolver  # For resolving item types

    def resolve(
        self,
        schema: IRSchema,
        parent_name_hint: str | None = None,
        resolve_alias_target: bool = False,
    ) -> str | None:
        """
        Resolves an IRSchema of `type: "array"` to a Python `List[...]` type string.

        Args:
            schema: The IRSchema, expected to have `type: "array"`.
            parent_name_hint: Optional name of the containing schema for context.
            resolve_alias_target: Whether to resolve alias targets.

        Returns:
            A Python type string like "List[ItemType]" or None.
        """
        if schema.type == "array":
            item_schema = schema.items
            if not item_schema:
                logger.warning(f"[ArrayTypeResolver] Array schema '{schema.name}' has no items. -> List[Any]")
                self.context.add_import("typing", "Any")
                self.context.add_import("typing", "List")
                return "List[Any]"

            item_type_str = self.main_resolver.resolve(
                item_schema,
                current_schema_context_name=parent_name_hint,
                resolve_alias_target=resolve_alias_target,
            )

            if item_type_str:
                self.context.add_import("typing", "List")
                return f"List[{item_type_str}]"
        return None
