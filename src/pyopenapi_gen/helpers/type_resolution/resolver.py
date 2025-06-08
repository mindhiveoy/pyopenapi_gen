"""Orchestrates IRSchema to Python type resolution."""

import logging
from typing import Dict, Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.types.services.type_service import UnifiedTypeService

from .array_resolver import ArrayTypeResolver
from .composition_resolver import CompositionTypeResolver
from .finalizer import TypeFinalizer
from .named_resolver import NamedTypeResolver
from .object_resolver import ObjectTypeResolver
from .primitive_resolver import PrimitiveTypeResolver

logger = logging.getLogger(__name__)


class SchemaTypeResolver:
    """Orchestrates the resolution of IRSchema to Python type strings."""

    def __init__(self, context: RenderContext, all_schemas: Dict[str, IRSchema]):
        self.context = context
        self.all_schemas = all_schemas

        # Initialize specialized resolvers, passing self for circular dependencies if needed
        self.primitive_resolver = PrimitiveTypeResolver(context)
        self.named_resolver = NamedTypeResolver(context, all_schemas)
        self.array_resolver = ArrayTypeResolver(context, all_schemas, self)
        self.object_resolver = ObjectTypeResolver(context, all_schemas, self)
        self.composition_resolver = CompositionTypeResolver(context, all_schemas, self)
        self.finalizer = TypeFinalizer(context, self.all_schemas)

    def resolve(
        self,
        schema: IRSchema,
        required: bool = True,
        resolve_alias_target: bool = False,
        current_schema_context_name: Optional[str] = None,
    ) -> str:
        """
        Determines the Python type string for a given IRSchema.
        Now delegates to the UnifiedTypeService for consistent type resolution.
        """
        # Delegate to the unified type service for all type resolution
        type_service = UnifiedTypeService(self.all_schemas)
        return type_service.resolve_schema_type(schema, self.context, required)
