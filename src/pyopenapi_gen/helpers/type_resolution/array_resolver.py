"""Resolves IRSchema to Python List types."""

import logging
from typing import TYPE_CHECKING, Dict, Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

if TYPE_CHECKING:
    from .resolver import SchemaTypeResolver  # Avoid circular import

logger = logging.getLogger(__name__)


class ArrayTypeResolver:
    """Resolves IRSchema instances of type 'array'."""

    def __init__(self, context: RenderContext, all_schemas: Dict[str, IRSchema], main_resolver: "SchemaTypeResolver"):
        self.context = context
        self.all_schemas = all_schemas
        self.main_resolver = main_resolver  # For resolving item types

    def resolve(self, schema: IRSchema, parent_name_hint: Optional[str] = None) -> Optional[str]:
        """
        Resolves an IRSchema of `type: "array"` to a Python `List[...]` type string.

        Args:
            schema: The IRSchema, expected to have `type: "array"`.
            parent_name_hint: Optional name of the containing schema for context.

        Returns:
            A Python type string like "List[ItemType]" or None.
        """
        if schema.type == "array":
            item_type: str
            if schema.items:
                # Use the main resolver to get the type of the items
                item_type = self.main_resolver.resolve(
                    schema.items,
                    required=True,  # Item nullability handled by item schema itself
                    current_schema_context_name=parent_name_hint,
                )
            else:
                item_type = "Any"
                self.context.add_import("typing", "Any")

            self.context.add_import("typing", "List")
            logger.debug(
                f"[ArrayTypeResolver] Resolved array with item type '{item_type}' for schema '{schema.name or 'anonymous'}'."
            )
            return f"List[{item_type}]"
        return None
