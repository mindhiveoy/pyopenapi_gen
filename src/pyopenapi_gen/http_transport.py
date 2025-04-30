from typing import Any, Dict, Optional, Protocol

import httpx

from .auth.base import BaseAuth


class HttpTransport(Protocol):
    """
    Defines the interface for an asynchronous HTTP transport layer.

    This protocol allows different HTTP client implementations (like httpx, aiohttp)
    to be used interchangeably by the generated API client. It requires
    implementing classes to provide an async `request` method.

    All implementations must:
    - Provide a fully type-annotated async `request` method.
    - Return an `httpx.Response` object for all requests.
    - Be safe for use in async contexts.
    """

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Sends an asynchronous HTTP request.

        Args:
            method: The HTTP method (e.g., 'GET', 'POST').
            url: The target URL for the request.
            **kwargs: Additional keyword arguments for the HTTP client (e.g., headers, params, json, data).

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            Exception: Implementations may raise exceptions for network errors or invalid responses.
        """
        raise NotImplementedError()


class HttpxTransport:
    """
    A concrete implementation of the HttpTransport protocol using the `httpx` library.

    This class provides the default asynchronous HTTP transport mechanism for the
    generated API client. It wraps an `httpx.AsyncClient` instance to handle
    request sending, connection pooling, and resource management.

    Optionally supports authentication via a BaseAuth instance or a raw bearer token.

    Attributes:
        _client (httpx.AsyncClient): Configured HTTPX async client for all requests.
        _auth (Optional[BaseAuth]): Optional authentication plugin for request signing.
        _bearer_token (Optional[str]): Optional bearer token for Authorization header.
    """

    def __init__(
        self,
        base_url: str,
        timeout: Optional[float] = None,
        auth: Optional[BaseAuth] = None,
        bearer_token: Optional[str] = None,
    ) -> None:
        """
        Initializes the HttpxTransport.

        Args:
            base_url (str): The base URL for all API requests made through this transport.
            timeout (Optional[float]): The default timeout in seconds for requests. If None, httpx's default is used.
            auth (Optional[BaseAuth]): Optional authentication plugin for request signing.
            bearer_token (Optional[str]): Optional raw bearer token string for Authorization header.

        Note:
            If both auth and bearer_token are provided, auth takes precedence.
        """
        self._client: httpx.AsyncClient = httpx.AsyncClient(base_url=base_url, timeout=timeout)
        self._auth: Optional[BaseAuth] = auth
        self._bearer_token: Optional[str] = bearer_token

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Sends an asynchronous HTTP request using the underlying httpx.AsyncClient.

        Args:
            method (str): The HTTP method (e.g., 'GET', 'POST').
            url (str): The target URL path, relative to the `base_url` provided during initialization, or an absolute
            URL.
            **kwargs: Additional keyword arguments passed directly to `httpx.AsyncClient.request` (e.g., headers,
            params, json, data).

        Returns:
            httpx.Response: The HTTP response object from the server.

        Raises:
            httpx.HTTPError: For network errors or invalid responses.
        """
        # Prepare request arguments
        request_args: Dict[str, Any] = dict(kwargs)
        headers = request_args.get("headers", {})
        # Apply authentication
        if self._auth is not None:
            # Use the provided BaseAuth instance
            request_args = await self._auth.authenticate_request(request_args)
        elif self._bearer_token is not None:
            # Add Bearer token header
            headers = dict(headers)  # copy to avoid mutating input
            headers["Authorization"] = f"Bearer {self._bearer_token}"
            request_args["headers"] = headers
        return await self._client.request(method, url, **request_args)

    async def close(self) -> None:
        """
        Closes the underlying httpx.AsyncClient and releases resources.

        This should be called when the transport is no longer needed, typically
        when the main API client is being shut down, to ensure proper cleanup
        of network connections.
        """
        await self._client.aclose()
