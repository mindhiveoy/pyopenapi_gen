from typing import Any, AsyncIterator, Dict, cast

from ..core.http_transport import HttpTransport


class ListenClient:
    """Client for Listen endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def listen_events(
        self,
        filters: Dict[str, Any],
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Establish a Server-Sent Events connection

        Establishes a Server-Sent Events connection with optional filters. Requires
        authentication and system user role.

        Args:
            filters (Dict[str, Any]) : JSON object defining filters for the events

        Returns:
            AsyncIterator[Dict[str, Any]]: Server-Sent Events stream established

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/listen"
        params: dict[str, Any] = {
            "filters": filters,
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(AsyncIterator[Dict[str, Any]], response.json())
