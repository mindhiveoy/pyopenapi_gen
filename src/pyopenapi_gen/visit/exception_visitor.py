from pyopenapi_gen import IRSpec

from ..context.render_context import RenderContext
from ..core.writers.code_writer import CodeWriter


class ExceptionVisitor:
    """Visitor for rendering exception alias classes from IRSpec."""

    def __init__(self) -> None:
        pass

    def visit(self, spec: IRSpec, context: RenderContext) -> str:
        # Register imports needed for the exception aliases
        context.add_import(f"{context.core_package}.exceptions", "HTTPError")
        context.add_import(f"{context.core_package}.exceptions", "ClientError")
        context.add_import(f"{context.core_package}.exceptions", "ServerError")
        # Collect unique numeric status codes
        codes = sorted({
            int(resp.status_code) for op in spec.operations for resp in op.responses if resp.status_code.isdigit()
        })
        writer = CodeWriter()
        # Remove direct import emission; rely on context/import collector
        # writer.write_line("from .exceptions import HTTPError, ClientError, ServerError")
        writer.write_line("")
        writer.write_line("# Generated exception aliases for specific status codes")
        for code in codes:
            base = "ClientError" if code < 500 else "ServerError"
            writer.write_line(f"class Error{code}({base}):")
            writer.indent()
            writer.write_line(f'"""Exception alias for HTTP {code} responses."""')
            writer.write_line("pass")
            writer.dedent()
        return writer.get_code()
