import os
from typing import Dict, Optional, Set

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.render_context import RenderContext

from ..core.utils import Formatter, NameSanitizer
from ..visit.model_visitor import ModelVisitor

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
{% set required_props = [] %}
{% set optional_props = [] %}
{% for prop, ps in schema.properties.items() %}
    {% if prop in schema.required %}
        {% set _ = required_props.append((prop, ps)) %}
    {% else %}
        {% set _ = optional_props.append((prop, ps)) %}
    {% endif %}
{% endfor %}
{% for prop, ps in required_props %}
    {# If the property is a true object (not a model reference), use default_factory #}
    {% set is_object = ps.type == 'object' and not ps.name %}
    {{ prop }}: {{ get_type(ps, required=True) }}{% set factory = get_default_factory(ps) %}{% if factory and is_object %} = field(default_factory={{ factory }}){% endif %}  # {{ ps.description | replace('\n', ' ') if ps.description else '' }}
{% endfor %}
{% for prop, ps in optional_props %}
    {% set is_object = ps.type == 'object' and not ps.name %}
    {{ prop }}: {{ get_type(ps, required=False) }}{% if is_object %} = field(default_factory=dict){% else %} = None{% endif %}  # {{ ps.description | replace('\n', ' ') if ps.description else '' }}
{% endfor %}
{% if not schema.properties %}
    # No properties defined in schema
    pass
{% endif %}
{% endif %}
'''


class ModelsEmitter:
    """Generates Python dataclass models from IRSpec using the visitor/context architecture."""

    def __init__(self, core_import_path: Optional[str] = None) -> None:
        self.formatter = Formatter()
        self.schema_names: Set[str] = set()
        self.visitor: Optional[ModelVisitor] = None
        self.core_import_path = core_import_path

    def emit(self, spec: IRSpec, output_dir: str) -> list[str]:
        """Render one model file per schema under <output_dir>/models using the visitor/context/registry pattern. Returns a list of generated file paths."""
        models_dir = os.path.join(output_dir, "models")
        context = RenderContext(core_import_path=self.core_import_path)
        context.file_manager.ensure_dir(models_dir)
        # Always create an empty __init__.py to ensure package
        empty_init_path = os.path.join(models_dir, "__init__.py")
        if not context.file_manager:
            raise RuntimeError("FileManager not set in RenderContext.")
        if not os.path.exists(empty_init_path):
            context.file_manager.write_file(empty_init_path, "")
        # Ensure py.typed marker for mypy
        pytyped_path = os.path.join(models_dir, "py.typed")
        if not os.path.exists(pytyped_path):
            context.file_manager.write_file(pytyped_path, "")

        # Store schema names for cross-references
        self.schema_names = {name for name in spec.schemas.keys() if name}

        # Create a single ModelVisitor with all schemas for correct type resolution
        if self.visitor is None:
            self.visitor = ModelVisitor(schemas=spec.schemas)

        # Prepare context and mark all generated modules
        for name in spec.schemas.keys():
            if not name:
                continue
            module_name = NameSanitizer.sanitize_module_name(name)
            file_path = os.path.join(models_dir, f"{module_name}.py")
            context.mark_generated_module(file_path)

        generated_files = []
        # Generate model files for all schemas
        for name, schema in spec.schemas.items():
            if not name:
                continue
            module_name = NameSanitizer.sanitize_module_name(name)
            file_path = os.path.join(models_dir, f"{module_name}.py")
            context = RenderContext(core_import_path=self.core_import_path)  # Create a new context for each file
            context.file_manager.ensure_dir(models_dir)
            context.mark_generated_module(file_path)
            context.set_current_file(file_path)
            # Render model code using the visitor (with schemas for type resolution)
            model_code = self.visitor.visit(schema, context)
            # Render imports for this file
            imports_code = context.render_imports(models_dir)
            file_content = imports_code + "\n\n" + model_code
            file_content = self.formatter.format(file_content)
            context.file_manager.write_file(file_path, file_content)
            generated_files.append(file_path)
        return generated_files
