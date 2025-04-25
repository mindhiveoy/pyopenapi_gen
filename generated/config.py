
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
