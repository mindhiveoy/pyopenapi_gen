"""
ModelVisitor: Transforms IRSchema objects into Python model code (dataclasses and enums).

This module provides the ModelVisitor class that generates Python code for data models
defined in OpenAPI specifications, supporting type aliases, enums, and dataclasses.
"""

import logging
from typing import Dict, List, Optional, Tuple
import re
import keyword

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

from ..core.utils import Formatter, NameSanitizer
from ..core.writers.python_construct_renderer import PythonConstructRenderer
from ..helpers.type_helper import TypeHelper
from .visitor import Visitor

logger = logging.getLogger(__name__)


class ModelVisitor(Visitor[IRSchema, str]):
    """
    Visitor for rendering a Python model (dataclass or enum) from an IRSchema.

    This visitor analyzes an IRSchema and generates the appropriate Python construct:
    - Type aliases for primitive or array types with names
    - Enums for string or integer types with enum values
    - Dataclasses for object types with properties

    Returns the rendered code as a string (does not write files).
    Only adds imports/types to the context if they are actually used in the rendered code.
    """

    def __init__(self, schemas: Optional[Dict[str, IRSchema]] = None) -> None:
        """
        Initialize a new ModelVisitor.

        Args:
            schemas: Dictionary of all schemas for reference resolution
        """
        self.formatter = Formatter()
        self.schemas = schemas or {}
        self.renderer = PythonConstructRenderer()

    def clean_field_type(self, py_type: str) -> str:
        """
        Post-process type hints to fix common issues with complex types.
        
        Args:
            py_type: The Python type hint to clean
            
        Returns:
            A cleaned type hint
        """
        # Import before using to avoid circular import issues
        from ..helpers.type_helper import TypeHelper
        return TypeHelper._clean_type_parameters(py_type)

    def visit_IRSchema(self, schema: IRSchema, context: RenderContext) -> str:
        """
        Visit an IRSchema node and generate Python code for it.

        Args:
            schema: The schema to visit
            context: The rendering context for imports and configuration

        Returns:
            Formatted Python code for the model as a string
        """
        # Revised Alias, Enum, Dataclass Detection Logic

        # --- Enum Detection first ---
        # An enum must have a name and enum values, and be string/integer type.
        is_enum = bool(schema.name and schema.enum and schema.type in ("string", "integer"))

        # --- Type Alias Detection ---
        # A type alias must have a name, NOT have properties, NOT be an enum, AND NOT be of type "object".
        is_type_alias = bool(schema.name and not schema.properties and not is_enum and schema.type != "object")

        # --- Dataclass Detection ---
        # If it's not an enum and not a type alias, it's treated as a dataclass.
        is_dataclass = not is_enum and not is_type_alias

        # --- Basic Validation & Skipping ---
        if not schema.name and (is_type_alias or is_enum or is_dataclass):
            return ""
        assert schema.name is not None

        # --- Determine the base name to use for Python constructs ---
        # Reverting previous attempt to use schema.title as it does not exist on IRSchema.
        # We will use schema.name for now, acknowledging this doesn't solve the
        # underlying User/UserCreate naming issue yet.
        base_name_for_construct = schema.name
        logger.debug(f"Schema name: '{schema.name}'. Using '{base_name_for_construct}' for construct name.")

        # --- Import Registration (Delegated for constructs, handled here for types) ---
        self._analyze_and_register_imports(schema, context)

        # Mark this module as generated
        if context.current_file:
            context.mark_generated_module(context.current_file)

        # --- Code Generation Dispatch ---
        rendered_code = ""

        if is_type_alias:
            # Prepare data for alias renderer
            alias_name = NameSanitizer.sanitize_class_name(base_name_for_construct)
            target_type = TypeHelper.get_python_type_for_schema(schema, self.schemas, context, required=True)
            target_type = self.clean_field_type(target_type)
            rendered_code = self.renderer.render_alias(
                alias_name=alias_name,
                target_type=target_type,
                description=schema.description,
                context=context,
            )
        elif is_enum:
            # Prepare data for enum renderer
            enum_name = NameSanitizer.sanitize_class_name(base_name_for_construct)
            base_type = "str" if schema.type == "string" else "int"
            values: List[Tuple[str, str | int]] = []
            if schema.enum:
                for val in schema.enum:
                    if base_type == "str":
                        # Convert value to potential member name: uppercase, replace separators
                        base_member_name = str(val).upper().replace("-", "_").replace(" ", "_")
                        # Ensure it's a valid Python identifier (alphanumeric + underscore, not starting with digit)
                        sanitized_member_name = re.sub(r"[^A-Z0-9_]", "", base_member_name)
                        # Prefix with underscore if starts with digit or is empty, using a clear prefix
                        if not sanitized_member_name:
                            sanitized_member_name = f"MEMBER_EMPTY_STRING"
                        elif sanitized_member_name[0].isdigit():
                            sanitized_member_name = f"MEMBER_{sanitized_member_name}"
                        # Avoid keywords
                        if keyword.iskeyword(sanitized_member_name):
                            sanitized_member_name += "_"
                        member_name = sanitized_member_name
                        values.append((member_name, str(val)))
                    else:  # Integer enum values
                        try:
                            int_val = int(val)
                        except (ValueError, TypeError):
                            # Handle cases where enum value for integer type isn't easily convertible
                            # Maybe log a warning and skip or use a default name/value?
                            # For now, let's try to create a name from string repr and use 0 as value if cast fails
                            int_val = 0
                            logger.warning(
                                f"Could not convert enum value '{val}' to int for schema '{schema.name}'. Using value 0."
                            )

                        name_basis = str(val)  # Use string representation as basis for name
                        base_member_name = (
                            name_basis.upper().replace("-", "_").replace(" ", "_").replace(".", "_DOT_")
                        )  # Also handle dots maybe
                        sanitized_member_name = re.sub(r"[^A-Z0-9_]", "", base_member_name)
                        if not sanitized_member_name:
                            sanitized_member_name = f"MEMBER_UNKNOWN_{str(val).replace('[^a-zA-Z0-9]', '_')}"
                        elif sanitized_member_name[0].isdigit():
                            # Prefix with VALUE_ if starts with digit for integer enums
                            sanitized_member_name = f"VALUE_{sanitized_member_name}"
                        if keyword.iskeyword(sanitized_member_name):
                            sanitized_member_name += "_"
                        member_name = sanitized_member_name
                        values.append((member_name, int_val))
            rendered_code = self.renderer.render_enum(
                enum_name=enum_name,
                base_type=base_type,
                values=values,
                description=schema.description,
                context=context,
            )
        elif is_dataclass:
            # Prepare data for dataclass renderer
            class_name = NameSanitizer.sanitize_class_name(base_name_for_construct)
            fields_data: List[Tuple[str, str, Optional[str], Optional[str]]] = []
            if schema.properties:
                # Separate required and optional for the renderer to handle ordering
                required_props = {prop: ps for prop, ps in schema.properties.items() if prop in schema.required}
                optional_props = {prop: ps for prop, ps in schema.properties.items() if prop not in schema.required}

                # Process required fields
                for prop, ps in required_props.items():
                    py_type = TypeHelper.get_python_type_for_schema(ps, self.schemas, context, required=True)
                    py_type = self.clean_field_type(py_type)
                    fields_data.append((prop, py_type, None, ps.description))

                # Process optional fields
                for prop, ps in optional_props.items():
                    py_type = TypeHelper.get_python_type_for_schema(ps, self.schemas, context, required=False)
                    py_type = self.clean_field_type(py_type)
                    default_expr: Optional[str] = self._get_field_default(ps, context)
                    fields_data.append((prop, py_type, default_expr, ps.description))

            rendered_code = self.renderer.render_dataclass(
                class_name=class_name,
                fields=fields_data,
                description=schema.description,
                context=context,
            )

        return self.formatter.format(rendered_code)

    def _get_field_default(self, ps: IRSchema, context: RenderContext) -> Optional[str]:
        """
        Determines the default value expression string for a dataclass field.
        This method is called for fields determined to be optional.

        Args:
            ps: The property schema to analyze
            context: The rendering context

        Returns:
            A string representing the Python default value expression
        """
        # Restore logic for default_factory for list and dict
        if ps.type == "array":
            context.add_import("dataclasses", "field")
            return "field(default_factory=list)"
        elif ps.type == "object" and ps.name is None and not ps.any_of and not ps.one_of and not ps.all_of:
            # This condition aims for anonymous objects that are not part of a union/composition.
            # These should get default_factory=dict if they are optional fields.
            context.add_import("dataclasses", "field")
            return "field(default_factory=dict)"
        else:
            # Primitives, enums, named objects, unions default to None when optional
            return "None"

    def _analyze_and_register_imports(self, schema: IRSchema, context: RenderContext) -> None:
        """
        Analyze a schema and register necessary imports for the generated code.

        This ensures that all necessary types used in the model are properly imported
        in the generated Python file.

        Args:
            schema: The schema to analyze
            context: The rendering context for import registration
        """
        # Call the helper to ensure types within properties/items/composition are analyzed
        # and imports registered
        _ = TypeHelper.get_python_type_for_schema(schema, self.schemas, context, required=True)
