import os

from pyopenapi_gen import IRSpec, IRParameter, IRRequestBody
from ..core.utils import NameSanitizer, Formatter
from ..visit.endpoint_visitor import EndpointVisitor
from pyopenapi_gen.context.render_context import RenderContext

# Basic OpenAPI schema to Python type mapping for parameters
PARAM_TYPE_MAPPING = {
    "integer": "int",
    "number": "float",
    "boolean": "bool",
    "string": "str",
    "array": "List",
    "object": "Dict[str, Any]",
}
# Format-specific overrides
PARAM_FORMAT_MAPPING = {
    "int32": "int",
    "int64": "int",
    "float": "float",
    "double": "float",
    "byte": "str",
    "binary": "bytes",
    "date": "date",
    "date-time": "datetime",
}

# Default tag for untagged operations
DEFAULT_TAG = "default"


def schema_to_type(schema: IRParameter) -> str:
    """Convert an IRParameter's schema to a Python type string."""
    s = schema.schema
    # Format-specific override
    if s.format in PARAM_FORMAT_MAPPING:
        return PARAM_FORMAT_MAPPING[s.format]
    # Handle case where s.type is a list (nullable types)
    s_type = s.type
    is_nullable = False
    if isinstance(s_type, list):
        types = [t for t in s_type if t != "null"]
        is_nullable = "null" in s_type
        s_type = types[0] if types else None
    # Array handling
    if s_type == "array" and s.items:
        item_type = schema_to_type(
            IRParameter(name="", in_="", required=False, schema=s.items)
        )
        py_type = f"List[{item_type}]"
    # Default mapping
    elif s_type in PARAM_TYPE_MAPPING:
        py_type = PARAM_TYPE_MAPPING[s_type]
    else:
        py_type = "Any"
    # If nullable, wrap with Optional
    if is_nullable:
        py_type = f"Optional[{py_type}]"
    return py_type


def _get_request_body_type(body: IRRequestBody) -> str:
    """Determine the Python type for a request body schema."""
    for mt, sch in body.content.items():
        if "json" in mt.lower():
            return schema_to_type(
                IRParameter(name="body", in_="body", required=body.required, schema=sch)
            )
    # Fallback to generic dict
    return "Dict[str, Any]"


class EndpointsEmitter:
    """Generates endpoint modules organized by tag from IRSpec using the visitor/context architecture."""

    def __init__(self) -> None:
        self.formatter = Formatter()
        self.visitor = EndpointVisitor()

    def emit(self, spec: IRSpec, output_dir: str) -> None:
        """Render endpoint client files per tag under <output_dir>/endpoints using the visitor/context/registry pattern."""
        endpoints_dir = os.path.join(output_dir, "endpoints")
        context = RenderContext()
        context.file_manager.ensure_dir(endpoints_dir)
        # Always create an empty __init__.py to ensure package
        empty_init_path = os.path.join(endpoints_dir, "__init__.py")
        if not os.path.exists(empty_init_path):
            context.file_manager.write_file(empty_init_path, "")
        # Ensure root __init__.py for output_dir
        root_init_path = os.path.join(output_dir, "__init__.py")
        if not os.path.exists(root_init_path):
            context.file_manager.write_file(root_init_path, "")
        # Ensure py.typed marker for mypy
        pytyped_path = os.path.join(endpoints_dir, "py.typed")
        if not os.path.exists(pytyped_path):
            context.file_manager.write_file(pytyped_path, "")

        # Group operations by tag
        tag_to_ops = {}
        for op in spec.operations:
            tags = op.tags or ["default"]
            for tag in tags:
                tag_to_ops.setdefault(tag, []).append(op)

        # Prepare context and mark all generated modules
        for tag in tag_to_ops:
            module_name = NameSanitizer.sanitize_module_name(tag)
            file_path = os.path.join(endpoints_dir, f"{module_name}.py")
            context.mark_generated_module(file_path)

        # Generate endpoint files per tag
        for tag, ops in tag_to_ops.items():
            module_name = NameSanitizer.sanitize_module_name(tag)
            file_path = os.path.join(endpoints_dir, f"{module_name}.py")
            context.set_current_file(file_path)
            # Render all methods for this tag
            methods = [self.visitor.visit(op, context) for op in ops]
            # Compose class content
            class_content = self.visitor.emit_endpoint_client_class(
                tag, methods, context
            )
            # Render imports for this file
            imports_code = context.render_imports(endpoints_dir)
            print(f"[DEBUG] Imports for {file_path}:\n{imports_code}")
            file_content = imports_code + "\n\n" + class_content
            # file_content = self.formatter.format(file_content)
            context.file_manager.write_file(file_path, file_content)
