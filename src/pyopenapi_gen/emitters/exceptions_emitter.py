import os
from pyopenapi_gen import IRSpec
from ..visit.exception_visitor import ExceptionVisitor
from pyopenapi_gen.context.render_context import RenderContext

# Template for spec-specific exception aliases
EXCEPTIONS_ALIASES_TEMPLATE = '''
from .exceptions import HTTPError, ClientError, ServerError

# Generated exception aliases for specific status codes
{% for code in codes %}
class Error{{ code }}({% if code < 500 %}ClientError{% else %}ServerError{% endif %}):
    """Exception alias for HTTP {{ code }} responses."""
    pass
{% endfor %}
'''


class ExceptionsEmitter:
    """Generates spec-specific exception aliases in exceptions.py using visitor/context."""

    def __init__(self) -> None:
        self.visitor = ExceptionVisitor()

    def emit(self, spec: IRSpec, output_dir: str) -> list[str]:
        file_path = os.path.join(output_dir, "exceptions.py")
        context = RenderContext()
        context.mark_generated_module(file_path)
        context.set_current_file(file_path)
        # Render exception code using the visitor
        exception_code = self.visitor.visit(spec, context)
        # Render imports for this file
        imports_code = context.render_imports(output_dir)
        file_content = imports_code + "\n\n" + exception_code
        context.file_manager.write_file(file_path, file_content)
        return [file_path]
