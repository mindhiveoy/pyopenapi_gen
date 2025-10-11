"""Resolves IRSchema composition types (anyOf, oneOf, allOf)."""

import logging
from typing import TYPE_CHECKING, List

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

if TYPE_CHECKING:
    from .resolver import SchemaTypeResolver  # Avoid circular import

logger = logging.getLogger(__name__)


class CompositionTypeResolver:
    """Resolves IRSchema instances with anyOf, oneOf, or allOf."""

    def __init__(self, context: RenderContext, all_schemas: dict[str, IRSchema], main_resolver: "SchemaTypeResolver"):
        self.context = context
        self.all_schemas = all_schemas
        self.main_resolver = main_resolver  # For resolving member types

    def resolve(self, schema: IRSchema) -> str | None:
        """
        Handles 'anyOf', 'oneOf', 'allOf' and returns a Python type string.
        'anyOf'/'oneOf' -> Union[...]
        'allOf' -> Type of first schema (simplification)
        """
        composition_schemas: List[IRSchema] | None = None
        composition_keyword: str | None = None

        if schema.any_of is not None:
            composition_schemas = schema.any_of
            composition_keyword = "anyOf"
        elif schema.one_of is not None:
            composition_schemas = schema.one_of
            composition_keyword = "oneOf"
        elif schema.all_of is not None:
            composition_schemas = schema.all_of
            composition_keyword = "allOf"

        if not composition_keyword or composition_schemas is None:
            return None

        if not composition_schemas:  # Empty list
            self.context.add_import("typing", "Any")
            return "Any"

        if composition_keyword == "allOf":
            if len(composition_schemas) == 1:
                resolved_type = self.main_resolver.resolve(composition_schemas[0], required=True)
                return resolved_type
            if composition_schemas:  # len > 1
                # Heuristic: return type of the FIRST schema for allOf with multiple items.
                first_schema_type = self.main_resolver.resolve(composition_schemas[0], required=True)
                return first_schema_type
            self.context.add_import("typing", "Any")  # Should be unreachable
            return "Any"

        if composition_keyword in ["anyOf", "oneOf"]:
            member_types: List[str] = []
            for sub_schema in composition_schemas:
                member_type = self.main_resolver.resolve(sub_schema, required=True)
                member_types.append(member_type)

            unique_types = sorted(list(set(member_types)))

            if not unique_types:
                self.context.add_import("typing", "Any")
                return "Any"

            if len(unique_types) == 1:
                return unique_types[0]

            self.context.add_import("typing", "Union")
            union_str = f"Union[{', '.join(unique_types)}]"
            return union_str

        return None
