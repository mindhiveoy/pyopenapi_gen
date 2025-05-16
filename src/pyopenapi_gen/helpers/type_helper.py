"""Helper functions for determining Python types and managing related imports from IRSchema."""

import logging
from typing import Dict, List

from .. import IRSchema
from ..context.render_context import RenderContext
from ..core.utils import NameSanitizer
from .type_cleaner import TypeCleaner

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
        logger.debug(
            f"[_get_named_or_enum_type ID:{id(schema)}] Entry: schema.name='{schema.name}', type='{schema.type}', schema.name in schemas: {schema.name in schemas if schema.name else False}"
        )

        if schema.name and schema.name in schemas:  # Named schema reference found in registry
            ref_schema = schemas[schema.name]
            logger.debug(
                f"[_get_named_or_enum_type] Found '{ref_schema.name}' (type: {ref_schema.type}, any_of: {bool(ref_schema.any_of)}) in schemas dict for input schema '{schema.name}'."
            )

            is_simple_alias_target_type = ref_schema.type in ("array", "string", "integer", "number", "boolean")
            is_just_an_alias_structure = (
                not ref_schema.properties
                and not ref_schema.enum
                and not ref_schema.any_of
                and not ref_schema.one_of
                and not ref_schema.all_of
            )
            logger.debug(
                f"[_get_named_or_enum_type] '{ref_schema.name}': is_simple_alias_target_type={is_simple_alias_target_type}, is_just_an_alias_structure={is_just_an_alias_structure}"
            )

            if is_simple_alias_target_type and is_just_an_alias_structure:
                # It's a simple alias (e.g. MyStrings = List[str] or UserID = str).
                # Return None here so that _get_array_type or _get_primitive_type handles it
                # in the main get_python_type_for_schema function to get the underlying type.
                # The ModelVisitor will handle the TypeAlias generation based on the schema name.
                logger.debug(
                    f"[TypeHelper._get_named_or_enum_type] Schema '{ref_schema.name}' is a simple alias to '{ref_schema.type}'. Returning None for further processing."
                )
                return None

            # Otherwise, it's a named model (object), enum, or a named composite type alias (like a Union from anyOf)
            # that will have its own .py file. So, we need to import it.
            assert ref_schema.name is not None  # Assure linter that ref_schema.name is str
            class_name_to_import = NameSanitizer.sanitize_class_name(ref_schema.name)
            module_name_to_import_from = NameSanitizer.sanitize_module_name(ref_schema.name)

            # Correct module path construction relative to `models` directory
            model_module_path_within_package = f"models.{module_name_to_import_from}"

            logger.warning(
                f"[_get_named_or_enum_type ID:{id(ref_schema)}] REF: '{ref_schema.name}'. Adding import: "
                f"module='{model_module_path_within_package}', name='{class_name_to_import}' (from schema '{schema.name}')"
            )
            context.add_import(model_module_path_within_package, class_name_to_import)
            logger.debug(
                f"[_get_named_or_enum_type ID:{id(ref_schema)}] RETURNING '{class_name_to_import}' for '{ref_schema.name}'"
            )
            return class_name_to_import  # Return the sanitized class name for the type hint

        # Handle case where schema has a name and enum but might not be in schemas dict
        # (e.g., inline enum definition with a name hint by the parser?)
        # This primarily covers enums that might be defined inline but have a name.
        if schema.enum and schema.name:  # Named inline enum
            assert schema.name is not None  # Assure linter that schema.name is str
            class_name = NameSanitizer.sanitize_class_name(schema.name)
            # Assume it will be in its own file under models if it's a named enum
            model_module = f"models.{NameSanitizer.sanitize_module_name(schema.name)}"
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
            # Always add Optional import if the type is optional
            context.add_import("typing", "Optional")
            
            # Handle different cases
            if py_type == "Any":
                return "Optional[Any]"
            elif py_type.startswith("Union["):
                # If it's not already an Optional, wrap it
                if not py_type.startswith("Optional["):
                    # Don't add None to Union if it already has None
                    if ", None]" in py_type:
                        return py_type
                    # If the schema itself is nullable, prefer Optional[Union[...]] form
                    if schema.is_nullable:
                        return f"Optional[{py_type}]"
                    # Otherwise add None to the Union
                    else:
                        return py_type.replace("]", ", None]")
            elif not py_type.startswith("Optional["):
                return f"Optional[{py_type}]"
        
        return py_type

    @staticmethod
    def _clean_type_parameters(type_str: str) -> str:
        """
        Clean type parameters by removing incorrect None parameters from Dict, List, and Optional.
        For example:
        - Dict[str, Any, None] -> Dict[str, Any]
        - List[JsonValue, None] -> List[JsonValue]
        - Optional[Any, None] -> Optional[Any]
        - Complex nested types are handled recursively
        
        Args:
            type_str: The type string to clean
            
        Returns:
            A cleaned type string
        """
        # Delegate to the specialized TypeCleaner class
        return TypeCleaner.clean_type_parameters(type_str)

    @staticmethod
    def get_python_type_for_schema(
        schema: IRSchema,
        schemas: Dict[str, IRSchema],
        context: RenderContext,
        required: bool = True,
    ) -> str:
        logger.debug(
            f"[get_python_type_for_schema ID:{id(schema)}] Entry: schema.name='{schema.name}', type='{schema.type}', any_of_present={bool(schema.any_of)}, required={required}"
        )

        py_type: str | None = None

        # 1. Handle composition types first
        if not py_type:
            py_type = TypeHelper._get_composition_type(schema, schemas, context)

        # 2. Handle named schemas (models or enums) or primitive aliases if schema.name exists
        #    This is for when `schema` itself is a definition from the main `schemas` dict.
        if not py_type and schema.name:
            py_type = TypeHelper._get_named_or_enum_type(schema, schemas, context)

        # NEW STEP 2.5: Handle cases where schema.type is a string that refers to a named schema
        # This is for properties whose IRSchema node has its `type` field set to a custom model name.
        if (
            not py_type
            and isinstance(schema.type, str)
            and schema.type
            not in {
                "string",
                "integer",
                "number",
                "boolean",
                "object",
                "array",
            }
        ):
            # schema.type is something like "MyCustomModelName".
            referenced_schema_name_from_type_field = schema.type
            class_name_candidate = NameSanitizer.sanitize_class_name(referenced_schema_name_from_type_field)

            # MODIFIED: Only treat as a reference if the candidate name is a key in the `schemas` dict
            if class_name_candidate in schemas:  # Check if this type name exists as a defined schema
                # It's a known model/enum defined elsewhere. Generate import for it.
                module_name_part = NameSanitizer.sanitize_module_name(class_name_candidate)
                model_module_path_within_package = f"models.{module_name_part}"
                context.add_import(model_module_path_within_package, class_name_candidate)
                py_type = class_name_candidate  # Assign py_type only if it's a known schema
                logger.debug(
                    f"[TypeHelper] Resolved type '{schema.type}' to known schema '{class_name_candidate}' from models."
                )
            # If class_name_candidate is NOT in schemas, do nothing here.
            # py_type remains None, and it will fall through to primitive/array/object checks or to Any.
            # Removed the 'else' block that previously added a speculative import.

        # 3. Handle primitive types (if schema.type is "string", "integer", etc., and not yet resolved)
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

        # 6.5 Clean any incorrect type parameters (Dict[key, val, None], List[item, None])
        if py_type:
            py_type = TypeHelper._clean_type_parameters(py_type)

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
