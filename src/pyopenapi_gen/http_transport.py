from typing import Protocol, Any, Optional
import httpx


class HttpTransport(Protocol):
    """
    Defines the interface for an asynchronous HTTP transport layer.

    This protocol allows different HTTP client implementations (like httpx, aiohttp)
    to be used interchangeably by the generated API client. It requires
    implementing classes to provide an async `request` method.
    """

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Sends an asynchronous HTTP request.

        Implementations should handle sending the request to the specified URL
        using the given HTTP method and any additional keyword arguments
        recognized by the underlying HTTP client library (e.g., headers, json, data).

        Args:
            method: The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
            url: The target URL for the request. Can be relative if the transport
                 was initialized with a base URL.
            **kwargs: Additional keyword arguments passed directly to the
                      underlying HTTP client's request method. Common arguments
                      include `headers`, `params`, `json`, `data`, `files`.

        Returns:
            An httpx.Response object (or a compatible response object from
            the underlying library if adapted) representing the server's response.
            The protocol definition uses `httpx.Response` for type hinting clarity,
            but implementations might return objects from other libraries if needed,
            provided they offer a compatible interface for accessing status code,
            headers, and body content.
        """
        ...  # Protocol methods have no implementation


class HttpxTransport:
    """
    A concrete implementation of the HttpTransport protocol using the `httpx` library.

    This class provides the default asynchronous HTTP transport mechanism for the
    generated API client. It wraps an `httpx.AsyncClient` instance to handle
    request sending, connection pooling, and resource management.

    Attributes:
        _client: An instance of `httpx.AsyncClient` configured with the base URL
                 and timeout.
    """

    def __init__(self, base_url: str, timeout: Optional[float] = None) -> None:
        """
        Initializes the HttpxTransport.

        Args:
            base_url: The base URL for all API requests made through this transport.
                      Relative URLs passed to the `request` method will be joined
                      with this base URL.
            timeout: The default timeout in seconds for requests. If None, httpx's
                     default timeout (typically 5 seconds) is used.
        """
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Sends an asynchronous HTTP request using the underlying httpx.AsyncClient.

        This method directly delegates the request to the `_client.request` method,
        passing along the method, URL, and any additional keyword arguments.

        Args:
            method: The HTTP method (e.g., 'GET', 'POST').
            url: The target URL path, relative to the `base_url` provided during
                 initialization, or an absolute URL.
            **kwargs: Additional keyword arguments passed directly to
                      `httpx.AsyncClient.request`. See httpx documentation for
                      available options (e.g., `headers`, `params`, `json`, `data`).

        Returns:
            An `httpx.Response` object containing the server's response.
        """
        return await self._client.request(method, url, **kwargs)

    async def close(self) -> None:
        """
        Closes the underlying httpx.AsyncClient and releases resources.

        This should be called when the transport is no longer needed, typically
        when the main API client is being shut down, to ensure proper cleanup
        of network connections.
        """
        await self._client.aclose()
