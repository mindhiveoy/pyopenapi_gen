from typing import Any, Protocol

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
    - Return an `httpx.Response` object for all requests, regardless of status code.
    - Be safe for use in async contexts.
    - STRICT REQUIREMENT: Return the `httpx.Response` unchanged for every HTTP response, including
      non-2xx responses. Implementations must NOT raise on error status codes. Status-code handling
      is the responsibility of the generated endpoint methods, which inspect `response.status_code`
      and raise the appropriate exception alias (e.g. `NotFoundError` for 404) or the base `HTTPError`
      for unhandled status codes. This contract ensures exception aliases work as intended.
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
            httpx.Response: The HTTP response object, regardless of status code.

        Raises:
            Exception: Implementations may raise exceptions for network errors or invalid responses.

        Protocol Contract:
            - Every response is returned to the caller unchanged, including non-2xx responses.
            - Implementations must NOT raise on error status codes. Status-code handling (including
              raising exception aliases such as NotFoundError) is performed by the generated endpoint
              methods. This ensures error handling is consistent and explicit across all generated
              clients and transport implementations.
        """
        raise NotImplementedError()

    async def close(self) -> None:
        """
        Closes any resources held by the transport (e.g., HTTP connections).

        All implementations must provide this method. If the transport does not hold resources,
        this should be a no-op.
        """
        raise NotImplementedError()


class HttpxTransport:
    """
    A concrete implementation of the HttpTransport protocol using the `httpx` library.

    This class provides the default asynchronous HTTP transport mechanism for the
    generated API client. It wraps an `httpx.AsyncClient` instance to handle
    request sending, connection pooling, and resource management.

    Optionally supports authentication via any BaseAuth-compatible plugin, including CompositeAuth.

    CONTRACT:
        - This implementation returns the `httpx.Response` unchanged for every response, including non-2xx
          responses. It does NOT raise on error status codes. Status-code handling (including raising exception
          aliases such as `NotFoundError`) is delegated to the generated endpoint methods, which inspect
          `response.status_code`. This ensures the generated exception aliases are actually raised.

    Attributes:
        _client (httpx.AsyncClient): Configured HTTPX async client for all requests.
        _auth (BaseAuth | None): Optional authentication plugin for request signing (can be CompositeAuth).
        _bearer_token (str | None): Optional bearer token for Authorization header.
        _default_headers (dict[str, str] | None): Default headers to apply to all requests.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float | None = None,
        auth: BaseAuth | None = None,
        bearer_token: str | None = None,
        default_headers: dict[str, str] | None = None,
        verify_ssl: bool = True,
    ) -> None:
        """
        Initializes the HttpxTransport.

        Args:
            base_url (str): The base URL for all API requests made through this transport.
            timeout (float | None): The default timeout in seconds for requests. If None, httpx's default is used.
            auth (BaseAuth | None): Optional authentication plugin for request signing (can be CompositeAuth).
            bearer_token (str | None): Optional raw bearer token string for Authorization header.
            default_headers (dict[str, str] | None): Default headers to apply to all requests.
            verify_ssl (bool): Whether to verify SSL certificates. Defaults to True.
                Set to False for local development with self-signed certificates.

        Note:
            If both auth and bearer_token are provided, auth takes precedence.
        """
        self._client: httpx.AsyncClient = httpx.AsyncClient(base_url=base_url, timeout=timeout, verify=verify_ssl)
        self._auth: BaseAuth | None = auth
        self._bearer_token: str | None = bearer_token
        self._default_headers: dict[str, str] | None = default_headers

    async def _prepare_headers(
        self,
        current_request_kwargs: dict[str, Any],
    ) -> dict[str, str]:
        """
        Prepares headers for an HTTP request, incorporating default headers,
        request-specific headers, and authentication.
        """
        # Initialize headers for the current request
        prepared_headers: dict[str, str] = {}

        # 1. Apply transport-level default headers
        if self._default_headers:
            prepared_headers.update(self._default_headers)

        # 2. Merge headers passed specifically for this request (overriding transport defaults)
        if "headers" in current_request_kwargs and isinstance(current_request_kwargs["headers"], dict):
            prepared_headers.update(current_request_kwargs["headers"])

        # 3. Apply authentication plugin or bearer token (which can further modify headers)
        # We pass a temporary request_args dict containing only the headers to the auth plugin,
        # as the auth plugin might expect other keys which are not relevant for header preparation.
        # The auth plugin is expected to modify the 'headers' key in the passed dict.
        temp_request_args_for_auth = {"headers": prepared_headers.copy()}

        if self._auth is not None:
            authenticated_args = await self._auth.authenticate_request(temp_request_args_for_auth)
            # Ensure 'headers' key exists and is a dict after authentication
            if "headers" in authenticated_args and isinstance(authenticated_args["headers"], dict):
                prepared_headers = authenticated_args["headers"]
            else:
                # Handle cases where auth plugin might not return headers as expected
                # This could be an error or a specific design of an auth plugin.
                # For now, we assume it should always return a 'headers' dict.
                # If not, we retain the headers we had before calling the auth plugin.
                pass  # Or raise an error, or log a warning.
        elif self._bearer_token is not None:
            # If no auth plugin, but bearer token is present, add/overwrite Authorization header.
            prepared_headers["Authorization"] = f"Bearer {self._bearer_token}"

        return prepared_headers

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
            httpx.Response: The HTTP response object from the server, regardless of status code.

        Raises:
            httpx.HTTPError: For network errors or invalid responses. Non-2xx HTTP responses are
                returned unchanged; status-code handling is performed by the generated endpoint methods.
        """
        # Prepare request arguments, excluding headers initially
        request_args: dict[str, Any] = {k: v for k, v in kwargs.items() if k != "headers"}

        # This method handles default headers, request-specific headers, and authentication
        prepared_headers = await self._prepare_headers(kwargs)
        request_args["headers"] = prepared_headers

        response = await self._client.request(method, url, **request_args)
        return response

    async def close(self) -> None:
        """
        Closes the underlying httpx.AsyncClient and releases resources.

        This should be called when the transport is no longer needed, typically
        when the main API client is being shut down, to ensure proper cleanup
        of network connections.
        """
        await self._client.aclose()

    async def __aenter__(self) -> "HttpxTransport":
        """
        Enter the async context manager. Returns self.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """
        Exit the async context manager. Calls close().
        """
        await self.close()
