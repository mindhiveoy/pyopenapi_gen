import os
from typing import Optional

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.render_context import RenderContext

from ..visit.exception_visitor import ExceptionVisitor

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

    def __init__(self, core_package_name: str = "core", overall_project_root: Optional[str] = None) -> None:
        self.visitor = ExceptionVisitor()
        self.core_package_name = core_package_name
        self.overall_project_root = overall_project_root

    def emit(self, spec: IRSpec, output_dir: str) -> tuple[list[str], list[str]]:
        file_path = os.path.join(output_dir, "exception_aliases.py")

        context = RenderContext(
            package_root_for_generated_code=output_dir,
            core_package_name=self.core_package_name,
            overall_project_root=self.overall_project_root,
        )
        context.set_current_file(file_path)

        generated_code, alias_names = self.visitor.visit(spec, context)
        generated_imports = context.render_imports()

        # Add __all__ list
        if alias_names:
            all_list_str = ", ".join([f'"{name}"' for name in alias_names])
            all_assignment = f"\n\n__all__ = [{all_list_str}]\n"
            generated_code += all_assignment

        full_content = f"{generated_imports}\n\n{generated_code}"
        with open(file_path, "w") as f:
            f.write(full_content)
        return [file_path], alias_names
