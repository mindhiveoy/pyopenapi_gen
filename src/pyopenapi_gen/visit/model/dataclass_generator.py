"""
Generates Python code for dataclasses from IRSchema objects.
"""

import json
import logging
from typing import List, Tuple

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

        When additionalProperties references a typed schema, the wrapper will:
        - Store values with proper type annotations
        - Include _value_type ClassVar for runtime type resolution
        - Generate hooks that deserialize values into their proper types

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

        description = schema.description or "Generic JSON value object that preserves arbitrary data."

        # Determine value type from additionalProperties
        value_type = "Any"
        has_typed_values = False

        if isinstance(schema.additional_properties, IRSchema):
            ap_schema = schema.additional_properties
            # Resolve the type using UnifiedTypeService
            resolved_type = self.type_service.resolve_schema_type(ap_schema, context, required=True)
            # Only use typed wrapper if we have a concrete type (not Any or Any | None)
            if resolved_type and resolved_type != "Any" and "Any" not in resolved_type:
                value_type = resolved_type
                has_typed_values = True

        if has_typed_values:
            # Generate typed wrapper with value deserialisation
            context.add_import("typing", "ClassVar")
            code = self._generate_typed_wrapper_class(class_name, value_type, description, context)
        else:
            # Generate untyped wrapper (existing behaviour)
            code = self._generate_untyped_wrapper_class(class_name, description, context)

        return code

    def _generate_untyped_wrapper_class(
        self,
        class_name: str,
        description: str,
        context: RenderContext,
    ) -> str:
        """Generate wrapper class for untyped additionalProperties (Any values)."""
        return f'''__all__ = ["{class_name}"]

@dataclass
class {class_name}:
    """
    {description}

    This class wraps arbitrary JSON objects with no defined schema,
    preserving all data during serialization/deserialization.

    Example:
        from {context.core_package_name}.cattrs_converter import structure_from_dict, unstructure_to_dict

        # Deserialize from API response
        obj = structure_from_dict({{"key": "value"}}, {class_name})

        # Access data
        print(obj["key"])  # "value"
        obj["new_key"] = "new_value"

        # Serialize for API request
        data = unstructure_to_dict(obj)  # {{"key": "value", "new_key": "new_value"}}
    """

    _data: dict[str, Any] = field(default_factory=dict, repr=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value for key, returning default if key not present."""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get value for key."""
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set value for key."""
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data

    def __bool__(self) -> bool:
        """Return True if wrapper contains any data."""
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

    def __iter__(self) -> Any:
        """Iterate over keys."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return number of items."""
        return len(self._data)


# Register cattrs hooks for {class_name}
def _structure_{class_name.lower()}(data: dict[str, Any], _: type[{class_name}]) -> {class_name}:
    """Structure hook for cattrs to handle {class_name} deserialization."""
    if data is None:
        return {class_name}()
    if isinstance(data, {class_name}):
        return data
    return {class_name}(_data=data)


def _unstructure_{class_name.lower()}(instance: {class_name}) -> dict[str, Any]:
    """Unstructure hook for cattrs to handle {class_name} serialization."""
    return instance._data.copy()
'''

    def _generate_typed_wrapper_class(
        self,
        class_name: str,
        value_type: str,
        description: str,
        context: RenderContext,
    ) -> str:
        """Generate wrapper class for typed additionalProperties with value deserialisation."""
        # Import Iterator and ValuesView for proper type hints
        context.add_import("typing", "Iterator")
        context.add_import("collections.abc", "ValuesView")
        context.add_import("collections.abc", "ItemsView")
        context.add_import("collections.abc", "KeysView")

        return f'''__all__ = ["{class_name}"]

@dataclass
class {class_name}:
    """
    {description}

    This class wraps a dictionary with typed values, providing dict-like access
    while ensuring values are properly deserialised into {value_type} instances.

    Example:
        from {context.core_package_name}.cattrs_converter import structure_from_dict, unstructure_to_dict

        # Deserialize from API response - values become {value_type} instances
        obj = structure_from_dict({{"key": {{"field": "value"}}}}, {class_name})

        # Access returns typed {value_type} instance
        item = obj["key"]
        print(item.field)  # "value" - direct attribute access

        # Serialize for API request
        data = unstructure_to_dict(obj)
    """

    _data: dict[str, {value_type}] = field(default_factory=dict, repr=False)

    # Runtime type information for cattrs deserialisation
    _value_type: ClassVar[str] = "{value_type}"

    def get(self, key: str, default: {value_type} | None = None) -> {value_type} | None:
        """Get value for key, returning default if key not present."""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> {value_type}:
        """Get value for key."""
        return self._data[key]

    def __setitem__(self, key: str, value: {value_type}) -> None:
        """Set value for key."""
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data

    def __bool__(self) -> bool:
        """Return True if wrapper contains any data."""
        return bool(self._data)

    def keys(self) -> KeysView[str]:
        """Return dictionary keys."""
        return self._data.keys()

    def values(self) -> ValuesView[{value_type}]:
        """Return dictionary values."""
        return self._data.values()

    def items(self) -> ItemsView[str, {value_type}]:
        """Return dictionary items."""
        return self._data.items()

    def __iter__(self) -> Iterator[str]:
        """Iterate over keys."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return number of items."""
        return len(self._data)


# Register cattrs hooks for {class_name}
def _structure_{class_name.lower()}(data: dict[str, Any], _: type[{class_name}]) -> {class_name}:
    """Structure hook for cattrs to handle {class_name} deserialization with typed values."""
    if data is None:
        return {class_name}()
    if isinstance(data, {class_name}):
        return data

    # Import converter lazily to avoid circular imports
    from {context.core_package_name}.cattrs_converter import converter, _register_structure_hooks_recursively

    # Register hooks for dataclass value types (once, outside loop)
    if hasattr({value_type}, '__dataclass_fields__'):
        _register_structure_hooks_recursively({value_type})

    # Deserialise each value into {value_type}
    # Using converter.structure() for all values - cattrs handles primitives, datetime, bytes, etc.
    structured_data: dict[str, {value_type}] = {{}}
    for key, value in data.items():
        structured_data[key] = converter.structure(value, {value_type})

    return {class_name}(_data=structured_data)


def _unstructure_{class_name.lower()}(instance: {class_name}) -> dict[str, Any]:
    """Unstructure hook for cattrs to handle {class_name} serialization."""
    from {context.core_package_name}.cattrs_converter import converter

    # Unstructure each value
    return {{
        key: converter.unstructure(value)
        for key, value in instance._data.items()
    }}
'''

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
            # Check if this is an enum field (has a name that references another schema with enum values)
            if ps.name and self.all_schemas:
                enum_schema = self.all_schemas.get(ps.name)
                if enum_schema and enum_schema.enum:
                    # This is an enum field - convert default value to enum member access
                    # e.g., "default" -> JobPriorityEnum.DEFAULT
                    default_str = str(ps.default)
                    # Convert the value to the enum member name (e.g., "default" -> "DEFAULT")
                    enum_member_name = default_str.upper().replace("-", "_").replace(" ", "_")
                    return f"{ps.name}.{enum_member_name}"

            if isinstance(ps.default, str):
                escaped_inner_content = json.dumps(ps.default)[1:-1]
                return '"' + escaped_inner_content + '"'
            elif isinstance(ps.default, bool):
                return str(ps.default)
            elif isinstance(ps.default, (int, float)):
                return str(ps.default)
            else:
                logger.warning(
                    f"DataclassGenerator: Complex default value '{ps.default}' for field '{ps.name}' of type '{ps.type}'"
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

            # Track sanitised names to detect collisions
            seen_field_names: dict[str, str] = {}  # sanitised_name → original_api_name

            for prop_name, prop_schema in sorted_props:
                is_required = prop_name in schema.required

                # Sanitize the property name for use as a Python attribute
                field_name = NameSanitizer.sanitize_method_name(prop_name)

                # Collision detection: check if this sanitised name was already used
                if field_name in seen_field_names:
                    original_api_name = seen_field_names[field_name]
                    base_field_name = field_name
                    suffix = 2
                    while field_name in seen_field_names:
                        field_name = f"{base_field_name}_{suffix}"
                        suffix += 1
                    logger.warning(
                        f"Field name collision in schema '{base_name}': "
                        f"API fields '{original_api_name}' and '{prop_name}' both sanitise to '{base_field_name}'. "
                        f"Using '{seen_field_names[base_field_name]}' for '{original_api_name}' "
                        f"and '{field_name}' for '{prop_name}'."
                    )

                # Track this field name as used
                seen_field_names[field_name] = prop_name

                # Always create field mapping to preserve original API name
                field_mappings[prop_name] = field_name

                py_type = self.type_service.resolve_schema_type(prop_schema, context, required=is_required)

                default_expr: str | None = None
                if not is_required:
                    default_expr = self._get_field_default(prop_schema, context)

                # Enhance field documentation for mapped fields when names differ
                field_doc = prop_schema.description
                if prop_name != field_name:
                    if field_doc:
                        field_doc = f"{field_doc} (maps from '{prop_name}')"
                    else:
                        field_doc = f"Maps from '{prop_name}'"

                fields_data.append((field_name, py_type, default_expr, field_doc))

        # logger.debug(
        #     f"DataclassGenerator: Preparing to render dataclass '{class_name}' with fields: {fields_data}."
        # )

        # Always include field mappings to preserve original API field names
        # This ensures correct serialisation for any API naming convention
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
