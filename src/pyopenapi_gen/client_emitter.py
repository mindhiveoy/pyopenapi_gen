from jinja2 import Environment, Template
import os

from . import IRSpec
from .utils import (
    ImportCollector,
    NameSanitizer,
)  # import collector and sanitization helper

# NOTE: ClientConfig and transports are only referenced in template strings, not at runtime
# hence we avoid importing config and http_transport modules to prevent runtime errors

# Template for client configuration file
CLIENT_CONFIG_TEMPLATE = '''
import os
import toml
from typing import Optional

class ClientConfig:
    """Configuration for the API client; supports env-var & TOML layering."""

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None) -> None:
        # Load defaults from TOML config
        cfg: dict = {}
        path = os.path.expanduser('~/.config/pyopenapi-gen.toml')
        if os.path.exists(path):
            try:
                cfg = toml.load(path).get('client', {})
            except Exception:
                pass
        # Environment overrides
        env_base = os.getenv('PYOPENAPI_BASE_URL')
        env_timeout = os.getenv('PYOPENAPI_TIMEOUT')
        # Resolve values: parameter -> env -> toml -> default
        self.base_url = base_url or env_base or cfg.get('base_url')
        self.timeout = (
            timeout
            if timeout is not None
            else (float(env_timeout) if env_timeout else cfg.get('timeout', 10.0))
        )
'''

# Jinja template for base async client file with tag-specific clients
CLIENT_TEMPLATE = '''
from typing import Optional, Any
{% for tag in tags %}
from .endpoints.{{ tag | sanitize_module_name }} import {{ tag | sanitize_tag_class_name }}
{% endfor %}
from pyopenapi_gen.http_transport import HttpTransport, HttpxTransport

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
        # Initialize tag clients for code completion and typing
{% for tag in tags %}
        self.{{ tag | sanitize_module_name }} = {{ tag | sanitize_tag_class_name }}(
            self.transport, self.config.base_url
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
    """Generates core client files (config.py, client.py) from IRSpec."""

    def __init__(self) -> None:
        self.env = Environment()
        # Register sanitization filters for client template
        self.env.filters["sanitize_module_name"] = NameSanitizer.sanitize_module_name
        self.env.filters["sanitize_class_name"] = NameSanitizer.sanitize_class_name
        self.env.filters["sanitize_tag_class_name"] = (
            NameSanitizer.sanitize_tag_class_name
        )

    def emit(self, spec: IRSpec, output_dir: str) -> None:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        # Write config.py (static template)
        config_path = os.path.join(output_dir, "config.py")
        with open(config_path, "w") as f:
            f.write(CLIENT_CONFIG_TEMPLATE)

        # Generate client.py with organized imports
        imports = ImportCollector()
        # Standard typing imports
        imports.add_import("typing", "Any")
        imports.add_import("typing", "Optional")
        # Relative imports for client core
        imports.add_relative_import(".config", "ClientConfig")
        imports.add_direct_import("pyopenapi_gen.http_transport", "HttpTransport")
        imports.add_direct_import("pyopenapi_gen.http_transport", "HttpxTransport")
        # Prepare tag list for client attributes, deduplicated by normalized key
        tag_map = {}
        for op in spec.operations:
            if op.tags:
                for tag in op.tags:
                    key = NameSanitizer.normalize_tag_key(tag)
                    if key not in tag_map:
                        tag_map[key] = tag
            else:
                fallback = op.path.strip("/").split("/")[0] or "root"
                key = NameSanitizer.normalize_tag_key(fallback)
                if key not in tag_map:
                    tag_map[key] = fallback
        tags = [tag_map[key] for key in sorted(tag_map)]
        # Render client.py using Jinja template with actual tags
        tpl = self.env.from_string(CLIENT_TEMPLATE)
        client_body = tpl.render(tags=tags)
        # Combine imports and rendered client template
        client_content = imports.get_formatted_imports() + "\n\n" + client_body
        client_path = os.path.join(output_dir, "client.py")
        with open(client_path, "w") as f:
            f.write(client_content)
