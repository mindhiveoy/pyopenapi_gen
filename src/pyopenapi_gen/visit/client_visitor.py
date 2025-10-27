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
        # Step 1: Process tags and build tag_tuples
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

        # Step 2: Generate Protocol definition
        protocol_code = self.generate_client_protocol(spec, context, tag_tuples)

        # Step 3: Generate implementation class
        impl_code = self._generate_client_implementation(spec, context, tag_tuples)

        # Step 4: Combine Protocol and implementation
        return f"{protocol_code}\n\n\n{impl_code}"

    def _generate_client_implementation(
        self, spec: IRSpec, context: RenderContext, tag_tuples: list[tuple[str, str, str]]
    ) -> str:
        """
        Generate the APIClient implementation class.

        Args:
            spec: The IR specification
            context: Render context for import management
            tag_tuples: List of (tag_name, class_name, module_name) tuples

        Returns:
            Implementation class code as string
        """
        writer = CodeWriter()
        # Register all endpoint client imports using relative imports (endpoints are within the same package)
        for _, class_name, module_name in tag_tuples:
            # Use relative imports for endpoints since they're part of the same generated package
            # Import both the implementation and the Protocol
            protocol_name = f"{class_name}Protocol"
            context.import_collector.add_relative_import(f".endpoints.{module_name}", class_name)
            context.import_collector.add_relative_import(f".endpoints.{module_name}", protocol_name)

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

        context.add_typing_imports_for_type("HttpTransport | None")
        context.add_typing_imports_for_type("Any")
        context.add_typing_imports_for_type("Dict")
        # Class definition - implements Protocol
        writer.write_line("class APIClient(APIClientProtocol):")
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
            ("transport", "HttpTransport | None", "Custom HTTP transport (optional)."),
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
        writer.write_line("def __init__(self, config: ClientConfig, transport: HttpTransport | None = None) -> None:")
        writer.indent()
        writer.write_line("self.config = config")
        writer.write_line(
            "self.transport = transport if transport is not None else "
            "HttpxTransport(str(config.base_url), config.timeout)"
        )
        writer.write_line("self._base_url: str = str(self.config.base_url)")
        # Initialize private fields for each tag client
        for tag, class_name, module_name in tag_tuples:
            context.add_typing_imports_for_type(f"{class_name} | None")
            writer.write_line(f"self._{module_name}: {class_name} | None = None")
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
            "async def __aexit__(self, exc_type: type[BaseException] | None, "
            "exc_val: BaseException | None, exc_tb: object | None) -> None:"
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

    def generate_client_protocol(
        self, spec: IRSpec, context: RenderContext, tag_tuples: list[tuple[str, str, str]]
    ) -> str:
        """
        Generate APIClientProtocol defining the client interface.

        Args:
            spec: The IR specification
            context: Render context for import management
            tag_tuples: List of (tag_name, class_name, module_name) tuples

        Returns:
            Protocol class code as string with:
            - Tag-based endpoint properties
            - Standard methods (request, close, __aenter__, __aexit__)
        """
        # Register Protocol imports
        context.add_typing_imports_for_type("Protocol")
        context.add_import("typing", "runtime_checkable")
        context.add_typing_imports_for_type("Any")

        writer = CodeWriter()

        # Protocol class header
        writer.write_line("@runtime_checkable")
        writer.write_line("class APIClientProtocol(Protocol):")
        writer.indent()

        # Docstring
        writer.write_line('"""Protocol defining the interface of APIClient for dependency injection."""')
        writer.write_line("")

        # Tag-based endpoint properties
        for tag, class_name, module_name in tag_tuples:
            # Use forward reference for tag client protocol
            protocol_name = f"{class_name}Protocol"
            writer.write_line("@property")
            writer.write_line(f"def {module_name}(self) -> '{protocol_name}':")
            writer.indent()
            writer.write_line("...")
            writer.dedent()
            writer.write_line("")

        # Standard methods
        # request method
        writer.write_line("async def request(self, method: str, url: str, **kwargs: Any) -> Any:")
        writer.indent()
        writer.write_line("...")
        writer.dedent()
        writer.write_line("")

        # close method
        writer.write_line("async def close(self) -> None:")
        writer.indent()
        writer.write_line("...")
        writer.dedent()
        writer.write_line("")

        # __aenter__ method
        writer.write_line("async def __aenter__(self) -> 'APIClientProtocol':")
        writer.indent()
        writer.write_line("...")
        writer.dedent()
        writer.write_line("")

        # __aexit__ method
        context.add_typing_imports_for_type("type[BaseException] | None")
        context.add_typing_imports_for_type("BaseException | None")
        context.add_typing_imports_for_type("object | None")
        writer.write_line(
            "async def __aexit__(self, exc_type: type[BaseException] | None, "
            "exc_val: BaseException | None, exc_tb: object | None) -> None:"
        )
        writer.indent()
        writer.write_line("...")
        writer.dedent()

        writer.dedent()  # Close class
        return writer.get_code()

    def generate_client_mock_class(
        self, spec: IRSpec, context: RenderContext, tag_tuples: list[tuple[str, str, str]]
    ) -> str:
        """
        Generate MockAPIClient for testing.

        Args:
            spec: The IR specification
            context: Render context for import management
            tag_tuples: List of (tag, class_name, module_name) tuples

        Returns:
            Mock client class code as string
        """
        # Import TYPE_CHECKING for Protocol imports
        context.add_import("typing", "TYPE_CHECKING")
        context.add_import("typing", "Any")

        writer = CodeWriter()

        # TYPE_CHECKING imports
        writer.write_line("if TYPE_CHECKING:")
        writer.indent()
        writer.write_line("from ..client import APIClientProtocol")
        for tag, class_name, module_name in tag_tuples:
            protocol_name = f"{class_name}Protocol"
            writer.write_line(f"from ..endpoints.{module_name} import {protocol_name}")
        writer.dedent()
        writer.write_line("")

        # Import mock endpoint classes
        for tag, class_name, module_name in tag_tuples:
            mock_class_name = f"Mock{class_name}"
            writer.write_line(f"from .endpoints.mock_{module_name} import {mock_class_name}")
        writer.write_line("")

        # Class definition
        writer.write_line("class MockAPIClient:")
        writer.indent()

        # Docstring
        writer.write_line('"""')
        writer.write_line("Mock implementation of APIClient for testing.")
        writer.write_line("")
        writer.write_line("Auto-creates default mock implementations for all tag-based endpoint clients.")
        writer.write_line("You can override specific tag clients by passing them to the constructor.")
        writer.write_line("")
        writer.write_line("Example:")
        writer.write_line("    # Use all defaults")
        writer.write_line("    client = MockAPIClient()")
        writer.write_line("")
        writer.write_line("    # Override specific tag client")
        for tag, class_name, module_name in tag_tuples[:1]:  # Show example with first tag
            mock_class_name = f"Mock{class_name}"
            writer.write_line(f"    class My{class_name}Mock({mock_class_name}):")
            writer.write_line("        async def method_name(self, ...) -> ReturnType:")
            writer.write_line("            return test_data")
            writer.write_line("")
            writer.write_line(f"    client = MockAPIClient({module_name}=My{class_name}Mock())")
            break
        writer.write_line('"""')
        writer.write_line("")

        # Constructor
        writer.write_line("def __init__(")
        writer.indent()
        writer.write_line("self,")
        for tag, class_name, module_name in tag_tuples:
            protocol_name = f"{class_name}Protocol"
            writer.write_line(f'{module_name}: "{protocol_name} | None" = None,')
        writer.dedent()
        writer.write_line(") -> None:")
        writer.indent()

        # Initialize tag clients
        for tag, class_name, module_name in tag_tuples:
            mock_class_name = f"Mock{class_name}"
            writer.write_line(
                f"self._{module_name} = {module_name} if {module_name} is not None else {mock_class_name}()"
            )
        writer.dedent()
        writer.write_line("")

        # Properties for tag clients
        for tag, class_name, module_name in tag_tuples:
            protocol_name = f"{class_name}Protocol"
            writer.write_line("@property")
            writer.write_line(f'def {module_name}(self) -> "{protocol_name}":')
            writer.indent()
            writer.write_line(f"return self._{module_name}")
            writer.dedent()
            writer.write_line("")

        # request() method
        writer.write_line("async def request(self, method: str, url: str, **kwargs: Any) -> Any:")
        writer.indent()
        writer.write_line('"""')
        writer.write_line("Mock request method - raises NotImplementedError.")
        writer.write_line("")
        writer.write_line("This is a low-level method - consider using tag-specific methods instead.")
        writer.write_line('"""')
        writer.write_line(
            "raise NotImplementedError("
            '"MockAPIClient.request() not implemented. '
            'Use tag-specific methods instead."'
            ")"
        )
        writer.dedent()
        writer.write_line("")

        # close() method
        writer.write_line("async def close(self) -> None:")
        writer.indent()
        writer.write_line('"""Mock close method - no-op for testing."""')
        writer.write_line("pass  # No cleanup needed for mocks")
        writer.dedent()
        writer.write_line("")

        # __aenter__() method
        writer.write_line('async def __aenter__(self) -> "APIClientProtocol":')
        writer.indent()
        writer.write_line('"""Enter async context manager."""')
        writer.write_line("return self")
        writer.dedent()
        writer.write_line("")

        # __aexit__() method
        writer.write_line(
            "async def __aexit__("
            "self, "
            "exc_type: type[BaseException] | None, "
            "exc_val: BaseException | None, "
            "exc_tb: object | None"
            ") -> None:"
        )
        writer.indent()
        writer.write_line('"""Exit async context manager - no-op for mocks."""')
        writer.write_line("pass  # No cleanup needed for mocks")
        writer.dedent()

        writer.dedent()  # Close class
        return writer.get_code()
