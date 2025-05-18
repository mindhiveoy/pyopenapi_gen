"""Resolves IRSchema to Python named types (classes, enums)."""

import logging
import os
from typing import Dict, Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer

logger = logging.getLogger(__name__)


class NamedTypeResolver:
    """Resolves IRSchema instances that refer to named models/enums."""

    def __init__(self, context: RenderContext, all_schemas: Dict[str, IRSchema]):
        self.context = context
        self.all_schemas = all_schemas

    def resolve(self, schema: IRSchema, resolve_alias_target: bool = False) -> Optional[str]:
        """
        Resolves an IRSchema that refers to a named model/enum, or an inline named enum.

        Args:
            schema: The IRSchema to resolve.
            resolve_alias_target: If true, the resolver should return the Python type string for the *target* of an alias.
                                 If false, it should return the alias name itself (for type hinting).

        Returns:
            A Python type string for the resolved schema, e.g., "MyModel", "Optional[MyModel]".
        """
        # ==== TARGETED LOGGING START ====
        log_trigger_ntr = False
        schema_name_str = schema.name if schema and schema.name else ""

        if "embedding" in schema_name_str.lower():
            log_trigger_ntr = True

        if log_trigger_ntr:
            logger.critical(f"[NTR_TARGET_LOG] NamedTypeResolver.resolve ENTRY:")
            logger.critical(
                f"  schema.name: {schema_name_str}, schema.is_nullable: {schema.is_nullable if schema else 'N/A'}"
            )
            schema_dict_str = schema.to_dict() if schema and hasattr(schema, "to_dict") else "N/A"
            logger.critical(f"  schema_details: {schema_dict_str}")
            logger.critical(f"  self.context.current_file: {self.context.current_file}")
        # ==== TARGETED LOGGING END ====

        logger.debug(
            f"[NamedTypeResolver ID:{id(schema)}] Entry: schema.name='{schema.name}', type='{schema.type}', schema.name in all_schemas: {schema.name in self.all_schemas if schema.name else False}"
        )

        if schema.name and schema.name in self.all_schemas:
            # This schema is a REFERENCE to a globally defined schema (e.g., in components/schemas)
            ref_schema = self.all_schemas[schema.name]  # Get the actual definition
            assert ref_schema.name is not None, f"Schema '{schema.name}' resolved to ref_schema with None name."

            class_name_for_ref = NameSanitizer.sanitize_class_name(ref_schema.name)
            module_name_for_ref = NameSanitizer.sanitize_module_name(ref_schema.name)
            model_module_path_for_ref = (
                f"{self.context.get_current_package_name_for_generated_code()}.models.{module_name_for_ref}"
            )

            # ==== VECTOR_DATABASE DETAILED TRACE LOGGING START ====
            if schema.name and schema.name.lower() == "vectordatabase":
                is_structurally_alias_like_check = not (
                    ref_schema.properties
                    or ref_schema.enum
                    or ref_schema.any_of
                    or ref_schema.one_of
                    or ref_schema.all_of
                )
                logger.error(
                    f"[NTR_VD_DETAIL_TRACE] schema.name='{schema.name}', ref_schema.name='{ref_schema.name}', "
                    f"resolve_alias_target={resolve_alias_target}, ref_schema.enum_is_not_none={ref_schema.enum is not None}, "
                    f"is_structurally_alias_like_check={is_structurally_alias_like_check}, "
                    f"ref_schema.properties is None: {ref_schema.properties is None}, "
                    f"ref_schema.type: {ref_schema.type}"
                )
            # ==== VECTOR_DATABASE DETAILED TRACE LOGGING END ====

            if not resolve_alias_target:
                # For type hinting (default case), always use the referenced schema's own name
                # and ensure it's imported. This applies to direct model usage, enums,
                # or aliases (e.g. MyObjectAlias, MyArrayAlias, MyStringAlias).
                logger.debug(
                    f"[NamedTypeResolver] REF to '{schema.name}' (actual def: '{ref_schema.name}'). "
                    f"Not resolving target. Returning its name: '{class_name_for_ref}'. "
                    f"Import from: '{model_module_path_for_ref}'."
                )
                self.context.add_import(logical_module=model_module_path_for_ref, name=class_name_for_ref)
                return class_name_for_ref
            else:
                # self.resolve_alias_target is TRUE. We are trying to find the *actual underlying type*
                # of 'ref_schema' for use in an alias definition (e.g., MyStringAlias: TypeAlias = str).
                logger.debug(
                    f"[NamedTypeResolver] REF to '{schema.name}' (actual def: '{ref_schema.name}'). "
                    f"RESOLVING TARGET (resolve_alias_target=True)."
                )
                # Check if ref_schema is structurally a simple alias (no properties, enum, composition)
                is_structurally_simple_alias = not (
                    ref_schema.properties
                    or ref_schema.enum
                    or ref_schema.any_of
                    or ref_schema.one_of
                    or ref_schema.all_of
                )

                if is_structurally_simple_alias:
                    # It's an alias to a primitive, array, or simple object.
                    # We need to return the Python type of its target.
                    # For this, we delegate back to the main resolver, but on ref_schema's definition,
                    # and crucially, with resolve_alias_target=False for that sub-call to avoid loops
                    # and to get the structural type.
                    # Also, treat ref_schema as anonymous for this sub-resolution so it's purely structural.

                    # Construct a temporary schema that is like ref_schema but anonymous
                    # to force structural resolution by the main resolver.
                    # This is a bit of a workaround for not having direct access to other resolvers here.
                    # A better design might involve passing the main SchemaTypeResolver instance.
                    # For now, returning None effectively tells TypeHelper to do this.
                    logger.debug(
                        f"[NamedTypeResolver] REF target resolve: '{ref_schema.name}' is structurally a simple alias "
                        f"to type '{ref_schema.type}'. Deferring to structural resolution for its target by returning None."
                    )
                    return None  # Signal to TypeHelper to resolve ref_schema structurally.
                else:
                    # ref_schema is NOT structurally alias-like (e.g., it's a full object schema).
                    # If we are resolving an alias target, and the target is a full object schema,
                    # the "target type" IS that object schema's name.
                    # e.g. MyDataAlias = DataObject. Here, DataObject is the target.
                    # The AliasGenerator will then generate "MyDataAlias: TypeAlias = DataObject".
                    # It needs "DataObject" as the string.
                    # The import for DataObject will be handled by TypeHelper when generating that alias file itself, using the regular non-alias-target path.
                    logger.debug(
                        f"[NamedTypeResolver] resolve_alias_target=True, ref_schema '{ref_schema.name}' "
                        f"is NOT structurally_alias_like. Returning its class name for AliasGenerator: {class_name_for_ref}"
                    )
                    # Simplified and very specific trace for VectorDatabase import path
                    if ref_schema.name and ref_schema.name.lower() == "vectordatabase":
                        logger.error(
                            f"!!!!!!!!!! [NTR_VD_FINAL_TRACE] About to import VectorDatabase for Alias Target. "
                            f"Context file: {self.context.current_file}, resolve_alias_target: {resolve_alias_target} !!!!!!"
                        )
                    self.context.add_import(logical_module=model_module_path_for_ref, name=class_name_for_ref)
                    return (
                        class_name_for_ref  # Return the name of the referenced complex type for AliasGenerator's RHS.
                    )

        elif schema.enum:
            # This is an INLINE enum definition (not a reference to a global enum)
            enum_name: Optional[str] = None
            if schema.name:  # If the inline enum has a name, it will be generated as a named enum class
                enum_name = NameSanitizer.sanitize_class_name(schema.name)
                module_name = NameSanitizer.sanitize_module_name(schema.name)
                model_module_path = f"{self.context.get_current_package_name_for_generated_code()}.models.{module_name}"
                self.context.add_import(logical_module=model_module_path, name=enum_name)
                logger.debug(
                    f"[NamedTypeResolver] INLINE NAMED ENUM '{schema.name}'. Returning its name: '{enum_name}'. Import from: '{model_module_path}'."
                )
                return enum_name
            else:  # Inline anonymous enum, falls back to primitive type of its values
                # (Handled by PrimitiveTypeResolver if this returns None or specific primitive)
                # For now, this path might lead to PrimitiveTypeResolver via TypeHelper's main loop.
                # Let's try to return the primitive type directly if possible.
                primitive_type_of_enum = "str"  # Default for enums if type not specified
                if schema.type == "integer":
                    primitive_type_of_enum = "int"
                elif schema.type == "number":
                    primitive_type_of_enum = "float"
                # other types for enums are unusual.
                logger.debug(
                    f"[NamedTypeResolver] INLINE ANONYMOUS ENUM. Values suggest type '{primitive_type_of_enum}'. Returning this primitive type."
                )
                return primitive_type_of_enum
        else:
            # Not a reference to a known schema, and not an inline enum.
            # This could be an anonymous complex type, or an unresolved reference.
            # Defer to other resolvers by returning None.
            logger.debug(
                f"[NamedTypeResolver] Schema '{schema.name or 'anonymous'}' is not a known ref and not an inline enum. Returning None to defer."
            )
            return None
