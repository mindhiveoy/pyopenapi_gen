"""
ModelVisitor: Transforms IRSchema objects into Python model code (dataclasses and enums).

This module provides the ModelVisitor class that generates Python code for data models
defined in OpenAPI specifications, supporting type aliases, enums, and dataclasses.
"""

from typing import Dict, List, Optional, Tuple

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext

from ..core.utils import Formatter, NameSanitizer
from ..core.writers.python_construct_renderer import PythonConstructRenderer
from ..helpers.type_helper import get_python_type_for_schema
from .visitor import Visitor


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

    def visit_IRSchema(self, schema: IRSchema, context: RenderContext) -> str:
        """
        Visit an IRSchema node and generate Python code for it.
        
        Args:
            schema: The schema to visit
            context: The rendering context for imports and configuration
            
        Returns:
            Formatted Python code for the model as a string
        """
        # ---- Type Alias Detection ----
        is_primitive_alias = (
            schema.name and not schema.properties and schema.type in ("string", "integer", "number", "boolean")
        )
        is_array_alias = schema.name and not schema.properties and schema.type == "array" and schema.items is not None
        is_type_alias = is_primitive_alias or is_array_alias

        # --- Enum Detection ---
        is_enum = schema.enum and schema.type in ("string", "integer") and not is_type_alias

        # --- Dataclass Detection ---
        is_dataclass = not is_enum and not is_type_alias

        # --- Basic Validation & Skipping ---
        if not schema.name and (is_type_alias or is_enum or is_dataclass):
            return ""
        assert schema.name is not None

        # --- Import Registration (Delegated for constructs, handled here for types) ---
        self._analyze_and_register_imports(schema, context)

        # Mark this module as generated
        if context.current_file:
            context.mark_generated_module(context.current_file)

        # --- Code Generation Dispatch ---
        rendered_code = ""

        if is_type_alias:
            # Prepare data for alias renderer
            alias_name = NameSanitizer.sanitize_class_name(schema.name)
            target_type = get_python_type_for_schema(schema, self.schemas, context, required=True)
            rendered_code = self.renderer.render_alias(
                alias_name=alias_name,
                target_type=target_type,
                description=schema.description,
                context=context,
            )
        elif is_enum:
            # Prepare data for enum renderer
            enum_name = NameSanitizer.sanitize_class_name(schema.name)
            base_type = "str" if schema.type == "string" else "int"
            values: List[Tuple[str, str | int]] = []
            if schema.enum:
                for val in schema.enum:
                    if base_type == "str":
                        member_name = NameSanitizer.sanitize_class_name(
                            str(val).upper().replace("-", "_").replace(" ", "_")
                        )
                        values.append((member_name, str(val)))
                    else:
                        int_val = int(val) if isinstance(val, (int, str)) and str(val).isdigit() else 0
                        member_name_base = str(val).replace("-", "_").replace(" ", "_")
                        member_name = (
                            NameSanitizer.sanitize_class_name(f"VALUE_{member_name_base}")
                            if not member_name_base.isidentifier() or member_name_base[0].isdigit()
                            else member_name_base.upper()
                        )
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
            class_name = NameSanitizer.sanitize_class_name(schema.name)
            fields_data: List[Tuple[str, str, Optional[str], Optional[str]]] = []
            if schema.properties:
                # Separate required and optional for the renderer to handle ordering
                required_props = {prop: ps for prop, ps in schema.properties.items() if prop in schema.required}
                optional_props = {prop: ps for prop, ps in schema.properties.items() if prop not in schema.required}

                # Process required fields
                for prop, ps in required_props.items():
                    py_type = get_python_type_for_schema(ps, self.schemas, context, required=True)
                    fields_data.append((prop, py_type, None, ps.description))

                # Process optional fields
                for prop, ps in optional_props.items():
                    py_type = get_python_type_for_schema(ps, self.schemas, context, required=False)
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
        
        Args:
            ps: The property schema to analyze
            context: The rendering context
            
        Returns:
            A string representing the Python default value expression
        """
        if ps.type == "array":
            return "field(default_factory=list)"
        elif ps.type == "object" and ps.name is None and not ps.any_of and not ps.one_of and not ps.all_of:
            # Default factory only for anonymous, non-composed objects
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
        _ = get_python_type_for_schema(
            schema, self.schemas, context, required=True
        )
