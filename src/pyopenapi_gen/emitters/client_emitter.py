import os
import traceback
from typing import Optional

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.render_context import RenderContext

from ..visit.client_visitor import ClientVisitor

# NOTE: ClientConfig and transports are only referenced in template strings, not at runtime
# hence we avoid importing config and http_transport modules to prevent runtime errors

# Jinja template for base async client file with tag-specific clients
# CLIENT_TEMPLATE = ''' ... removed ... '''


class ClientEmitter:
    """Generates core client files (client.py) from IRSpec using visitor/context."""

    def __init__(self, core_package: str = "core", overall_project_root: Optional[str] = None) -> None:
        self.visitor = ClientVisitor()
        self.core_package = core_package  # This is core_package_name
        self.overall_project_root = overall_project_root

    def emit(self, spec: IRSpec, output_dir: str) -> list[str]:
        error_log = "/tmp/pyopenapi_gen_error.log"
        generated_files = []
        try:
            os.makedirs(output_dir, exist_ok=True)
            # Remove config.py emission
            # Prepare context and mark generated client module
            client_path = os.path.join(output_dir, "client.py")
            context = RenderContext(
                core_package_name=self.core_package,
                package_root_for_generated_code=output_dir,
                overall_project_root=self.overall_project_root,
            )
            context.mark_generated_module(client_path)
            context.set_current_file(client_path)
            # Render client code using the visitor
            client_code = self.visitor.visit(spec, context)
            # Render imports for this file (AFTER visitor, so all types are registered)
            imports_code = context.render_imports()
            file_content = imports_code + "\n\n" + client_code
            context.file_manager.write_file(client_path, file_content)
            generated_files.append(client_path)
            # Ensure py.typed marker for mypy in the client package
            pytyped_path = os.path.join(output_dir, "py.typed")
            if not os.path.exists(pytyped_path):
                context.file_manager.write_file(pytyped_path, "")
            generated_files.append(pytyped_path)
            return generated_files
        except Exception as e:
            with open(error_log, "a") as f:
                f.write(f"ERROR in ClientEmitter.emit: {e}\n")
                f.write(traceback.format_exc())
            raise
