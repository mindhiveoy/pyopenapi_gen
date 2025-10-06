from pyopenapi_gen import IRSpec

from ..context.render_context import RenderContext
from ..core.http_status_codes import (
    get_exception_class_name,
    get_status_name,
    is_client_error,
    is_error_code,
    is_server_error,
)
from ..core.writers.python_construct_renderer import PythonConstructRenderer


class ExceptionVisitor:
    """Visitor for rendering exception alias classes from IRSpec.

    This visitor generates exception classes only for error status codes (4xx and 5xx).
    Success codes (2xx) are intentionally excluded as they represent successful responses.
    """

    def __init__(self) -> None:
        self.renderer = PythonConstructRenderer()

    def visit(self, spec: IRSpec, context: RenderContext) -> tuple[str, list[str], list[int]]:
        """Generate exception classes from IRSpec.

        Args:
            spec: The IRSpec containing operations and responses
            context: Render context for imports and code generation

        Returns:
            Tuple of (generated_code, exception_class_names, status_codes_list)
        """
        # Register base exception imports (only the ones we actually use)
        # Note: HTTPError is not used in exception_aliases.py, so we don't import it
        context.add_import("httpx", "Response")  # Third-party import first (Ruff I001)
        context.add_import(f"{context.core_package_name}.exceptions", "ClientError")
        context.add_import(f"{context.core_package_name}.exceptions", "ServerError")

        # Collect unique numeric error status codes (4xx and 5xx only)
        all_codes = {
            int(resp.status_code) for op in spec.operations for resp in op.responses if resp.status_code.isdigit()
        }
        error_codes = sorted([code for code in all_codes if is_error_code(code)])

        all_exception_code = []
        generated_alias_names = []

        # Use renderer to generate each exception class
        for code in error_codes:
            # Determine base class using helper functions
            if is_client_error(code):
                base_class = "ClientError"
            elif is_server_error(code):
                base_class = "ServerError"
            else:
                # Should not happen since we filtered to 4xx/5xx, but be defensive
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

            exception_code = self.renderer.render_class(
                class_name=class_name,
                base_classes=[base_class],
                docstring=docstring,
                body_lines=init_method_body,
                context=context,
            )
            all_exception_code.append(exception_code)

        # Join the generated class strings with 2 blank lines between classes (PEP 8 / Ruff E302)
        final_code = "\n\n\n".join(all_exception_code)
        return final_code, generated_alias_names, error_codes
