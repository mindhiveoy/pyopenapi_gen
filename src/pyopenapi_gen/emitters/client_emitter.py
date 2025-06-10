import tempfile
import traceback
from pathlib import Path

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.render_context import RenderContext

from ..visit.client_visitor import ClientVisitor

# NOTE: ClientConfig and transports are only referenced in template strings, not at runtime
# hence we avoid importing config and http_transport modules to prevent runtime errors

# Jinja template for base async client file with tag-specific clients
# CLIENT_TEMPLATE = ''' ... removed ... '''


class ClientEmitter:
    """Generates core client files (client.py) from IRSpec using visitor/context."""

    def __init__(self, context: RenderContext) -> None:
        self.visitor = ClientVisitor()
        self.context = context

    def emit(self, spec: IRSpec, output_dir_str: str) -> list[str]:
        error_log = Path(tempfile.gettempdir()) / "pyopenapi_gen_error.log"
        generated_files = []
        try:
            output_dir_abs = Path(output_dir_str)
            output_dir_abs.mkdir(parents=True, exist_ok=True)

            client_path = output_dir_abs / "client.py"

            self.context.set_current_file(str(client_path))

            client_code = self.visitor.visit(spec, self.context)
            imports_code = self.context.render_imports()
            file_content = imports_code + "\n\n" + client_code

            self.context.file_manager.write_file(str(client_path), file_content)
            generated_files.append(str(client_path))

            pytyped_path = output_dir_abs / "py.typed"
            if not pytyped_path.exists():
                self.context.file_manager.write_file(str(pytyped_path), "")
            generated_files.append(str(pytyped_path))
            return generated_files
        except Exception as e:
            with open(error_log, "a") as f:
                f.write(f"ERROR in ClientEmitter.emit: {e}\n")
                f.write(traceback.format_exc())
            raise
