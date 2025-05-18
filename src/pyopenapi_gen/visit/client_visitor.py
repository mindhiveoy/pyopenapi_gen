import logging  # Added for logging
import re
import textwrap
from typing import TYPE_CHECKING, cast

from pyopenapi_gen import IRSpec

from ..context.render_context import RenderContext
from ..core.utils import NameSanitizer
from ..core.writers.code_writer import CodeWriter
from ..core.writers.documentation_writer import DocumentationBlock, DocumentationWriter

if TYPE_CHECKING:
    # To prevent circular imports if any type from core itself is needed for hints
    pass

logger = logging.getLogger(__name__)  # Added for logging


class ClientVisitor:
    """Visitor for rendering the Python API client from IRSpec."""

    def __init__(self) -> None:
        pass

    def visit(self, spec: IRSpec, context: RenderContext) -> str:
        tag_candidates: dict[str, list[str]] = {}
        for op in spec.operations:
            # Use DEFAULT_TAG consistent with EndpointsEmitter
            tags = op.tags or ["default"]  # Use literal "default" here
            # Loop through the determined tags (original or default)
            for tag in tags:
                key = NameSanitizer.normalize_tag_key(tag)
                if key not in tag_candidates:
                    tag_candidates[key] = []
                tag_candidates[key].append(tag)
            # Ensure the old logic is removed (idempotent if already gone)
            # if op.tags:
            #     ...
            # else:
            #     ...

        def tag_score(t: str) -> tuple[bool, int, int, str]:
            is_pascal = bool(re.search(r"[a-z][A-Z]", t)) or bool(re.search(r"[A-Z]{2,}", t))
            words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|[0-9]+", t)
            words += re.split(r"[_-]+", t)
            word_count = len([w for w in words if w])
            upper = sum(1 for c in t if c.isupper())
            return (is_pascal, word_count, upper, t)

        tag_map = {}
        for key, candidates in tag_candidates.items():
            best = max(candidates, key=tag_score)
            tag_map[key] = best
        tag_tuples = [
            (
                tag_map[key],
                NameSanitizer.sanitize_class_name(tag_map[key]) + "Client",
                NameSanitizer.sanitize_module_name(tag_map[key]),
            )
            for key in sorted(tag_map)
        ]
        writer = CodeWriter()
        # Register all endpoint client imports using context.add_import
        for _, class_name, module_name in tag_tuples:
            current_gen_pkg_name = context.get_current_package_name_for_generated_code()
            if not current_gen_pkg_name:
                logger.error(
                    f"[ClientVisitor] Could not determine generated package name from context. "
                    f"Cannot form fully qualified import for endpoints.{module_name}.{class_name}"
                )
                # Fallback or raise error - for now, attempt direct, which might fail later in mypy
                context.add_import(f"endpoints.{module_name}", class_name)
            else:
                logical_module_for_add_import = f"{current_gen_pkg_name}.endpoints.{module_name}"
                context.add_import(logical_module_for_add_import, class_name)

        # Register core/config/typing imports for class signature
        # Use LOGICAL import path for core components

        # Use the core_package name from the context to form the base of the import path
        # RenderContext.add_import will handle making it relative correctly based on the current file.
        context.add_import(f"{context.core_package_name}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package_name}.http_transport", "HttpxTransport")
        context.add_import(f"{context.core_package_name}.config", "ClientConfig")
        # If security schemes are present and an auth plugin like ApiKeyAuth is used by the client itself,
        # it would also be registered here using context.core_package.
        # For now, the client_py_content check in the test looks for this for ApiKeyAuth specifically:
        context.add_import(f"{context.core_package_name}.auth.plugins", "ApiKeyAuth")

        context.add_typing_imports_for_type("Optional[HttpTransport]")
        context.add_typing_imports_for_type("Any")
        context.add_typing_imports_for_type("Dict")
        # Class definition
        writer.write_line("class APIClient:")
        writer.indent()
        # Build docstring for APIClient
        docstring_lines = []
        # Add API title and version
        docstring_lines.append(f"{spec.title} (version {spec.version})")
        # Add API description if present
        if getattr(spec, "description", None):
            desc = spec.description
            if desc is not None:
                # Remove triple quotes, escape backslashes, and dedent
                desc_clean = desc.replace('"""', "'").replace("'''", "'").replace("\\", "\\\\").strip()
                desc_clean = textwrap.dedent(desc_clean)
                docstring_lines.append("")
                docstring_lines.append(desc_clean)
        # Add a blank line before the generated summary/args
        docstring_lines.append("")
        summary = "Async API client with pluggable transport, tag-specific clients, and client-level headers."
        args: list[tuple[str, str, str]] = [
            ("config", "ClientConfig", "Client configuration object."),
            ("transport", "Optional[HttpTransport]", "Custom HTTP transport (optional)."),
        ]
        for tag, class_name, module_name in tag_tuples:
            args.append((module_name, class_name, f"Client for '{tag}' endpoints."))
        doc_block = DocumentationBlock(
            summary=summary,
            args=cast(list[tuple[str, str, str] | tuple[str, str]], args),
        )
        docstring = DocumentationWriter(width=88).render_docstring(doc_block, indent=0)
        docstring_lines.extend([line for line in docstring.splitlines()])
        # Write only one docstring, no extra triple quotes after
        writer.write_line('"""')  # At class indent (1)
        writer.dedent()  # Go to indent 0 for docstring content
        for line in docstring_lines:
            writer.write_line(line.rstrip('"'))
        writer.indent()  # Back to class indent (1)
        writer.write_line('"""')
        # __init__
        writer.write_line(
            "def __init__(self, config: ClientConfig, transport: Optional[HttpTransport] = None) -> None:"
        )
        writer.indent()
        writer.write_line("self.config = config")
        writer.write_line(
            "self.transport = transport if transport is not None else HttpxTransport(str(config.base_url), config.timeout)"
        )
        writer.write_line("self._base_url: str = str(self.config.base_url)")
        # Initialize private fields for each tag client
        for tag, class_name, module_name in tag_tuples:
            context.add_typing_imports_for_type(f"Optional[{class_name}]")
            writer.write_line(f"self._{module_name}: Optional[{class_name}] = None")
        writer.dedent()
        writer.write_line("")
        # @property for each tag client
        for tag, class_name, module_name in tag_tuples:
            writer.write_line(f"@property")
            # Use context.add_import here too
            current_gen_pkg_name_prop = context.get_current_package_name_for_generated_code()
            if not current_gen_pkg_name_prop:
                logger.error(
                    f"[ClientVisitor Property] Could not determine generated package name from context. "
                    f"Cannot form fully qualified import for endpoints.{module_name}.{class_name}"
                )
                # Fallback or raise error
                context.add_import(f"endpoints.{module_name}", class_name)
            else:
                logical_module_for_add_import_prop = f"{current_gen_pkg_name_prop}.endpoints.{module_name}"
                context.add_import(logical_module_for_add_import_prop, class_name)

            writer.write_line(f"def {module_name}(self) -> {class_name}:")
            writer.indent()
            writer.write_line(f'"""Client for \'{tag}\' endpoints."""')
            writer.write_line(f"if self._{module_name} is None:")
            writer.indent()
            writer.write_line(f"self._{module_name} = {class_name}(self.transport, self._base_url)")
            writer.dedent()
            writer.write_line(f"return self._{module_name}")
            writer.dedent()
            writer.write_line("")
        # request method
        context.add_typing_imports_for_type("Any")
        writer.write_line("async def request(self, method: str, url: str, **kwargs: Any) -> Any:")
        writer.indent()
        writer.write_line('"""Send an HTTP request via the transport."""')
        writer.write_line("return await self.transport.request(method, url, **kwargs)")
        writer.dedent()
        writer.write_line("")
        # close method
        context.add_typing_imports_for_type("None")
        writer.write_line("async def close(self) -> None:")
        writer.indent()
        writer.write_line('"""Close the underlying transport if supported."""')
        writer.write_line("if hasattr(self.transport, 'close'):")
        writer.indent()
        writer.write_line("await self.transport.close()")
        writer.dedent()
        writer.write_line("else:")
        writer.indent()
        writer.write_line("pass  # Or log a warning if close is expected but not found")
        writer.dedent()
        writer.dedent()
        writer.write_line("")
        # __aenter__ for async context management (dedented)
        writer.write_line("async def __aenter__(self) -> 'APIClient':")
        writer.indent()
        writer.write_line('"""Enter the async context manager. Returns self."""')
        writer.write_line("if hasattr(self.transport, '__aenter__'):")
        writer.indent()
        writer.write_line("await self.transport.__aenter__()")
        writer.dedent()
        writer.write_line("return self")
        writer.dedent()
        writer.write_line("")
        # __aexit__ for async context management (dedented)
        context.add_typing_imports_for_type("type[BaseException] | None")
        context.add_typing_imports_for_type("BaseException | None")
        context.add_typing_imports_for_type("object | None")
        writer.write_line(
            "async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object | None) -> None:"
        )
        writer.indent()
        writer.write_line('"""Exit the async context manager, ensuring transport is closed."""')
        # Close internal transport if it supports __aexit__
        writer.write_line("if hasattr(self.transport, '__aexit__'):")
        writer.indent()
        writer.write_line("await self.transport.__aexit__(exc_type, exc_val, exc_tb)")
        writer.dedent()
        writer.write_line("else:")  # Fallback if transport doesn't have __aexit__ but has close()
        writer.indent()
        writer.write_line("await self.close()")
        writer.dedent()
        writer.dedent()
        writer.write_line("")

        # Ensure crucial core imports are present before final rendering
        # This is a fallback / re-emphasis due to potential issues with ImportCollector
        context.add_import(f"{context.core_package_name}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package_name}.http_transport", "HttpxTransport")
        context.add_import(f"{context.core_package_name}.config", "ClientConfig")

        return writer.get_code()
