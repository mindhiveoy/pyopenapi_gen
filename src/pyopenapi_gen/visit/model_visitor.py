from pyopenapi_gen import IRSchema
from .visitor import Visitor
from pyopenapi_gen.context.render_context import RenderContext
from ..core.utils import Formatter, CodeWriter
from typing import Optional


class ModelVisitor(Visitor[IRSchema, str]):
    """
    Visitor for rendering a Python model (dataclass or enum) from an IRSchema.
    Returns the rendered code as a string (does not write files).
    Only adds imports/types to the context if they are actually used in the rendered code for the module.
    """

    def __init__(self) -> None:
        self.formatter = Formatter()

    def visit_IRSchema(self, schema: IRSchema, context: RenderContext) -> str:
        # Enum detection
        is_enum = schema.enum and schema.type in ("string", "integer")
        if is_enum:
            context.add_import("enum", "Enum")
        # Dataclass detection
        if not is_enum:
            context.add_import("dataclasses", "dataclass")
        # Analyze properties for type usage and add imports as needed
        self._analyze_and_register_imports(schema, context)
        # Mark this module as generated (assume context.current_file is set)
        if context.current_file:
            context.mark_generated_module(context.current_file)
        # Generate code using CodeWriter
        writer = CodeWriter()
        if is_enum:
            # Enum class
            base = "str" if schema.type == "string" else "int"
            writer.write_line(f"class {schema.name}(" + base + ", Enum):")
            writer.indent()
            if schema.description:
                writer.write_line('"""')
                for line in schema.description.splitlines():
                    writer.write_line(line)
                writer.write_line('"""')
            for val in schema.enum:
                if schema.type == "string":
                    name = val.upper().replace("-", "_").replace(" ", "_")
                    writer.write_line(f'{name} = "{val}"')
                elif schema.type == "integer":
                    if isinstance(val, str):
                        name = val.replace("-", "_").replace(" ", "_").upper()
                        writer.write_line(f"{name} = {val}")
                    else:
                        writer.write_line(f"_{val} = {val}")
            writer.dedent()
        else:
            # Dataclass
            writer.write_line("@dataclass")
            writer.write_line(f"class {schema.name}:")
            writer.indent()
            if schema.description:
                writer.write_line('"""')
                for line in schema.description.splitlines():
                    writer.write_line(line)
                writer.write_line('"""')
            required_props = []
            optional_props = []
            for prop, ps in schema.properties.items():
                if prop in schema.required:
                    required_props.append((prop, ps))
                else:
                    optional_props.append((prop, ps))
            # Emit required fields first (no default values)
            for prop, ps in required_props:
                is_object = ps.type == "object" and not ps.name
                py_type = self._get_python_type(ps, required=True)
                line = f"{prop}: {py_type}"
                if ps.description:
                    line += f"  # {ps.description.replace('\n', ' ')}"
                writer.write_line(line)
            # Then emit optional fields (with defaults)
            for prop, ps in optional_props:
                is_object = ps.type == "object" and not ps.name
                py_type = self._get_python_type(ps, required=False)
                line = f"{prop}: {py_type}"
                if is_object:
                    line += " = field(default_factory=dict)"
                else:
                    line += " = None"
                if ps.description:
                    line += f"  # {ps.description.replace('\n', ' ')}"
                writer.write_line(line)
            if not schema.properties:
                writer.write_line("# No properties defined in schema")
                writer.write_line("pass")
            writer.dedent()
        return self.formatter.format(writer.get_code())

    def _analyze_and_register_imports(
        self, schema: IRSchema, context: RenderContext
    ) -> None:
        for prop, ps in schema.properties.items():
            # Optional if not required
            if prop not in schema.required:
                context.add_import("typing", "Optional")
            # List if array
            if ps.type == "array":
                context.add_import("typing", "List")
            # Dict if object
            if ps.type == "object":
                context.add_import("typing", "Dict")
            # field if default_factory is needed
            if (ps.type == "object" and not ps.name) or ps.type == "array":
                context.add_import("dataclasses", "field")
            # Any if type is unknown
            context.add_typing_imports_for_type(self._get_python_type(ps))
            # --- Recursive registration for nested schemas ---
            if ps.type == "array" and ps.items:
                self._analyze_and_register_imports(ps.items, context)
            if ps.type == "object" and ps.properties:
                self._analyze_and_register_imports(ps, context)

    def _get_python_type(self, schema: IRSchema, required: bool = True) -> str:
        # Simplified: always use Any for unknowns
        if not schema:
            return "Any"
        if schema.type == "array" and schema.items:
            item_type = self._get_python_type(schema.items)
            py_type = f"List[{item_type}]"
        elif schema.type == "object" and schema.properties:
            py_type = "Dict[str, Any]"
        elif schema.type in ("integer", "number", "boolean", "string"):
            py_type = {
                "integer": "int",
                "number": "float",
                "boolean": "bool",
                "string": "str",
            }[schema.type]
        else:
            py_type = "Any"
        if not required:
            py_type = f"Optional[{py_type}]"
        return py_type

    def _get_default_factory(self, prop: IRSchema) -> Optional[str]:
        if prop.type == "array":
            return "list"
        if prop.type == "object":
            return "dict"
        return None
