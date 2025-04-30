import os
import traceback

from pyopenapi_gen import IRSpec
from pyopenapi_gen.context.render_context import RenderContext

from ..visit.client_visitor import ClientVisitor

# NOTE: ClientConfig and transports are only referenced in template strings, not at runtime
# hence we avoid importing config and http_transport modules to prevent runtime errors

# Jinja template for base async client file with tag-specific clients
CLIENT_TEMPLATE = '''
from typing import Optional, Any
{% for tag, class_name, module_name in tag_tuples %}
from .endpoints.{{ module_name }} import {{ class_name }}
{% endfor %}
from .config import ClientConfig
from .core.http_transport import HttpTransport, HttpxTransport

class APIClient:
    """Async API client with pluggable transport and tag-specific clients."""

    def __init__(
        self,
        config: ClientConfig,
        transport: Optional[HttpTransport] = None,
    ) -> None:
        self.config = config
        # Use provided transport or default to HttpxTransport (concrete class)
        self.transport = transport if transport is not None else HttpxTransport(
            config.base_url, config.timeout  # type: ignore[arg-type]
        )
        # Always extract the underlying AsyncClient for endpoint clients
        from httpx import AsyncClient
        if hasattr(self.transport, "_client") and isinstance(self.transport._client, AsyncClient):
            client = self.transport._client
        else:
            raise TypeError("Transport must provide an httpx.AsyncClient as _client for endpoint clients.")
        base_url: str = str(self.config.base_url)
{% for tag, class_name, module_name in tag_tuples %}
        self.{{ module_name }} = {{ class_name }}(
            client, base_url
        )
{% endfor %}

    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Send an HTTP request via the transport."""
        return await self.transport.request(method, url, **kwargs)

    async def close(self) -> None:
        """Close the underlying transport if supported."""
        if hasattr(self.transport, "close"):
            await self.transport.close()
'''


class ClientEmitter:
    """Generates core client files (client.py) from IRSpec using visitor/context."""

    def __init__(self, core_package: str = "core") -> None:
        self.visitor = ClientVisitor()
        self.core_package = core_package

    def emit(self, spec: IRSpec, output_dir: str) -> list[str]:
        error_log = "/tmp/pyopenapi_gen_error.log"
        generated_files = []
        try:
            os.makedirs(output_dir, exist_ok=True)
            # Remove config.py emission
            # Prepare context and mark generated client module
            client_path = os.path.join(output_dir, "client.py")
            context = RenderContext(core_package=self.core_package)
            context.mark_generated_module(client_path)
            context.set_current_file(client_path)
            # Render imports for this file
            imports_code = context.render_imports(output_dir)
            # Render client code using the visitor
            client_code = self.visitor.visit(spec, context)
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
