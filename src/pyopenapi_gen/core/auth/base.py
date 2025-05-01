from typing import Any, Protocol  # noqa: F401


class BaseAuth(Protocol):
    """Protocol for authentication plugins."""

    async def authenticate_request(self, request_args: dict[str, Any]) -> dict[str, Any]:
        """Modify or augment the request arguments for authentication."""
        # Default stub returns the input unchanged
        return request_args


class CompositeAuth(BaseAuth):
    """Compose multiple BaseAuth plugins, applying each in sequence to the request."""

    def __init__(self, *plugins: BaseAuth):
        self.plugins = plugins

    async def authenticate_request(self, request_args: dict[str, Any]) -> dict[str, Any]:
        for plugin in self.plugins:
            request_args = await plugin.authenticate_request(request_args)
        return request_args
