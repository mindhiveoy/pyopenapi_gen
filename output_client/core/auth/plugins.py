from typing import Any, Awaitable, Callable, Dict, Optional

from .base import BaseAuth


class BearerAuth(BaseAuth):
    """Authentication plugin for Bearer tokens."""

    def __init__(self, token: str) -> None:
        self.token = token

    async def authenticate_request(self, request_args: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure headers dict exists
        headers = dict(request_args.get("headers", {}))
        headers["Authorization"] = f"Bearer {self.token}"
        request_args["headers"] = headers
        return request_args


class HeadersAuth(BaseAuth):
    """Authentication plugin for arbitrary headers."""

    def __init__(self, headers: Dict[str, str]) -> None:
        self.headers = headers

    async def authenticate_request(self, request_args: Dict[str, Any]) -> Dict[str, Any]:
        # Merge custom headers
        hdrs = dict(request_args.get("headers", {}))
        hdrs.update(self.headers)
        request_args["headers"] = hdrs
        return request_args


class ApiKeyAuth(BaseAuth):
    """Authentication plugin for API keys (header, query, or cookie)."""

    def __init__(self, key: str, location: str = "header", name: str = "X-API-Key") -> None:
        """
        Args:
            key: The API key value.
            location: Where to add the key ("header", "query", or "cookie").
            name: The name of the header/query/cookie parameter.
        """
        self.key = key
        self.location = location
        self.name = name

    async def authenticate_request(self, request_args: Dict[str, Any]) -> Dict[str, Any]:
        if self.location == "header":
            headers = dict(request_args.get("headers", {}))
            headers[self.name] = self.key
            request_args["headers"] = headers
        elif self.location == "query":
            params = dict(request_args.get("params", {}))
            params[self.name] = self.key
            request_args["params"] = params
        elif self.location == "cookie":
            cookies = dict(request_args.get("cookies", {}))
            cookies[self.name] = self.key
            request_args["cookies"] = cookies
        else:
            raise ValueError(f"Invalid API key location: {self.location}")
        return request_args


class OAuth2Auth(BaseAuth):
    """Authentication plugin for OAuth2 Bearer tokens, with optional auto-refresh."""

    def __init__(self, access_token: str, refresh_callback: Optional[Callable[[str], Awaitable[str]]] = None) -> None:
        """
        Args:
            access_token: The OAuth2 access token.
            refresh_callback: Optional async function to refresh the token. If provided, will be called
            if token is expired.
        """
        self.access_token = access_token
        self.refresh_callback = refresh_callback

    async def authenticate_request(self, request_args: Dict[str, Any]) -> Dict[str, Any]:
        # In a real implementation, check expiry and refresh if needed
        if self.refresh_callback is not None:
            # Optionally refresh token (user must implement expiry logic)
            new_token = await self.refresh_callback(self.access_token)
            if new_token and new_token != self.access_token:
                self.access_token = new_token
        headers = dict(request_args.get("headers", {}))
        headers["Authorization"] = f"Bearer {self.access_token}"
        request_args["headers"] = headers
        return request_args
