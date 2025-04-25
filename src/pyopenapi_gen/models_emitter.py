from jinja2 import Environment
import os
from typing import Dict, Set
import re

from .loader import IRSpec
from . import IRSchema
from .utils import ImportCollector, NameSanitizer, TemplateRenderer, Formatter

# OpenAPI to Python type mapping
OPENAPI_TO_PYTHON_TYPES: Dict[str, str] = {
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "string": "str",
    "array": "List",
    "object": "Dict[str, Any]",  # Any is used in the dict definition here
}

# Format-specific type mappings
FORMAT_TYPE_MAPPING: Dict[str, str] = {
    "int32": "int",
    "int64": "int",
    "float": "float",
    "double": "float",
    "byte": "str",  # base64 encoded string
    "binary": "bytes",
    "date": "date",  # Would require datetime import
    "date-time": "datetime",  # Would require datetime import
    "password": "str",
    "email": "str",
    "uuid": "str",  # Could be UUID with uuid import
}

# Model template without imports, as these will be handled by ImportCollector
MODEL_TEMPLATE = '''
{% if schema.enum and schema.type == "string" %}
class {{ schema.name | sanitize_class_name }}(str, Enum):
    """
    {{ (schema.description or ('Enum values for ' + schema.name)) | wordwrap(72, wrapstring='\n    ') }}
    """
{% for val in schema.enum %}
    {{ val|upper|replace('-', '_')|replace(' ', '_') }} = "{{ val }}"
{% endfor %}
{% elif schema.enum and schema.type == "integer" %}
class {{ schema.name | sanitize_class_name }}(int, Enum):
    """
    {{ (schema.description or ('Enum values for ' + schema.name)) | wordwrap(72, wrapstring='\n    ') }}
    """
{% for val in schema.enum %}
    {%- if val is string -%}
    {{ val|replace('-', '_')|replace(' ', '_')|upper }} = {{ val }}
    {%- else -%}
    _{{ val }} = {{ val }}
    {%- endif %}
{% endfor %}
{% else %}
@dataclass
class {{ schema.name | sanitize_class_name }}:
{% if schema.description %}    """
    {{ schema.description | wordwrap(72, wrapstring='\n    ') }}
    """
{% endif %}
{% for prop, ps in schema.properties.items() %}
    {{ prop }}: {% if prop not in schema.required %}Optional[{% endif %}{{ get_type(ps) }}{% if prop not in schema.required %}]{% endif %} = {% if prop not in schema.required %}None{% else %}field(default_factory={{ get_default_factory(ps) }}){% endif %}  # {{ ps.description | replace('\n', ' ') if ps.description else '' }}
{% endfor %}
{% if not schema.properties %}
    # No properties defined in schema
    pass
{% endif %}
{% endif %}
'''


