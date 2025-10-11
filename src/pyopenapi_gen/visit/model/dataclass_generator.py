"""
Generates Python code for dataclasses from IRSchema objects.
"""

import json
import logging
from typing import Any, List, Tuple

from pyopenapi_gen import IRSchema
from pyopenapi_gen.context.render_context import RenderContext
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.core.writers.python_construct_renderer import PythonConstructRenderer
from pyopenapi_gen.helpers.type_resolution.finalizer import TypeFinalizer
from pyopenapi_gen.types.services.type_service import UnifiedTypeService

logger = logging.getLogger(__name__)


class DataclassGenerator:
    """Generates Python code for a dataclass."""

    def __init__(
        self,
        renderer: PythonConstructRenderer,
        all_schemas: dict[str, IRSchema] | None,
    ):
        """
        Initialize a new DataclassGenerator.

        Contracts:
            Pre-conditions:
                - ``renderer`` is not None.
        """
        if renderer is None:
            raise ValueError("PythonConstructRenderer cannot be None.")
        self.renderer = renderer
        self.all_schemas = all_schemas if all_schemas is not None else {}
        self.type_service = UnifiedTypeService(self.all_schemas)

    def _is_arbitrary_json_object(self, schema: IRSchema) -> bool:
        """
        Check if schema represents an arbitrary JSON object (additionalProperties but no properties).

        Args:
            schema: The schema to check.

        Returns:
            True if this is an arbitrary JSON object that should use wrapper class.
        """
        return (
            schema.type == "object"
            and not schema.properties  # No defined properties
            and (
                schema.additional_properties is True  # Explicit true
                or isinstance(schema.additional_properties, IRSchema)  # Schema for additional props
            )
        )

    def _generate_json_wrapper_class(
        self,
        class_name: str,
        schema: IRSchema,
        context: RenderContext,
    ) -> str:
        """
        Generate a wrapper class for arbitrary JSON objects.

        This wrapper class preserves all JSON data and provides dict-like access,
        preventing data loss when deserializing API responses with arbitrary properties.

        Args:
            class_name: Name of the wrapper class.
            schema: The schema (should have additionalProperties but no properties).
            context: Render context for imports.

        Returns:
            Python code for the wrapper class.
        """
        # Register required imports
        context.add_import("dataclasses", "dataclass")
        context.add_import("dataclasses", "field")
        context.add_import("typing", "Any")
        # Use absolute core import path - add_import will handle it correctly
        context.add_import(f"{context.core_package_name}.schemas", "BaseSchema")

        description = schema.description or "Generic JSON value object that preserves arbitrary data."

        # Generate the wrapper class code
        code = f'''__all__ = ["{class_name}"]

@dataclass
class {class_name}(BaseSchema):
    """
    {description}

    This class wraps arbitrary JSON objects with no defined schema,
    preserving all data during serialization/deserialization.
    """

    _data: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> '{class_name}':
        """
        Create {class_name} from dictionary, preserving all data.

        Args:
            data: Dictionary with arbitrary keys and values.

        Returns:
            {class_name} instance containing the data.
        """
        instance = cls(_data=data)
        return instance

    def to_dict(self, exclude_none: bool = False) -> dict[str, Any]:
        """
        Convert back to dictionary.

        Args:
            exclude_none: If True, exclude None values from output.

        Returns:
            Dictionary representation of the data.
        """
        if exclude_none:
            return {{k: v for k, v in self._data.items() if v is not None}}
        return self._data.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for backward compatibility."""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Dict-like item access."""
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Dict-like item setting."""
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator."""
        return key in self._data

    def __bool__(self) -> bool:
        """Truthy if contains data."""
        return bool(self._data)

    def keys(self) -> Any:
        """Return dictionary keys."""
        return self._data.keys()

    def values(self) -> Any:
        """Return dictionary values."""
        return self._data.values()

    def items(self) -> Any:
        """Return dictionary items."""
        return self._data.items()
'''
        return code

    def _get_field_default(self, ps: IRSchema, context: RenderContext) -> str | None:
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
                - Returns a valid Python default value string
                  (e.g., "None", "field(default_factory=list)", "\"abc\"") or None.
        """
        if ps is None:
            raise ValueError("Property schema (ps) cannot be None.")
        if context is None:
            raise ValueError("RenderContext cannot be None.")

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

    def _requires_field_mapping(self, api_field: str, python_field: str) -> bool:
        """Check if field mapping is required between API and Python field names."""
        return api_field != python_field

    def _generate_field_mappings(self, properties: dict[str, Any], sanitized_names: dict[str, str]) -> dict[str, str]:
        """Generate field mappings for BaseSchema configuration."""
        mappings = {}
        for api_name, python_name in sanitized_names.items():
            if api_name in properties and self._requires_field_mapping(api_name, python_name):
                mappings[api_name] = python_name
        return mappings

    def _has_any_mappings(self, properties: dict[str, Any], sanitized_names: dict[str, str]) -> bool:
        """Check if any field mappings are needed."""
        return bool(self._generate_field_mappings(properties, sanitized_names))

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
        if schema is None:
            raise ValueError("Schema cannot be None for dataclass generation.")
        if schema.name is None:
            raise ValueError("Schema name must be present for dataclass generation.")
        if not base_name:
            raise ValueError("Base name cannot be empty for dataclass generation.")
        if context is None:
            raise ValueError("RenderContext cannot be None.")
        # Additional check for schema type might be too strict here, as ModelVisitor decides eligibility.

        # Check if this is an arbitrary JSON object that needs wrapper class
        if self._is_arbitrary_json_object(schema):
            logger.info(
                f"DataclassGenerator: Schema '{base_name}' is an arbitrary JSON object. "
                "Generating wrapper class to preserve data."
            )
            return self._generate_json_wrapper_class(base_name, schema, context)

        class_name = base_name
        fields_data: List[Tuple[str, str, str | None, str | None]] = []
        field_mappings: dict[str, str] = {}

        if schema.type == "array" and schema.items:
            field_name_for_array_content = "items"
            if schema.items is None:
                raise ValueError("Schema items must be present for array type dataclass field.")

            list_item_py_type = self.type_service.resolve_schema_type(schema.items, context, required=True)
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

            fields_data.append(
                (
                    field_name_for_array_content,
                    final_field_type_str,
                    array_items_field_default_expr,
                    field_description,
                )
            )
        elif schema.properties:
            sorted_props = sorted(schema.properties.items(), key=lambda item: (item[0] not in schema.required, item[0]))

            for prop_name, prop_schema in sorted_props:
                is_required = prop_name in schema.required

                # Sanitize the property name for use as a Python attribute
                field_name = NameSanitizer.sanitize_method_name(prop_name)

                # Track field mapping if the names differ
                if self._requires_field_mapping(prop_name, field_name):
                    field_mappings[prop_name] = field_name

                py_type = self.type_service.resolve_schema_type(prop_schema, context, required=is_required)

                default_expr: str | None = None
                if not is_required:
                    default_expr = self._get_field_default(prop_schema, context)

                # Enhance field documentation for mapped fields
                field_doc = prop_schema.description
                if field_mappings.get(prop_name) == field_name and prop_name != field_name:
                    if field_doc:
                        field_doc = f"{field_doc} (maps from '{prop_name}')"
                    else:
                        field_doc = f"Maps from '{prop_name}'"

                fields_data.append((field_name, py_type, default_expr, field_doc))

        # logger.debug(
        #     f"DataclassGenerator: Preparing to render dataclass '{class_name}' with fields: {fields_data}."
        # )

        # Always use BaseSchema for better developer experience
        # Only include field mappings if there are actual mappings needed
        rendered_code = self.renderer.render_dataclass(
            class_name=class_name,
            fields=fields_data,
            description=schema.description,
            context=context,
            field_mappings=field_mappings if field_mappings else None,
        )

        if not rendered_code.strip():
            raise RuntimeError("Generated dataclass code cannot be empty.")
        # PythonConstructRenderer adds the @dataclass decorator and import
        if "@dataclass" not in rendered_code:
            raise RuntimeError("Dataclass code missing @dataclass decorator.")
        if not (
            "dataclasses" in context.import_collector.imports
            and "dataclass" in context.import_collector.imports["dataclasses"]
        ):
            raise RuntimeError("dataclass import was not added to context by renderer.")
        if "default_factory" in rendered_code:  # Check for field import if factory is used
            if "field" not in context.import_collector.imports.get("dataclasses", set()):
                raise RuntimeError("'field' import from dataclasses missing when default_factory is used.")

        return rendered_code
