"""Helper functions for determining Python types and managing related imports from IRSchema."""

import logging
from typing import Dict, Optional  # Keep Optional for type hints if any remain

from pyopenapi_gen import IRSchema  # Assuming top-level import is intended
from pyopenapi_gen.context.render_context import RenderContext
# Removed NameSanitizer, TypeCleaner as they are used in sub-resolvers or TypeFinalizer

# Import the new main resolver
from .type_resolution.resolver import SchemaTypeResolver

logger = logging.getLogger(__name__)


class TypeHelper:
    """
    Provides a method to determine appropriate Python type hints for IRSchema objects
    by delegating to the SchemaTypeResolver.
    All detailed type resolution logic has been moved to the `type_resolution` sub-package.
    """

    @staticmethod
    def get_python_type_for_schema(
        schema: IRSchema,
        all_schemas: Dict[str, IRSchema],
        context: RenderContext,
        required: bool = True,
        resolve_alias_target: bool = False,
        current_schema_context_name: Optional[str] = None,
    ) -> str:
        """
        Determines the Python type string for a given IRSchema by delegating
        to the SchemaTypeResolver.

        Args:
            schema: The IRSchema instance to determine the Python type for.
            all_schemas: A dictionary of all known (named) IRSchema instances.
            context: The RenderContext instance for managing imports.
            required: If the schema represents a required field/parameter.
            resolve_alias_target: If True, forces resolution to the aliased type.
            current_schema_context_name: Context name for promoting anonymous items/properties.

        Returns:
            A string representing the Python type for the schema.
        """
        # Instantiate the main resolver and call its resolve method
        resolver = SchemaTypeResolver(context=context, all_schemas=all_schemas)
        return resolver.resolve(
            schema=schema,
            required=required,
            resolve_alias_target=resolve_alias_target,
            current_schema_context_name=current_schema_context_name,
        )


# Removed all previous static methods like _get_primitive_type, _get_composition_type, etc.
# as their logic is now in the type_resolution package.
# TypeCleaner is imported and used directly by TypeFinalizer.
# NameSanitizer is imported and used by specific resolvers (NamedTypeResolver, ObjectTypeResolver).
