from typing import Any, Optional

from .core.config import ClientConfig
from .core.http_transport import HttpTransport, HttpxTransport
from .endpoints.default import DefaultClient


class APIClient:
    """
    Minimal Return Type Test Spec (version 1.0.0)


    Async API client with pluggable transport, tag-specific clients, and client-level
    headers.

    Args:
        config (ClientConfig)    : Client configuration object.
        transport (Optional[HttpTransport])
                                 : Custom HTTP transport (optional).
        default (DefaultClient)  : Client for 'default' endpoints.

    """

    def __init__(self, config: ClientConfig, transport: Optional[HttpTransport] = None) -> None:
        self.config = config
        self.transport = transport if transport is not None else HttpxTransport(str(config.base_url), config.timeout)
        self._base_url: str = str(self.config.base_url)
        self._default: Optional[DefaultClient] = None

    @property
    def default(self) -> DefaultClient:
        """Client for 'default' endpoints."""
        if self._default is None:
            self._default = DefaultClient(self.transport, self._base_url)
        return self._default

    async def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Send an HTTP request via the transport."""
        return await self.transport.request(method, url, **kwargs)

    async def close(self) -> None:
        """Close the underlying transport if supported."""
        if hasattr(self.transport, "close"):
            await self.transport.close()

    async def __aenter__(self) -> "APIClient":
        """Enter the async context manager. Returns self."""
        if hasattr(self.transport, "__aenter__"):
            await self.transport.__aenter__()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: object | None
    ) -> None:
        """Exit the async context manager. Calls close()."""
        if hasattr(self.transport, "__aexit__"):
            await self.transport.__aexit__(exc_type, exc_val, exc_tb)
        else:
            await self.close()
