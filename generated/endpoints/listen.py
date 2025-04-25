from typing import Any, AsyncIterator, Dict, Optional

from httpx import AsyncClient
from pyopenapi_gen.streaming_helpers import SSEEvent, iter_sse

from ..models.listeneventsresponse import ListenEventsResponse


class ListenClient:
    """Client for operations under the 'Listen' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def listenEvents(
        self,
        filters: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[bytes]:
        """Establish a Server-Sent Events connection
        Stream format: event-stream
        Use the appropriate streaming helper.
        """
        # Build URL
        url = f"{self.base_url}/listen"
        # Assemble request arguments
        kwargs = {}
        params = {"filters": filters}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        async for event in iter_sse(resp):
            yield event
