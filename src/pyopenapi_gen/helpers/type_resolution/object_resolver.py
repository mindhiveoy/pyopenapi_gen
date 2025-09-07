"""Resolves IRSchema to Python object types (classes, dicts)."""

import logging
import os
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
        if not proposed_name_base:
            return None

        class_name_base = NameSanitizer.sanitize_class_name(proposed_name_base)
        # Suffix logic can be refined here if needed (e.g. Property vs Item)
        potential_new_name = f"{class_name_base}Item"
        counter = 1
        final_new_name = potential_new_name
        while final_new_name in self.all_schemas:
            final_new_name = f"{potential_new_name}{counter}"
            counter += 1
            if counter > 10:  # Safety break
                logger.error(
                    f"[ObjectTypeResolver._promote] Could not find unique name "
                    f"for base '{potential_new_name}' after 10 tries."
                )
                return None

        schema_to_promote.name = final_new_name  # Assign the new name
        # Set generation_name and final_module_stem after the new name is assigned
        schema_to_promote.generation_name = NameSanitizer.sanitize_class_name(final_new_name)
        schema_to_promote.final_module_stem = NameSanitizer.sanitize_module_name(final_new_name)

        self.all_schemas[final_new_name] = schema_to_promote  # Register in global schemas

        # Add import for this newly named model
        module_to_import_from = f"models.{NameSanitizer.sanitize_module_name(final_new_name)}"
        self.context.add_import(module_to_import_from, final_new_name)
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
                    self.context.add_import("typing", "Dict")
                    return f"Dict[str, {additional_prop_type}]"

            # Path C: additionalProperties is False, None, or empty IRSchema.
            if schema.properties:  # Object has its own properties
                if not schema.name:  # Anonymous object with properties
                    if parent_schema_name_for_anon_promotion:
                        promoted_name = self._promote_anonymous_object_schema_if_needed(
                            schema, parent_schema_name_for_anon_promotion
                        )
                        if promoted_name:
                            return promoted_name
                    # Fallback for unpromoted anonymous object with properties
                    logger.warning(
                        f"[ObjectTypeResolver] Anonymous object with properties not promoted. "
                        f"-> Dict[str, Any]. Schema: {schema}"
                    )
                    self.context.add_import("typing", "Dict")
                    self.context.add_import("typing", "Any")
                    return "Dict[str, Any]"
                else:  # Named object with properties
                    # If this named object is a component schema, ensure it's imported.
                    if schema.name and schema.name in self.all_schemas:
                        actual_schema_def = self.all_schemas[schema.name]
                        if actual_schema_def.generation_name is None:
                            raise RuntimeError(
                                f"Actual schema '{actual_schema_def.name}' for '{schema.name}' must have generation_name."
                            )
                        if actual_schema_def.final_module_stem is None:
                            raise RuntimeError(
                                f"Actual schema '{actual_schema_def.name}' for '{schema.name}' must have final_module_stem."
                            )

                        class_name_to_use = actual_schema_def.generation_name
                        module_stem_to_use = actual_schema_def.final_module_stem

                        base_model_path_part = f"models.{module_stem_to_use}"
                        model_module_path = base_model_path_part

                        if self.context.package_root_for_generated_code and self.context.overall_project_root:
                            abs_pkg_root = os.path.abspath(self.context.package_root_for_generated_code)
                            abs_overall_root = os.path.abspath(self.context.overall_project_root)
                            if abs_pkg_root.startswith(abs_overall_root) and abs_pkg_root != abs_overall_root:
                                rel_pkg_path = os.path.relpath(abs_pkg_root, abs_overall_root)
                                current_gen_pkg_dot_path = rel_pkg_path.replace(os.sep, ".")
                                model_module_path = f"{current_gen_pkg_dot_path}.{base_model_path_part}"
                            elif abs_pkg_root == abs_overall_root:
                                model_module_path = base_model_path_part
                        elif self.context.package_root_for_generated_code:
                            current_gen_pkg_name_from_basename = os.path.basename(
                                os.path.normpath(self.context.package_root_for_generated_code)
                            )
                            if current_gen_pkg_name_from_basename and current_gen_pkg_name_from_basename != ".":
                                model_module_path = f"{current_gen_pkg_name_from_basename}.{base_model_path_part}"

                        current_module_dot_path = self.context.get_current_module_dot_path()
                        if model_module_path != current_module_dot_path:  # Avoid self-imports
                            self.context.add_import(model_module_path, class_name_to_use)
                        return class_name_to_use  # Return the potentially de-collided name
                    else:
                        # This case should ideally not be hit if all named objects are in all_schemas
                        # Or, it's a named object that isn't a global component (e.g. inline named object for promotion)
                        # For safety, use schema.name if it's not in all_schemas (might be a freshly promoted name)
                        class_name_to_use = NameSanitizer.sanitize_class_name(schema.name)
                        logger.warning(
                            f"[ObjectTypeResolver] Named object '{schema.name}' not in all_schemas, "
                            f"using its own name '{class_name_to_use}'. "
                            f"This might occur for locally promoted anonymous objects."
                        )
                        return class_name_to_use
            else:  # Object has NO properties
                if (
                    schema.name and schema.name in self.all_schemas
                ):  # Named object, no properties, AND it's a known component
                    actual_schema_def = self.all_schemas[schema.name]
                    if actual_schema_def.generation_name is None:
                        raise RuntimeError(
                            f"Actual schema (no props) '{actual_schema_def.name}' "
                            f"for '{schema.name}' must have generation_name."
                        )
                    if actual_schema_def.final_module_stem is None:
                        raise RuntimeError(
                            f"Actual schema (no props) '{actual_schema_def.name}' "
                            f"for '{schema.name}' must have final_module_stem."
                        )

                    class_name_to_use = actual_schema_def.generation_name
                    module_stem_to_use = actual_schema_def.final_module_stem

                    base_model_path_part = f"models.{module_stem_to_use}"
                    model_module_path = base_model_path_part

                    if self.context.package_root_for_generated_code and self.context.overall_project_root:
                        abs_pkg_root = os.path.abspath(self.context.package_root_for_generated_code)
                        abs_overall_root = os.path.abspath(self.context.overall_project_root)
                        if abs_pkg_root.startswith(abs_overall_root) and abs_pkg_root != abs_overall_root:
                            rel_pkg_path = os.path.relpath(abs_pkg_root, abs_overall_root)
                            current_gen_pkg_dot_path = rel_pkg_path.replace(os.sep, ".")
                            model_module_path = f"{current_gen_pkg_dot_path}.{base_model_path_part}"
                        elif abs_pkg_root == abs_overall_root:
                            model_module_path = base_model_path_part
                    elif self.context.package_root_for_generated_code:
                        current_gen_pkg_name_from_basename = os.path.basename(
                            os.path.normpath(self.context.package_root_for_generated_code)
                        )
                        if current_gen_pkg_name_from_basename and current_gen_pkg_name_from_basename != ".":
                            model_module_path = f"{current_gen_pkg_name_from_basename}.{base_model_path_part}"

                    current_module_dot_path = self.context.get_current_module_dot_path()
                    if model_module_path != current_module_dot_path:  # Avoid self-imports
                        self.context.add_import(model_module_path, class_name_to_use)
                    return class_name_to_use  # Return the potentially de-collided name
                elif schema.name:  # Named object, no properties, but NOT a known component
                    self.context.add_import("typing", "Dict")
                    self.context.add_import("typing", "Any")
                    return "Dict[str, Any]"
                else:  # Anonymous object, no properties
                    if schema.additional_properties is None:  # Default OpenAPI behavior allows additional props
                        self.context.add_import("typing", "Dict")
                        self.context.add_import("typing", "Any")
                        return "Dict[str, Any]"
                    else:  # additionalProperties was False or restrictive empty schema
                        self.context.add_import("typing", "Any")
                        return "Any"
        return None
