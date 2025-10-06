import json
import os
from pathlib import Path
from typing import Optional

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.render_context import RenderContext

from ..visit.exception_visitor import ExceptionVisitor


class ExceptionsEmitter:
    """Generates spec-specific exception aliases with multi-client support.

    This emitter handles two scenarios:
    1. **Single client**: Generates exception_aliases.py directly in the core package
    2. **Shared core**: Maintains a registry of all needed exception codes across clients
       and regenerates the complete exception_aliases.py file

    The registry file (.exception_registry.json) tracks which status codes are used by
    which clients, ensuring that when multiple clients share a core package, all required
    exceptions are available.
    """

    def __init__(self, core_package_name: str = "core", overall_project_root: Optional[str] = None) -> None:
        self.visitor = ExceptionVisitor()
        self.core_package_name = core_package_name
        self.overall_project_root = overall_project_root

    def emit(
        self, spec: IRSpec, output_dir: str, client_package_name: Optional[str] = None
    ) -> tuple[list[str], list[str]]:
        """Generate exception aliases for the given spec.

        Args:
            spec: IRSpec containing operations and responses
            output_dir: Directory where exception_aliases.py will be written
            client_package_name: Name of the client package (for registry tracking)

        Returns:
            Tuple of (list of generated file paths, list of exception class names)
        """
        file_path = os.path.join(output_dir, "exception_aliases.py")
        registry_path = os.path.join(output_dir, ".exception_registry.json")

        context = RenderContext(
            package_root_for_generated_code=output_dir,
            core_package_name=self.core_package_name,
            overall_project_root=self.overall_project_root,
        )
        context.set_current_file(file_path)

        # Generate exception classes for this spec
        generated_code, alias_names, status_codes = self.visitor.visit(spec, context)

        # Update registry if we have a client package name (shared core scenario)
        if client_package_name and self._is_shared_core(output_dir):
            all_codes = self._update_registry(registry_path, client_package_name, status_codes)
            # Regenerate with ALL codes from registry
            generated_code, alias_names = self._generate_for_codes(all_codes, context)

        generated_imports = context.render_imports()

        alias_names.sort()

        # Add __all__ list with proper spacing (2 blank lines after last class - Ruff E305)
        if alias_names:
            all_list_str = ", ".join([f'"{name}"' for name in alias_names])
            all_assignment = f"\n\n\n__all__ = [{all_list_str}]\n"
            generated_code += all_assignment

        full_content = f"{generated_imports}\n\n{generated_code}"
        with open(file_path, "w") as f:
            f.write(full_content)

        return [file_path], alias_names

    def _is_shared_core(self, core_dir: str) -> bool:
        """Check if this core package is shared between multiple clients.

        Args:
            core_dir: Path to the core package directory

        Returns:
            True if the core package is outside the immediate client package
        """
        # If overall_project_root is set and different from the core dir's parent,
        # we're in a shared core scenario
        if self.overall_project_root:
            core_path = Path(core_dir).resolve()
            project_root = Path(self.overall_project_root).resolve()
            # Check if there are other client directories at the same level
            parent_dir = core_path.parent
            return parent_dir == project_root or parent_dir.parent == project_root
        return False

    def _update_registry(self, registry_path: str, client_name: str, status_codes: list[int]) -> list[int]:
        """Update the exception registry with this client's status codes.

        Args:
            registry_path: Path to the .exception_registry.json file
            client_name: Name of the client package
            status_codes: List of status codes used by this client

        Returns:
            Complete list of all status codes across all clients
        """
        registry = {}
        if os.path.exists(registry_path):
            with open(registry_path) as f:
                registry = json.load(f)

        # Update this client's codes
        registry[client_name] = sorted(status_codes)

        # Write back to registry
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2, sort_keys=True)

        # Return union of all codes
        all_codes = set()
        for codes in registry.values():
            all_codes.update(codes)

        return sorted(all_codes)

    def _generate_for_codes(self, status_codes: list[int], context: RenderContext) -> tuple[str, list[str]]:
        """Generate exception classes for a specific list of status codes.

        Args:
            status_codes: List of HTTP status codes to generate exceptions for
            context: Render context for imports

        Returns:
            Tuple of (generated_code, exception_class_names)
        """
        from ..core.http_status_codes import (
            get_exception_class_name,
            get_status_name,
            is_client_error,
            is_server_error,
        )
        from ..core.writers.python_construct_renderer import PythonConstructRenderer

        renderer = PythonConstructRenderer()
        all_exception_code = []
        generated_alias_names = []

        for code in status_codes:
            # Determine base class
            if is_client_error(code):
                base_class = "ClientError"
            elif is_server_error(code):
                base_class = "ServerError"
            else:
                continue

            # Get human-readable exception class name (e.g., NotFoundError instead of Error404)
            class_name = get_exception_class_name(code)
            generated_alias_names.append(class_name)

            # Get human-readable status name for documentation
            status_name = get_status_name(code)
            docstring = f"HTTP {code} {status_name}.\n\nRaised when the server responds with a {code} status code."

            # Define the __init__ method body
            init_method_body = [
                "def __init__(self, response: Response) -> None:",
                f'    """Initialise {class_name} with the HTTP response.',
                "",  # Empty line without trailing whitespace (Ruff W293)
                "    Args:",
                "        response: The httpx Response object that triggered this exception",
                '    """',
                "    super().__init__(status_code=response.status_code, message=response.text, response=response)",
            ]

            exception_code = renderer.render_class(
                class_name=class_name,
                base_classes=[base_class],
                docstring=docstring,
                body_lines=init_method_body,
                context=context,
            )
            all_exception_code.append(exception_code)

        # Join the generated class strings with 2 blank lines between classes (PEP 8 / Ruff E302)
        final_code = "\n\n\n".join(all_exception_code)
        return final_code, generated_alias_names
