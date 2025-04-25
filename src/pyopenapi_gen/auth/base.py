from typing import Protocol, Dict, Any


class BaseAuth(Protocol):
    """Protocol for authentication plugins."""

    async def authenticate_request(
        self, request_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify or augment the request arguments for authentication."""
        # Default stub returns Ellipsis
        return Ellipsis
