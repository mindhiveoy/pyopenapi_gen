import re
import textwrap
from typing import cast

from pyopenapi_gen import IRSpec

from ..context.render_context import RenderContext
from ..core.utils import NameSanitizer
from ..core.writers.code_writer import CodeWriter
from ..core.writers.documentation_writer import DocumentationBlock, DocumentationWriter


class ClientVisitor:
    """Visitor for rendering the Python API client from IRSpec."""

    def __init__(self) -> None:
        pass

    def visit(self, spec: IRSpec, context: RenderContext) -> str:
        tag_candidates: dict[str, list[str]] = {}
        for op in spec.operations:
            if op.tags:
                for tag in op.tags:
                    key = NameSanitizer.normalize_tag_key(tag)
                    if key not in tag_candidates:
                        tag_candidates[key] = []
                    tag_candidates[key].append(tag)
            else:
                fallback = op.path.strip("/").split("/")[0] or "root"
                key = NameSanitizer.normalize_tag_key(fallback)
                if key not in tag_candidates:
                    tag_candidates[key] = []
                tag_candidates[key].append(fallback)

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
        # Register all endpoint client imports
        for _, class_name, module_name in tag_tuples:
            context.add_import(f"endpoints.{module_name}", class_name)
            writer.write_line(f"from .endpoints.{module_name} import {class_name}")
        writer.write_line("")
        # Register core/config/typing imports for class signature
        context.add_import(f"{context.core_package}.config", "ClientConfig")
        context.add_import(f"{context.core_package}.http_transport", "HttpTransport")
        context.add_import(f"{context.core_package}.http_transport", "HttpxTransport")
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
            context.add_import(f"endpoints.{module_name}", class_name)
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
        writer.write_line('"""Exit the async context manager. Calls close()."""')
        writer.write_line("if hasattr(self.transport, '__aexit__'):")
        writer.indent()
        writer.write_line("await self.transport.__aexit__(exc_type, exc_val, exc_tb)")
        writer.dedent()
        writer.write_line("else:")
        writer.indent()
        writer.write_line("await self.close()")
        writer.dedent()
        writer.dedent()
        writer.write_line("")
        return writer.get_code()
