"""Helper functions for determining Python types and managing related imports from IRSchema."""

import logging
from typing import Dict, List, Optional

from .. import IRSchema
from ..context.render_context import RenderContext
from ..core.utils import NameSanitizer

# Get logger
logger = logging.getLogger(__name__)


def get_python_type_for_schema(
    schema: IRSchema,
    schemas: Dict[str, IRSchema],
    context: RenderContext,
    required: bool = True,
) -> str:
    """
    Determines the Python type hint string for a given IRSchema.

    Also registers necessary imports (typing, models, datetime) in the provided RenderContext
    as a side effect.

    Args:
        schema: The IRSchema node to analyze.
        schemas: The dictionary of all named schemas for resolving references.
        context: The RenderContext to register imports into.
        required: Flag indicating if the schema is required (affects Optional wrapping).

    Returns:
        The Python type hint string (e.g., "Optional[str]", "List[MyModel]").
    """
    py_type: str | None = None

    # --- Handle Composition --- (anyOf, oneOf, allOf)
    union_types: List[str] = []
    if schema.any_of:
        union_types.extend(get_python_type_for_schema(sub, schemas, context, required=True) for sub in schema.any_of)
    if schema.one_of:
        union_types.extend(get_python_type_for_schema(sub, schemas, context, required=True) for sub in schema.one_of)
    if schema.all_of:
        union_types.extend(get_python_type_for_schema(sub, schemas, context, required=True) for sub in schema.all_of)

    if union_types:
        # Remove duplicates and filter out Any if other types exist
        unique_types = sorted(list(set(union_types)))
        if len(unique_types) > 1:
            unique_types = [t for t in unique_types if t != "Any"]
        # Handle cases where composition resulted in a single type
        if len(unique_types) == 1:
            py_type = unique_types[0]
        else:
            py_type = f"Union[{', '.join(unique_types)}]"
            context.add_import("typing", "Union")

    # <<< Start Change: Only run subsequent checks if py_type wasn't set by composition >>>
    if py_type is None:
        # --- Handle Standard Types ---
        # <<< Change: Prioritize Primitives >>>
        primitive_type_map = {
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "string": "str",
        }
        if schema.type == "string" and schema.format == "date-time":
            py_type = "datetime"
            context.add_import("datetime", "datetime")
        elif schema.type == "string" and schema.format == "date":
            py_type = "date"
            context.add_import("datetime", "date")
        elif schema.type in primitive_type_map:
            py_type = primitive_type_map[schema.type]
        # <<< End Primitive Check >>>

        # --- If not primitive, check other types ---
        if py_type is None:
            if schema.name and schema.name in schemas:  # Named schema reference
                # Check if the referenced schema is just a primitive alias we already handled
                ref_schema = schemas[schema.name]
                if ref_schema.type in primitive_type_map and not ref_schema.properties and not ref_schema.enum:
                    py_type = primitive_type_map[ref_schema.type]
                else:
                    class_name = NameSanitizer.sanitize_class_name(schema.name)
                    model_module = f"models.{NameSanitizer.sanitize_module_name(schema.name)}"
                    context.add_import(model_module, class_name)
                    py_type = class_name
            elif schema.enum:  # Enum reference
                py_type = NameSanitizer.sanitize_class_name(schema.name) if schema.name else "str"
                if schema.name:
                    model_module = f"models.{NameSanitizer.sanitize_module_name(schema.name)}"
                    context.add_import(model_module, py_type)
            elif schema.type == "array" and schema.items:  # Array type
                item_type = get_python_type_for_schema(schema.items, schemas, context, required=True)
                py_type = f"List[{item_type}]"
                context.add_import("typing", "List")
            elif schema.type == "object":  # Object type
                # <<< Start Change: Handle additionalProperties using IRSchema field >>>
                if schema.additional_properties is True or isinstance(schema.additional_properties, IRSchema):
                    # If additionalProperties allows anything or has its own schema, treat as Dict
                    # TODO: Could refine to use schema of additionalProperties if available
                    py_type = "Dict[str, Any]"
                    context.add_import("typing", "Dict")
                    context.add_import("typing", "Any")
                elif schema.properties:
                    # If it has properties but no additionalProperties (or additionalProperties=False),
                    # it should be treated like a named model if it has a name, otherwise maybe Dict or Any?
                    # For now, let's assume if it reaches here without a name/ref, it's Dict
                    py_type = "Dict[str, Any]"
                    context.add_import("typing", "Dict")
                    context.add_import("typing", "Any")
                else:
                    # No properties, no additionalProperties -> Treat as Any
                    py_type = "Any"
                    context.add_import("typing", "Any")
                # <<< End Change >>>
            # Fallback / Unknown schema.type
            else:
                py_type = "Any"
                context.add_import("typing", "Any")
    # <<< End Change >>>

    # Ensure py_type is set (should always be by now)
    if py_type is None:
        logger.warning(f"Type could not be determined for schema: {schema}. Defaulting to Any.")
        py_type = "Any"
        context.add_import("typing", "Any")

    # --- Handle Nullability ---
    is_optional = not required or schema.is_nullable
    if is_optional and py_type != "Any":  # Don't wrap Any
        if py_type.startswith("Union["):
            if "None" not in py_type:
                py_type = py_type.replace("]", ", None]")
        else:
            py_type = f"Optional[{py_type}]"
            context.add_import("typing", "Optional")

    # Ensure all components of the final type string are registered for import
    context.add_typing_imports_for_type(py_type)

    return py_type
