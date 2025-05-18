"""
Generates Python code for dataclasses from IRSchema objects.
"""

import logging
import json
from typing import Dict, List, Optional, Tuple

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.helpers.type_helper import TypeHelper
from pyopenapi_gen.helpers.type_resolution.finalizer import TypeFinalizer

logger = logging.getLogger(__name__)


class DataclassGenerator:
    """Generates Python code for a dataclass."""

    def __init__(
        self,
        renderer: PythonConstructRenderer,
        all_schemas: Optional[Dict[str, IRSchema]],
    ):
        """
        Initialize a new DataclassGenerator.

        Contracts:
            Pre-conditions:
                - ``renderer`` is not None.
        """
        assert renderer is not None, "PythonConstructRenderer cannot be None."
        self.renderer = renderer
        self.all_schemas = all_schemas if all_schemas is not None else {}

    def _get_field_default(self, ps: IRSchema, context: RenderContext) -> Optional[str]:
        """
        Determines the default value expression string for a dataclass field.
        This method is called for fields determined to be optional.

        Args:
            ps: The property schema to analyze.
            context: The rendering context.

        Returns:
            A string representing the Python default value expression or None.

        Contracts:
            Pre-conditions:
                - ``ps`` is not None.
                - ``context`` is not None.
            Post-conditions:
                - Returns a valid Python default value string (e.g., "None", "field(default_factory=list)", "\"abc\"") or None.
        """
        assert ps is not None, "Property schema (ps) cannot be None."
        assert context is not None, "RenderContext cannot be None."

        if ps.type == "array":
            context.add_import("dataclasses", "field")
            return "field(default_factory=list)"
        elif ps.type == "object" and ps.name is None and not ps.any_of and not ps.one_of and not ps.all_of:
            context.add_import("dataclasses", "field")
            return "field(default_factory=dict)"

        if ps.default is not None:
            if isinstance(ps.default, str):
                escaped_inner_content = json.dumps(ps.default)[1:-1]
                return '"' + escaped_inner_content + '"'
            elif isinstance(ps.default, bool):
                return str(ps.default)
            elif isinstance(ps.default, (int, float)):
                return str(ps.default)
            else:
                logger.warning(
                    f"DataclassGenerator: Complex default value '{ps.default}' for field '{ps.name}' of type '{ps.type}"
                    f" cannot be directly rendered. Falling back to None. Type: {type(ps.default)}"
                )
        return "None"

    def generate(
        self,
        schema: IRSchema,
        base_name: str,
        context: RenderContext,
    ) -> str:
        """
        Generates the Python code for a dataclass.

        Args:
            schema: The IRSchema for the dataclass.
            base_name: The base name for the dataclass.
            context: The render context.

        Returns:
            The generated Python code string for the dataclass.

        Contracts:
            Pre-conditions:
                - ``schema`` is not None and ``schema.name`` is not None.
                - ``base_name`` is a non-empty string.
                - ``context`` is not None.
                - ``schema.type`` is suitable for a dataclass (e.g. "object", or "array" for wrapper style).
            Post-conditions:
                - Returns a non-empty string containing valid Python code for a dataclass.
                - ``@dataclass`` decorator is present, implying ``dataclasses.dataclass`` is imported.
        """
        assert schema is not None, "Schema cannot be None for dataclass generation."
        assert schema.name is not None, "Schema name must be present for dataclass generation."
        assert base_name, "Base name cannot be empty for dataclass generation."
        assert context is not None, "RenderContext cannot be None."
        # Additional check for schema type might be too strict here, as ModelVisitor decides eligibility.

        class_name = base_name
        fields_data: List[Tuple[str, str, Optional[str], Optional[str]]] = []

        if schema.type == "array" and schema.items:
            field_name_for_array_content = "items"
            assert schema.items is not None, "Schema items must be present for array type dataclass field."

            list_item_py_type = TypeHelper.get_python_type_for_schema(
                schema.items, self.all_schemas, context, required=True
            )
            list_item_py_type = TypeFinalizer(context)._clean_type(list_item_py_type)
            field_type_str = f"List[{list_item_py_type}]"

            final_field_type_str = TypeFinalizer(context).finalize(
                py_type=field_type_str, schema=schema, required=False
            )

            synthetic_field_schema_for_default = IRSchema(
                name=field_name_for_array_content,
                type="array",
                items=schema.items,
                is_nullable=schema.is_nullable,
                default=schema.default,
            )
            array_items_field_default_expr = self._get_field_default(synthetic_field_schema_for_default, context)

            field_description = schema.description
            if not field_description and list_item_py_type != "Any":
                field_description = f"A list of {list_item_py_type} items."
            elif not field_description:
                field_description = "A list of items."

            fields_data.append((
                field_name_for_array_content,
                final_field_type_str,
                array_items_field_default_expr,
                field_description,
            ))
        elif schema.properties:
            sorted_props = sorted(schema.properties.items(), key=lambda item: (item[0] not in schema.required, item[0]))

            for prop_name, prop_schema in sorted_props:
                is_required = prop_name in schema.required

                py_type = TypeHelper.get_python_type_for_schema(
                    prop_schema,
                    self.all_schemas,
                    context,
                    required=is_required,
                    resolve_alias_target=False,
                    parent_schema_name=schema.name,
                )
                py_type = TypeFinalizer(context)._clean_type(py_type)

                default_expr: Optional[str] = None
                if not is_required:
                    default_expr = self._get_field_default(prop_schema, context)

                field_doc = prop_schema.description
                fields_data.append((prop_name, py_type, default_expr, field_doc))

        logger.debug(
            f"DataclassGenerator: Preparing to render dataclass '{class_name}' with fields: {fields_data}.אללو"
        )

        rendered_code = self.renderer.render_dataclass(
            class_name=class_name,
            fields=fields_data,
            description=schema.description,
            context=context,
        )

        assert rendered_code.strip(), "Generated dataclass code cannot be empty."
        # PythonConstructRenderer adds the @dataclass decorator and import
        assert "@dataclass" in rendered_code, "Dataclass code missing @dataclass decorator."
        assert (
            "dataclasses" in context.import_collector.imports
            and "dataclass" in context.import_collector.imports["dataclasses"]
        ), "dataclass import was not added to context by renderer."
        if "default_factory" in rendered_code:  # Check for field import if factory is used
            assert "field" in context.import_collector.imports.get("dataclasses", set()), (
                "'field' import from dataclasses missing when default_factory is used."
            )

        return rendered_code
