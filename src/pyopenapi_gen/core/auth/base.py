from typing import Any, Protocol  # noqa: F401


class BaseAuth(Protocol):
    """Protocol for authentication plugins."""

    async def authenticate_request(self, request_args: dict[str, Any]) -> dict[str, Any]:
        """Modify or augment the request arguments for authentication."""
        # Default stub returns the input unchanged
        return request_args
