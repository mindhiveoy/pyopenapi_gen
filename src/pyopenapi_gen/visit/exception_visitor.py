from pyopenapi_gen import IRSpec

from ..context.render_context import RenderContext
from ..core.writers.python_construct_renderer import PythonConstructRenderer


class ExceptionVisitor:
    """Visitor for rendering exception alias classes from IRSpec."""

    def __init__(self) -> None:
        self.renderer = PythonConstructRenderer()

    def visit(self, spec: IRSpec, context: RenderContext) -> tuple[str, list[str]]:
        # Register base exception imports
        context.add_import(f"{context.core_package_name}.exceptions", "HTTPError")
        context.add_import(f"{context.core_package_name}.exceptions", "ClientError")
        context.add_import(f"{context.core_package_name}.exceptions", "ServerError")
        context.add_import("httpx", "Response")

        # Collect unique numeric status codes
        codes = sorted(
            {int(resp.status_code) for op in spec.operations for resp in op.responses if resp.status_code.isdigit()}
        )

        all_exception_code = []
        generated_alias_names = []

        # Use renderer to generate each exception class
        for code in codes:
            base_class = "ClientError" if code < 500 else "ServerError"
            class_name = f"Error{code}"
            generated_alias_names.append(class_name)
            docstring = f"Exception alias for HTTP {code} responses."

            # Define the __init__ method body
            init_method_body = [
                "def __init__(self, response: Response) -> None:",
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

        # Join the generated class strings
        final_code = "\n".join(all_exception_code)
        return final_code, generated_alias_names
