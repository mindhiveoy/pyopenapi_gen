"""Helper functions for determining Python types and managing related imports from IRSchema."""

import logging
from typing import Dict, List

from .. import IRSchema
from ..context.render_context import RenderContext
from ..core.utils import NameSanitizer

# Get logger
logger = logging.getLogger(__name__)


class TypeHelper:
    @staticmethod
    def _get_composition_type(schema: IRSchema, schemas: Dict[str, IRSchema], context: RenderContext) -> str | None:
        """Handles 'anyOf', 'oneOf', 'allOf' composition types."""
        union_types: List[str] = []
        if schema.any_of:
            union_types.extend(
                TypeHelper.get_python_type_for_schema(sub, schemas, context, required=True) for sub in schema.any_of
            )
        if schema.one_of:
            union_types.extend(
                TypeHelper.get_python_type_for_schema(sub, schemas, context, required=True) for sub in schema.one_of
            )
        if schema.all_of:  # allOf typically results in merged properties, not a Union, but current logic forms a Union.
            # This simplification is kept from the original logic for now.
            union_types.extend(
                TypeHelper.get_python_type_for_schema(sub, schemas, context, required=True) for sub in schema.all_of
            )

        if not union_types:
            return None

        unique_types = sorted(list(set(union_types)))
        if len(unique_types) > 1:
            unique_types = [t for t in unique_types if t != "Any"]

        if not unique_types:  # e.g. if only [Any] was there and removed
            return "Any"  # Fallback if filtering 'Any' leaves an empty list

        if len(unique_types) == 1:
            return unique_types[0]

        context.add_import("typing", "Union")
        return f"Union[{', '.join(unique_types)}]"

    @staticmethod
    def _get_primitive_type(schema: IRSchema, context: RenderContext) -> str | None:
        """Handles primitive types including formats like date and date-time."""
        primitive_type_map = {
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "string": "str",
        }
        if schema.type == "string" and schema.format == "date-time":
            logger.debug(
                f"[TypeHelper._get_primitive_type] Matched date-time for schema: {schema.name or 'anonymous'}. Adding specific import."
            )
            context.add_import("datetime", "datetime")
            return "datetime"
        if schema.type == "string" and schema.format == "date":
            logger.debug(
                f"[TypeHelper._get_primitive_type] Matched date for schema: {schema.name or 'anonymous'}. Adding specific import."
            )
            context.add_import("datetime", "date")
            return "date"
        if schema.type == "string" and schema.format == "binary":
            return "bytes"
        if schema.type in primitive_type_map:
            return primitive_type_map[schema.type]
        return None

    @staticmethod
    def _get_named_or_enum_type(schema: IRSchema, schemas: Dict[str, IRSchema], context: RenderContext) -> str | None:
        """Handles named schema references (models, enums) or inline enums if named."""
        if schema.name and schema.name in schemas:  # Named schema reference found in registry
            ref_schema = schemas[schema.name]

            # Check if the referenced schema is actually an alias for array/primitive
            is_complex_override = ref_schema.properties or ref_schema.enum
            if ref_schema.type in ("array", "string", "integer", "number", "boolean") and not is_complex_override:
                # It's a simple alias (e.g. MyStrings = List[str]).
                # Return None here so that _get_array_type or _get_primitive_type handles it
                # in the main get_python_type_for_schema function to get the underlying type.
                # The ModelVisitor will handle the TypeAlias generation based on the schema name.
                return None

            # If it wasn't identified as a simple alias above, treat it as a reference
            # to a complex object model or a named enum.
            # This path should primarily catch object types or enums.
            if ref_schema.type == "object" or ref_schema.enum:
                if not ref_schema.name:  # Should not happen if schema.name was present
                    return None

                ref_schema_module_name = NameSanitizer.sanitize_module_name(ref_schema.name)

                # This is the module path relative to the root of the generated package (context.package_root_for_generated_code).
                # e.g., if package_root_for_generated_code is "client/", and model is "MyModel" (in "my_model.py"),
                # this will be "models.my_model".
                # RenderContext.add_import will then try to convert this to e.g., "..models.my_model"
                # if the current file is in "client/endpoints/".
                model_module_path_within_package = f"models.{ref_schema_module_name}"

                logger.debug(
                    f"[TypeHelper] Adding model import: module_within_package='{model_module_path_within_package}', "
                    f"name='{ref_schema.name}' for schema {schema.name} referencing {ref_schema.name}. "
                    f"Context details: current_file={context.current_file}, "
                    f"pkg_root_for_gen_code={context.package_root_for_generated_code}, "
                    f"overall_proj_root={context.overall_project_root}, "
                    f"core_pkg_name={context.core_package_name}"
                )
                context.add_import(model_module_path_within_package, ref_schema.name)
                return f"{ref_schema.name}"  # Correctly returns just the class name
            # If schema.name was in schemas but wasn't alias or object/enum, what is it?
            # Log a warning and fall through (will likely become Any)
            logger.warning(
                f"Named schema '{schema.name}' found but type '{ref_schema.type}' wasn't object/enum or simple alias."
            )

        # Handle case where schema has a name and enum but might not be in schemas dict
        # (e.g., inline enum definition with a name hint?)
        if schema.enum and schema.name:  # Named inline enum
            class_name = NameSanitizer.sanitize_class_name(schema.name)
            model_module = f"models.{NameSanitizer.sanitize_module_name(schema.name)}"
            # Add import defensively, might be duplicate if handled above but collector handles that
            context.add_import(model_module, class_name)
            return class_name

        # Unnamed enum is handled by ModelVisitor if needed, type helper returns base type
        if schema.enum and not schema.name:
            if schema.type == "integer":
                return "int"
            return "str"  # Default for enums if type not specified or string

        return None

    @staticmethod
    def _get_array_type(schema: IRSchema, schemas: Dict[str, IRSchema], context: RenderContext) -> str | None:
        """Handles array types."""
        if schema.type == "array" and schema.items:
            item_type = TypeHelper.get_python_type_for_schema(schema.items, schemas, context, required=True)
            context.add_import("typing", "List")
            return f"List[{item_type}]"
        return None

    @staticmethod
    def _get_object_type(schema: IRSchema, schemas: Dict[str, IRSchema], context: RenderContext) -> str | None:
        """Handles object types, including additionalProperties and anonymous objects."""
        if schema.type == "object":
            if schema.additional_properties is True or isinstance(schema.additional_properties, IRSchema):
                # If additionalProperties is an IRSchema, we might be more specific than Dict[str, Any]
                # For now, keeping it simple as Dict[str, Any]
                context.add_import("typing", "Dict")
                context.add_import("typing", "Any")
                return "Dict[str, Any]"
            if schema.properties:  # If it has properties but no specific additionalProperties behavior
                # and is unnamed (otherwise _get_named_or_enum_type would catch it),
                # it's an inline anonymous object.
                if not schema.name:  # Ensure it's an anonymous object
                    context.add_import("typing", "Dict")
                    context.add_import("typing", "Any")
                    return "Dict[str, Any]"  # Fallback for anonymous objects with properties
                # If it has a name, _get_named_or_enum_type should have handled it.
                # This path for named objects with properties should ideally not be hit frequently.
                # It might indicate a named object that wasn't found in `schemas`.
                class_name = NameSanitizer.sanitize_class_name(schema.name)  # Recalculate if somehow missed
                model_module = f"models.{NameSanitizer.sanitize_module_name(schema.name)}"
                context.add_import(model_module, class_name)
                return class_name

            # No properties, no specific additionalProperties -> Treat as Any
            context.add_import("typing", "Any")
            return "Any"
        return None

    @staticmethod
    def _finalize_type_with_optional(py_type: str, schema: IRSchema, required: bool, context: RenderContext) -> str:
        """Wraps the type with Optional if needed."""
        is_optional = not required or schema.is_nullable
        if is_optional:
            # Always add Optional import if the type is optional, even if rendered as Union[..., None]
            context.add_import("typing", "Optional")
            if py_type == "Any":
                # context.add_import("typing", "Optional") # Already added above
                return "Optional[Any]"
            if py_type.startswith("Union["):
                if "None" not in py_type and not py_type.startswith("Optional[Union["):
                    # Still render as Union[..., None] for clarity, but ensure Optional is imported.
                    return py_type.replace("]", ", None]")
            elif not py_type.startswith("Optional["):
                # context.add_import("typing", "Optional") # Already added above
                return f"Optional[{py_type}]"
        return py_type

    @staticmethod
    def get_python_type_for_schema(
        schema: IRSchema,
        schemas: Dict[str, IRSchema],
        context: RenderContext,
        required: bool = True,
    ) -> str:
        py_type: str | None = None

        # 1. Handle composition types first
        if not py_type:
            py_type = TypeHelper._get_composition_type(schema, schemas, context)

        # 2. Handle named schemas (models or enums) or primitive aliases if name exists
        if not py_type and schema.name:
            py_type = TypeHelper._get_named_or_enum_type(schema, schemas, context)

        # 3. Handle primitive types if not already resolved by name (e.g. unnamed primitive schema)
        if not py_type:
            py_type = TypeHelper._get_primitive_type(schema, context)

        # 4. Handle array types
        if not py_type:
            py_type = TypeHelper._get_array_type(schema, schemas, context)

        # 5. Handle object types (especially anonymous or those not caught as named schemas)
        if not py_type:
            py_type = TypeHelper._get_object_type(schema, schemas, context)

        # 6. Fallback to "Any" if no type could be determined
        if not py_type:
            logger.warning(f"Type could not be determined for schema: {schema}. Defaulting to Any.")
            py_type = "Any"
            context.add_import("typing", "Any")

        # 7. Apply Optional wrapping
        final_py_type = TypeHelper._finalize_type_with_optional(py_type, schema, required, context)

        # 8. Ensure all components of the final type string are registered for import
        context.add_typing_imports_for_type(final_py_type)

        # 9. Explicitly ensure datetime/date imports if they appear in the final type string
        #    This is a safeguard if the primitive type detection for format didn't trigger
        #    the specific import, but the type string still resolved to 'datetime' or 'date'.
        if (
            final_py_type == "datetime"
            or final_py_type.startswith("Optional[datetime]")
            or ("Union[" in final_py_type and "datetime" in final_py_type and "datetime." not in final_py_type)
        ):
            logger.debug(
                f"[TypeHelper] Safeguard: Ensuring 'from datetime import datetime' for final type: {final_py_type}"
            )
            context.add_import("datetime", "datetime")
        elif (
            final_py_type == "date"
            or final_py_type.startswith("Optional[date]")
            or ("Union[" in final_py_type and "date" in final_py_type and "datetime." not in final_py_type)
        ):  # avoid matching datetime.date as date
            logger.debug(
                f"[TypeHelper] Safeguard: Ensuring 'from datetime import date' for final type: {final_py_type}"
            )
            context.add_import("datetime", "date")

        return final_py_type
