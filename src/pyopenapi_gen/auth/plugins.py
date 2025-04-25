from typing import Dict, Any
from .base import BaseAuth


class BearerAuth(BaseAuth):
    """Authentication plugin for Bearer tokens."""

    def __init__(self, token: str) -> None:
        self.token = token

    async def authenticate_request(
        self, request_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Ensure headers dict exists
        headers = dict(request_args.get("headers", {}))
        headers["Authorization"] = f"Bearer {self.token}"
        request_args["headers"] = headers
        return request_args


class HeadersAuth(BaseAuth):
    """Authentication plugin for arbitrary headers."""

    def __init__(self, headers: Dict[str, str]) -> None:
        self.headers = headers

    async def authenticate_request(
        self, request_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Merge custom headers
        hdrs = dict(request_args.get("headers", {}))
        hdrs.update(self.headers)
        request_args["headers"] = hdrs
        return request_args
