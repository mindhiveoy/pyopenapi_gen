"""Resolves IRSchema to Python named types (classes, enums)."""

import logging
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

    def resolve(self, schema: IRSchema) -> Optional[str]:
        """
        Resolves an IRSchema that refers to a named model/enum, or an inline named enum.

        Args:
            schema: The IRSchema to resolve.

        Returns:
            A Python type string (class name) if a named type or enum is resolved, otherwise None.
        """
        logger.debug(
            f"[NamedTypeResolver ID:{id(schema)}] Entry: schema.name='{schema.name}', type='{schema.type}', schema.name in all_schemas: {schema.name in self.all_schemas if schema.name else False}"
        )

        if schema.name and schema.name in self.all_schemas:  # Named schema reference
            ref_schema = self.all_schemas[schema.name]
            logger.debug(
                f"[NamedTypeResolver] Found '{ref_schema.name}' (type: {ref_schema.type}, any_of: {bool(ref_schema.any_of)}) in all_schemas for input schema '{schema.name}'."
            )

            # Determine if it's a simple alias that should defer to structural resolution
            is_structurally_alias_like = not (
                ref_schema.properties or ref_schema.enum or ref_schema.any_of or ref_schema.one_of or ref_schema.all_of
            )

            if is_structurally_alias_like:
                if ref_schema.type in ("array", "string", "integer", "number", "boolean"):
                    logger.debug(
                        f"[NamedTypeResolver] Schema '{ref_schema.name}' is simple alias to known base type '{ref_schema.type}'. Returning None for structural processing."
                    )
                    return None  # Defer to main resolver for underlying type
                elif ref_schema.type == "object":
                    logger.debug(
                        f"[NamedTypeResolver] Schema '{ref_schema.name}' is structurally simple 'object'. Will be imported as class."
                    )
                    # Fall through to import logic for the class name
                else:
                    logger.debug(
                        f"[NamedTypeResolver] Schema '{ref_schema.name}' is simple alias to UNKNOWN base type '{ref_schema.type}'. Returning None for Any fallback."
                    )
                    return None  # Fallback to Any for unknown types

            # If complex or a simple 'object' type, import it as a class
            assert ref_schema.name is not None
            class_name_to_import = NameSanitizer.sanitize_class_name(ref_schema.name)
            module_name_to_import_from = NameSanitizer.sanitize_module_name(ref_schema.name)
            model_module_path = f"models.{module_name_to_import_from}"

            logger.debug(
                f"[NamedTypeResolver ID:{id(ref_schema)}] Importing: module='{model_module_path}', name='{class_name_to_import}' (from schema '{schema.name}')"
            )
            self.context.add_import(model_module_path, class_name_to_import)
            return class_name_to_import

        # Handle inline named enums (schema.name and schema.enum are present)
        if schema.enum and schema.name:
            assert schema.name is not None
            class_name = NameSanitizer.sanitize_class_name(schema.name)
            model_module = f"models.{NameSanitizer.sanitize_module_name(schema.name)}"
            self.context.add_import(model_module, class_name)
            logger.debug(f"[NamedTypeResolver] Resolved inline named enum '{schema.name}' to class '{class_name}'.")
            return class_name

        # Unnamed enum: return base type (string or int)
        if schema.enum and not schema.name:
            logger.debug(f"[NamedTypeResolver] Resolved unnamed enum to base type '{schema.type}'.")
            if schema.type == "integer":
                return "int"
            return "str"  # Default for enums if type not specified or string

        return None
