"""
ModelVisitor: Transforms IRSchema objects into Python model code (dataclasses and enums).

This module provides the ModelVisitor class that generates Python code for data models
defined in OpenAPI specifications, supporting type aliases, enums, and dataclasses.
"""

import logging

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import Formatter
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.helpers.type_helper import TypeHelper

from ..visitor import Visitor  # Relative import from parent package

# Import new generators from the current 'model' package
from .alias_generator import AliasGenerator
from .dataclass_generator import DataclassGenerator
from .enum_generator import EnumGenerator

logger = logging.getLogger(__name__)


class ModelVisitor(Visitor[IRSchema, str]):
    """
    Visitor for rendering a Python model (dataclass, enum, or type alias) from an IRSchema.
    It determines the model type and delegates to specialized generators.

    Contracts:
        Post-conditions:
            - Returns a valid Python code string representing the model.
            - Returns an empty string if the schema should not be rendered as a standalone model.
            - All necessary imports for the generated model are registered in the context.
    """

    def __init__(self, schemas: dict[str, IRSchema] | None = None) -> None:
        """
        Initialize a new ModelVisitor.

        Args:
            schemas: Dictionary of all schemas for reference resolution.
        """
        self.formatter = Formatter()
        self.all_schemas = schemas or {}

        # Initialize PythonConstructRenderer once; it's passed to generators.
        self.renderer = PythonConstructRenderer()

        # Initialize generators, passing the shared renderer and all_schemas (where needed).
        self.alias_generator = AliasGenerator(self.renderer, self.all_schemas)
        self.enum_generator = EnumGenerator(self.renderer)
        self.dataclass_generator = DataclassGenerator(self.renderer, self.all_schemas)

    def visit_IRSchema(self, schema: IRSchema, context: RenderContext) -> str:
        """
        Visit an IRSchema node, determine model type, and delegate to the appropriate generator.

        Args:
            schema: The schema to visit.
            context: The rendering context for imports and configuration.

        Returns:
            Formatted Python code for the model as a string, or an empty string if not generated.

        Contracts:
            Pre-conditions:
                - ``schema`` is a valid ``IRSchema`` object.
                - ``context`` is a valid ``RenderContext`` object.
            Post-conditions:
                - If a model is generated, it's a valid Python code string.
                - If ``schema.name`` is None and the schema would be a complex type (alias, enum, dataclass),
                  an empty string is returned.
                - Necessary imports for the generated types are added to ``context``.
        """
        # --- Model Type Detection Logic ---
        is_enum = bool(schema.name and schema.enum and schema.type in ("string", "integer"))

        is_type_alias = bool(schema.name and not schema.properties and not is_enum and schema.type != "object")

        if schema.type == "array" and schema.items and schema.items.type == "object" and schema.items.name is None:
            if is_type_alias:
                # logger.debug(
                #     f"ModelVisitor: Schema '{schema.name}' is an array of anonymous items. "
                #     "It will be rendered as a dataclass instead of a TypeAlias."
                # )
                is_type_alias = False
                schema.is_data_wrapper = True

        is_dataclass = not is_enum and not is_type_alias
        # --- End of Detection Logic ---

        if not schema.name and (is_type_alias or is_enum or is_dataclass):
            # logger.debug(f"ModelVisitor: Skipping anonymous schema that would be a standalone model: {schema}")
            return ""

        # Pre-condition check after filtering anonymous
        # schema.name is the original sanitized name. schema.generation_name is the de-collided one.
        # For standalone models, generation_name should be set and used.
        if schema.generation_name:
            base_name_for_construct = schema.generation_name
            # logger.debug(f"Using schema.generation_name ('{schema.generation_name}') for construct base name.")
        elif (
            schema.name
        ):  # Fallback for schemas not processed by emitter pre-naming (e.g. inline, or if generation_name wasn't set)
            base_name_for_construct = schema.name
            # logger.debug(f"Using schema.name ('{schema.name}') for construct base name, "
            #               f"as generation_name is not set.")
        else:
            # This case should ideally be caught by the "not schema.name and (is_type_alias...)" check above
            # or by assertions in generators if they receive a schema without a usable name.
            logger.error(
                f"ModelVisitor: Schema has no usable name (name or generation_name) for model generation: {schema}"
            )
            raise RuntimeError("Schema must have a name or generation_name for model code generation at this point.")
            # return "" # Should not reach here if assertions are active

        # --- Import Registration ---
        # Analyze the schema for all necessary type imports and register them.
        _ = TypeHelper.get_python_type_for_schema(
            schema, self.all_schemas, context, required=True, resolve_alias_target=True
        )

        if context.current_file:
            context.mark_generated_module(context.current_file)

        # --- Code Generation Dispatch ---
        rendered_code = ""
        if is_type_alias:
            # logger.debug(f"ModelVisitor: Dispatching to AliasGenerator for schema: {schema.name}")
            rendered_code = self.alias_generator.generate(schema, base_name_for_construct, context)
        elif is_enum:
            # logger.debug(f"ModelVisitor: Dispatching to EnumGenerator for schema: {schema.name}")
            rendered_code = self.enum_generator.generate(schema, base_name_for_construct, context)
        elif is_dataclass:
            # logger.debug(f"ModelVisitor: Dispatching to DataclassGenerator for schema: {schema.name}")
            rendered_code = self.dataclass_generator.generate(schema, base_name_for_construct, context)
        else:
            # logger.debug(
            #     f"ModelVisitor: Schema '{schema.name if schema.name else 'Unnamed'}' "
            #     f"(type: {schema.type}) did not map to a dedicated "
            #     "alias, enum, or dataclass. No standalone model generated by ModelVisitor."
            # )
            # Post-condition: returns empty string if no specific generator called
            if rendered_code:
                raise RuntimeError("Rendered code should be empty if no generator was matched.")
            return ""

        # Post-condition: ensure some code was generated if a generator was called
        if not rendered_code.strip() and (is_type_alias or is_enum or is_dataclass):
            raise RuntimeError(
                f"Code generation resulted in an empty string for schema '{schema.name}' which was matched as a model type."
            )

        return self.formatter.format(rendered_code)

    def _get_field_default(self, ps: IRSchema, context: RenderContext) -> str | None:
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
        _ = TypeHelper.get_python_type_for_schema(
            schema, self.all_schemas, context, required=True, resolve_alias_target=True
        )
