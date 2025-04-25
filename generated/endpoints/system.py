from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.getsystemhealthstatusresponse import GetSystemHealthStatusResponse


class SystemClient:
    """Client for operations under the 'System' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getSystemHealthStatus(
        self,
    ) -> GetSystemHealthStatusResponse:
        """Check system health status"""
        # Build URL
        url = f"{self.base_url}/status"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()
