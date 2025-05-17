"""Resolves IRSchema to Python object types (classes, dicts)."""

import logging
from typing import TYPE_CHECKING, Dict, Optional

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer

if TYPE_CHECKING:
    from .resolver import SchemaTypeResolver  # Avoid circular import

logger = logging.getLogger(__name__)


class ObjectTypeResolver:
    """Resolves IRSchema instances of type 'object'."""

    def __init__(self, context: RenderContext, all_schemas: Dict[str, IRSchema], main_resolver: "SchemaTypeResolver"):
        self.context = context
        self.all_schemas = all_schemas
        self.main_resolver = main_resolver  # For resolving nested types

    def _promote_anonymous_object_schema_if_needed(
        self,
        schema_to_promote: IRSchema,
        proposed_name_base: Optional[str],
    ) -> Optional[str]:
        """Gives a name to an anonymous object schema and registers it."""
        logger.debug(
            f"[ObjectTypeResolver._promote] Entry. schema_desc='{schema_to_promote.description or 'anonymous'}', proposed_name_base='{proposed_name_base}'"
        )
        if not proposed_name_base:
            logger.debug("[ObjectTypeResolver._promote] proposed_name_base is None, cannot promote.")
            return None

        class_name_base = NameSanitizer.sanitize_class_name(proposed_name_base)
        # Suffix logic can be refined here if needed (e.g. Property vs Item)
        potential_new_name = f"{class_name_base}Item"
        counter = 1
        final_new_name = potential_new_name
        while final_new_name in self.all_schemas:
            logger.debug(f"[ObjectTypeResolver._promote] Name '{final_new_name}' collides. Trying next suffix.")
            final_new_name = f"{potential_new_name}{counter}"
            counter += 1
            if counter > 10:  # Safety break
                logger.error(
                    f"[ObjectTypeResolver._promote] Could not find unique name for base '{potential_new_name}' after 10 tries."
                )
                return None

        logger.info(
            f"[ObjectTypeResolver._promote] Promoting anonymous object (desc: '{schema_to_promote.description or 'anonymous'}') to '{final_new_name}' based on '{proposed_name_base}'."
        )
        schema_to_promote.name = final_new_name  # Assign the new name
        self.all_schemas[final_new_name] = schema_to_promote  # Register in global schemas

        # Add import for this newly named model
        module_to_import_from = f"models.{NameSanitizer.sanitize_module_name(final_new_name)}"
        self.context.add_import(module_to_import_from, final_new_name)
        logger.debug(f"[ObjectTypeResolver._promote] Promoted and registered as '{final_new_name}'.")
        return final_new_name

    def resolve(self, schema: IRSchema, parent_schema_name_for_anon_promotion: Optional[str] = None) -> Optional[str]:
        """
        Resolves an IRSchema of `type: "object"`.
        Args:
            schema: The IRSchema, expected to have `type: "object"`.
            parent_schema_name_for_anon_promotion: Contextual name for promoting anonymous objects.
        Returns:
            A Python type string or None.
        """
        if schema.type == "object":
            # Path A: additionalProperties is True (boolean)
            if isinstance(schema.additional_properties, bool) and schema.additional_properties:
                logger.debug(
                    f"[ObjectTypeResolver] Schema '{schema.name or 'ANONYMOUS'}' has additionalProperties: true. -> Dict[str, Any]"
                )
                self.context.add_import("typing", "Dict")
                self.context.add_import("typing", "Any")
                return "Dict[str, Any]"

            # Path B: additionalProperties is an IRSchema instance
            if isinstance(schema.additional_properties, IRSchema):
                ap_schema_instance = schema.additional_properties
                is_ap_schema_defined = (
                    ap_schema_instance.type is not None
                    or ap_schema_instance.format is not None
                    or ap_schema_instance.properties
                    or ap_schema_instance.items
                    or ap_schema_instance.enum
                    or ap_schema_instance.any_of
                    or ap_schema_instance.one_of
                    or ap_schema_instance.all_of
                )
                if is_ap_schema_defined:
                    additional_prop_type = self.main_resolver.resolve(ap_schema_instance, required=True)
                    logger.debug(
                        f"[ObjectTypeResolver] Schema '{schema.name or 'ANONYMOUS'}' has defined additionalProperties. Value type: '{additional_prop_type}'. -> Dict[str, {additional_prop_type}]"
                    )
                    self.context.add_import("typing", "Dict")
                    return f"Dict[str, {additional_prop_type}]"
                logger.debug(
                    f"[ObjectTypeResolver] Schema '{schema.name or 'ANONYMOUS'}' additionalProperties IRSchema is effectively empty. Falling through."
                )

            # Path C: additionalProperties is False, None, or empty IRSchema.
            if schema.properties:  # Object has its own properties
                if not schema.name:  # Anonymous object with properties
                    logger.debug(
                        f"[ObjectTypeResolver] Anonymous object with props. Parent context for promotion: '{parent_schema_name_for_anon_promotion}'."
                    )
                    if parent_schema_name_for_anon_promotion:
                        promoted_name = self._promote_anonymous_object_schema_if_needed(
                            schema, parent_schema_name_for_anon_promotion
                        )
                        if promoted_name:
                            return promoted_name
                    # Fallback for unpromoted anonymous object with properties
                    logger.warning(
                        f"[ObjectTypeResolver] Anonymous object with properties not promoted. -> Dict[str, Any]. Schema: {schema}"
                    )
                    self.context.add_import("typing", "Dict")
                    self.context.add_import("typing", "Any")
                    return "Dict[str, Any]"
                else:  # Named object with properties
                    logger.debug(
                        f"[ObjectTypeResolver] Named object '{schema.name}' with properties. -> {NameSanitizer.sanitize_class_name(schema.name)}"
                    )
                    # The NamedTypeResolver would have handled the import if this was a direct reference.
                    # Here, we just return the name as it's structurally an object with properties.
                    return NameSanitizer.sanitize_class_name(schema.name)
            else:  # Object has NO properties
                if schema.name:  # Named object, no properties
                    logger.debug(
                        f"[ObjectTypeResolver] Named object '{schema.name}' with NO properties. -> {NameSanitizer.sanitize_class_name(schema.name)}"
                    )
                    return NameSanitizer.sanitize_class_name(schema.name)
                else:  # Anonymous object, no properties
                    if schema.additional_properties is None:  # Default OpenAPI behavior allows additional props
                        logger.debug(
                            "[ObjectTypeResolver] Anonymous object, no props, additionalProperties is None. -> Dict[str, Any]"
                        )
                        self.context.add_import("typing", "Dict")
                        self.context.add_import("typing", "Any")
                        return "Dict[str, Any]"
                    else:  # additionalProperties was False or restrictive empty schema
                        logger.debug(
                            "[ObjectTypeResolver] Anonymous object, no props, restrictive additionalProperties. -> Any"
                        )
                        self.context.add_import("typing", "Any")
                        return "Any"
        return None
