"""Orchestrates IRSchema to Python type resolution."""

import logging
from typing import Dict, Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer

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
        Orchestrates calls to specialized resolvers.
        """
        if schema is None:
            logger.warning(
                f"[SchemaTypeResolver ID:None] Input schema is None. Defaulting to 'Any'. Context: required={required}, resolve_alias_target={resolve_alias_target}, current_schema_context_name={current_schema_context_name}"
            )
            self.context.add_import("typing", "Any")
            return "Any"

        # logger.debug(
        #     f"[SchemaTypeResolver ID:{id(schema)}] Entry: schema.name='{schema.name}', type='{schema.type}', required={required}, resolve_alias_target={resolve_alias_target}, current_schema_context_name='{current_schema_context_name}'"
        # )

        py_type_str: Optional[str] = None

        # Effective context name for promoting anonymous children/properties.
        effective_parent_context_name = (
            current_schema_context_name if current_schema_context_name is not None else schema.name
        )

        # 1. Handle direct named types (models, enums) if not resolving alias target
        if not resolve_alias_target:
            py_type_str = self.named_resolver.resolve(schema, resolve_alias_target=resolve_alias_target)
            if py_type_str:
                # Named resolver already handles simple aliases by returning None if they should be structurally resolved.
                # If it returns a name, it's a direct model/enum class name.
                # Optionality is handled by the finalizer based on the schema's own definition or usage.
                # logger.debug(
                #     f"[SchemaTypeResolver ID:{id(schema)}] Resolved by NamedTypeResolver (not resolving alias target) to '{py_type_str}'."
                # )
                return self.finalizer.finalize(py_type_str, schema, required)

        # If resolving alias target, or if not a directly named type above, proceed with structural resolution:

        # 2. Enums (again, in case it's an unnamed enum or simple alias that named_resolver skipped)
        # NamedTypeResolver.resolve handles named enums, unnamed enums (returns base type), and simple aliases (returns None)
        # This re-check might seem redundant but covers cases where resolve_alias_target=True for a named enum,
        # or for unnamed enums if the first path (not resolve_alias_target) was skipped.
        # Essentially, if `schema.enum` is present, we try `named_resolver` regardless of `resolve_alias_target` now.
        if schema.enum:
            # When resolve_alias_target is true, we still want the name if it is a named enum.
            # If it's an unnamed enum, it gives base type.
            # If it's a named alias TO an enum, this path is tricky. Current named_resolver gives the alias name or None.
            temp_enum_type = self.named_resolver.resolve(schema, resolve_alias_target=resolve_alias_target)
            if temp_enum_type:
                py_type_str = temp_enum_type
                # logger.debug(
                #     f"[SchemaTypeResolver ID:{id(schema)}] Resolved by NamedTypeResolver (enum check) to '{py_type_str}'."
                # )

        # 3. Composition types (anyOf, oneOf, allOf)
        if not py_type_str:
            py_type_str = self.composition_resolver.resolve(schema)
            if py_type_str:
                # logger.debug(
                #     f"[SchemaTypeResolver ID:{id(schema)}] Resolved by CompositionTypeResolver to '{py_type_str}'."
                # )
                pass

        # 4. Primitive types
        if not py_type_str:
            py_type_str = self.primitive_resolver.resolve(schema)
            if py_type_str:
                # logger.debug(
                #     f"[SchemaTypeResolver ID:{id(schema)}] Resolved by PrimitiveTypeResolver to '{py_type_str}'."
                # )
                pass

        # 5. Array types
        if not py_type_str:
            py_type_str = self.array_resolver.resolve(
                schema,
                parent_name_hint=effective_parent_context_name,
                resolve_alias_target=resolve_alias_target,
            )
            if py_type_str:
                # logger.debug(f"[SchemaTypeResolver ID:{id(schema)}] Resolved by ArrayTypeResolver to '{py_type_str}'.")
                pass

        # 6. Object types
        if not py_type_str:
            py_type_str = self.object_resolver.resolve(
                schema, parent_schema_name_for_anon_promotion=effective_parent_context_name
            )
            if py_type_str:
                # logger.debug(f"[SchemaTypeResolver ID:{id(schema)}] Resolved by ObjectTypeResolver to '{py_type_str}'.")
                pass

        # Fallback if no type determined
        if not py_type_str:
            self.context.add_import("typing", "Any")
            py_type_str = "Any"

        return self.finalizer.finalize(py_type_str, schema, required)
