"""Helper functions for determining Python types and managing related imports from IRSchema."""

import logging
from typing import Dict, Optional, Set

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.types.services.type_service import UnifiedTypeService

logger = logging.getLogger(__name__)

# Define PRIMITIVE_TYPES here since it's not available from imports
PRIMITIVE_TYPES = {"string", "integer", "number", "boolean", "null", "object", "array"}


class TypeHelper:
    """
    Provides a method to determine appropriate Python type hints for IRSchema objects
    by delegating to the SchemaTypeResolver.
    All detailed type resolution logic has been moved to the `type_resolution` sub-package.
    """

    # Cache for circular references detection
    _circular_refs_cache: Dict[str, Set[str]] = {}

    @staticmethod
    def detect_circular_references(schemas: Dict[str, IRSchema]) -> Set[str]:
        """
        Detect circular references in a set of schemas.

        Args:
            schemas: Dictionary of all schemas

        Returns:
            Set of schema names that are part of circular references
        """
        # Use a cache key based on the schema names (order doesn't matter)
        cache_key = ",".join(sorted(schemas.keys()))
        if cache_key in TypeHelper._circular_refs_cache:
            return TypeHelper._circular_refs_cache[cache_key]

        circular_refs: Set[str] = set()
        visited: Dict[str, Set[str]] = {}

        def visit(schema_name: str, path: Set[str]) -> None:
            """Visit a schema and check for circular references."""
            if schema_name in path:
                # Found a circular reference
                circular_refs.add(schema_name)
                circular_refs.update(path)
                return

            if schema_name in visited:
                # Already visited this schema
                return

            # Mark as visited with current path
            visited[schema_name] = set(path)

            # Get the schema
            schema = schemas.get(schema_name)
            if not schema:
                return

            # Check all property references
            for prop_name, prop in schema.properties.items():
                if prop.type and prop.type in schemas:
                    # This property references another schema
                    new_path = set(path)
                    new_path.add(schema_name)
                    visit(prop.type, new_path)

        # Visit each schema
        for schema_name in schemas:
            visit(schema_name, set())

        # Cache the result
        TypeHelper._circular_refs_cache[cache_key] = circular_refs
        return circular_refs

    @staticmethod
    def get_python_type_for_schema(
        schema: Optional[IRSchema],
        all_schemas: Dict[str, IRSchema],
        context: RenderContext,
        required: bool,
        resolve_alias_target: bool = False,
        render_mode: str = "field",  # Literal["field", "alias_target"]
        parent_schema_name: Optional[str] = None,
    ) -> str:
        """
        Determines the Python type string for a given IRSchema.
        Now delegates to the UnifiedTypeService for consistent type resolution.

        Args:
            schema: The IRSchema instance.
            all_schemas: All known (named) IRSchema instances.
            context: The RenderContext for managing imports.
            required: If the schema represents a required field/parameter.
            resolve_alias_target: If True, forces resolution to the aliased type (ignored - handled by unified service).
            render_mode: The mode of rendering (ignored - handled by unified service).
            parent_schema_name: The name of the parent schema for debug context (ignored - handled by unified service).

        Returns:
            A string representing the Python type for the schema.
        """
        # Delegate to the unified type service for all type resolution
        type_service = UnifiedTypeService(all_schemas)
        if schema is None:
            context.add_import("typing", "Any")
            return "Any"
        return type_service.resolve_schema_type(schema, context, required)