class ModelsEmitter:
    """Generates Python dataclass models from IRSpec."""

    def __init__(self) -> None:
        # Use centralized TemplateRenderer and Formatter for model templates
        self.renderer = TemplateRenderer()
        self.formatter = Formatter()
        self.schema_names: Set[str] = set()

    def _get_python_type(self, schema: IRSchema) -> str:
        """Convert IR schema to Python type annotation."""
        if not schema:
            return "Any"

        # For named primitive schemas (not enum), return the Python type, not the schema name
        if schema.name and schema.name in self.schema_names:
            if (
                schema.type in ("string", "integer", "number", "boolean")
                and not schema.enum
            ):
                # Use the actual Python type
                schema_type = schema.type
                if schema.format and schema.format in FORMAT_TYPE_MAPPING:
                    py_type = FORMAT_TYPE_MAPPING[schema.format]
                elif schema_type in OPENAPI_TO_PYTHON_TYPES:
                    py_type = OPENAPI_TO_PYTHON_TYPES[schema_type]
                else:
                    py_type = "Any"
                return py_type
            return schema.name  # Reference to another model or enum

        # Handle case where schema.type is a list (nullable types)
        schema_type = schema.type
        is_nullable = False
        if isinstance(schema_type, list):
            # Remove 'null' and check if type is nullable
            types = [t for t in schema_type if t != "null"]
            is_nullable = "null" in schema_type
            schema_type = types[0] if types else None
        else:
            is_nullable = False

        if schema.format and schema.format in FORMAT_TYPE_MAPPING:
            py_type = FORMAT_TYPE_MAPPING[schema.format]
        elif schema_type == "array" and schema.items:
            item_type = self._get_python_type(schema.items)
            py_type = f"List[{item_type}]"
        elif schema_type == "object" and schema.properties:
            # For embedded objects, just use a generic Dict
            py_type = "Dict[str, Any]"
        elif schema_type and schema_type in OPENAPI_TO_PYTHON_TYPES:
            py_type = OPENAPI_TO_PYTHON_TYPES[schema_type]
        else:
            py_type = "Any"

        # If nullable, wrap with Optional
        if is_nullable:
            py_type = f"Optional[{py_type}]"
        return py_type

    def _get_default_factory(self, schema: IRSchema) -> str:
        """Generate appropriate default factory based on schema type."""
        if schema.type == "array":
            return "list"
        elif schema.type == "object":
            return "dict"
        return "str"  # Fallback to a string factory

    def _has_special_type(self, schema: IRSchema, format_type: str) -> bool:
        """Check if schema or any nested schema has a particular format."""
        if schema.format == format_type:
            return True

        for prop_schema in schema.properties.values():
            if self._has_special_type(prop_schema, format_type):
                return True

        if schema.items and self._has_special_type(schema.items, format_type):
            return True

        return False

    def _collect_required_imports(self, schema: IRSchema) -> ImportCollector:
        """Collect all required imports for a schema."""
        imports = ImportCollector()

        # Always import dataclass
        imports.add_direct_import("dataclasses", "dataclass")
        imports.add_direct_import("dataclasses", "field")

        # Basic typing imports always needed
        imports.add_typing_import("Optional")
        imports.add_typing_import("Any")
        imports.add_typing_import("Dict")
        imports.add_typing_import("List")

        # Check for enum
        if schema.enum and schema.type == "string":
            imports.add_direct_import("enum", "Enum")

        # Check for date and datetime formats
        has_date = self._has_special_type(schema, "date")
        has_datetime = self._has_special_type(schema, "date-time")

        if has_date:
            imports.add_direct_import("datetime", "date")
        if has_datetime:
            imports.add_direct_import("datetime", "datetime")

        # Here we could add more specific imports based on schema content
        # For example, if a schema uses UUID or specialized types

        return imports

    def emit(self, spec: IRSpec, output_dir: str) -> None:
        """Render one model file per schema under <output_dir>/models."""
        models_dir = os.path.join(output_dir, "models")
        os.makedirs(models_dir, exist_ok=True)

        # Create an __init__.py to expose models as a package
        init_path = os.path.join(models_dir, "__init__.py")
        with open(init_path, "w") as f:
            exports = [name for name in spec.schemas.keys() if name]
            # __all__ should list sanitized class names
            exports_str = ", ".join(
                f'"{NameSanitizer.sanitize_class_name(name)}"' for name in exports
            )
            f.write(f"__all__ = [{exports_str}]\n\n")

            # Import all models using module names (original if valid identifier, else sanitized)
            for name in exports:
                if name:
                    class_name = NameSanitizer.sanitize_class_name(name)
                    # Use original name as module if valid identifier, otherwise sanitize
                    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
                        module_name = name
                    else:
                        module_name = NameSanitizer.sanitize_module_name(name)
                    f.write(f"from .{module_name} import {class_name}\n")

        # Store schema names for cross-references
        self.schema_names = {name for name in spec.schemas.keys() if name}

        # Prepare template string
        template_str = MODEL_TEMPLATE

        # Generate model files
        for name, schema in spec.schemas.items():
            print(
                f"[DEBUG] Processing schema: name={name}, type={schema.type}, properties={list(schema.properties.keys())}"
            )
            # Skip schemas without names
            if not name:
                print(f"[DEBUG] Skipping unnamed schema.")
                continue

            # 1. Emit string or integer enum models
            if schema.enum and schema.type in ("string", "integer"):
                print(f"[DEBUG] Writing enum model for: {name}")
                imports = self._collect_required_imports(schema)
                # Add Enum import for integer enums as well
                if schema.type == "integer":
                    imports.add_direct_import("enum", "Enum")
                content = self.renderer.render(
                    template_str,
                    schema=schema,
                    get_type=self._get_python_type,
                    get_default_factory=self._get_default_factory,
                )
                file_content = imports.get_formatted_imports() + "\n\n" + content
                file_content = self.formatter.format(file_content)
                module_name = NameSanitizer.sanitize_module_name(name)
                file_path = os.path.join(models_dir, f"{module_name}.py")
                print(f"[DEBUG] Writing file: {file_path}")
                with open(file_path, "w") as f:
                    f.write(file_content)
                continue

            # 2. Emit array aliases for arrays of primitives or models
            if schema.type == "array" and schema.items:
                print(f"[DEBUG] Writing array alias for: {name}")
                imports = ImportCollector()
                imports.add_typing_import("List")
                item_type = self._get_python_type(schema.items)
                # If item is a named model, import it
                if schema.items.name:
                    module = NameSanitizer.sanitize_module_name(schema.items.name)
                    cls = NameSanitizer.sanitize_class_name(schema.items.name)
                    imports.add_relative_import(f".{module}", cls)
                    alias = f"{NameSanitizer.sanitize_class_name(name)} = List[{cls}]"
                else:
                    alias = (
                        f"{NameSanitizer.sanitize_class_name(name)} = List[{item_type}]"
                    )
                file_content = imports.get_formatted_imports() + "\n\n" + alias
                file_content = self.formatter.format(file_content)
                module_name = NameSanitizer.sanitize_module_name(name)
                file_path = os.path.join(models_dir, f"{module_name}.py")
                print(f"[DEBUG] Writing file: {file_path}")
                with open(file_path, "w") as f:
                    f.write(file_content)
                continue

            # 3. Emit type aliases for named primitive schemas
            if (
                schema.type in ("string", "integer", "number", "boolean")
                and not schema.enum
            ):
                print(f"[DEBUG] Writing primitive alias for: {name}")
                imports = ImportCollector()
                py_type = self._get_python_type(schema)
                # Use the actual Python type, not the schema name
                alias = f"{NameSanitizer.sanitize_class_name(name)} = {py_type}"
                file_content = imports.get_formatted_imports() + "\n\n" + alias
                file_content = self.formatter.format(file_content)
                module_name = NameSanitizer.sanitize_module_name(name)
                file_path = os.path.join(models_dir, f"{module_name}.py")
                print(f"[DEBUG] Writing file: {file_path}")
                with open(file_path, "w") as f:
                    f.write(file_content)
                continue

            # 4. Emit dataclass for object schemas
            if schema.type == "object":
                imports = self._collect_required_imports(schema)
                content = self.renderer.render(
                    template_str,
                    schema=schema,
                    get_type=self._get_python_type,
                    get_default_factory=self._get_default_factory,
                )
                file_content = imports.get_formatted_imports() + "\n\n" + content
                file_content = self.formatter.format(file_content)
                module_name = NameSanitizer.sanitize_module_name(name)
                file_path = os.path.join(models_dir, f"{module_name}.py")
                print(f"[DEBUG] Writing file: {file_path}")
                with open(file_path, "w") as f:
                    f.write(file_content)
                continue

            # 5. Fallback: skip schemas that do not match any of the above
            print(f"[DEBUG] Skipping schema: {name} (type={schema.type})")
            continue
