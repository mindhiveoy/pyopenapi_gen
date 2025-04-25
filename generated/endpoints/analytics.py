from typing import Any, Dict, Optional

from datetime import date
from httpx import AsyncClient

from ..models.gettenantchatstatsresponse import GetTenantChatStatsResponse


class AnalyticsClient:
    """Client for operations under the 'Analytics' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getTenantChatStats(
        self,
        tenantId: str,
        startDate: Optional[date] = None,
        endDate: Optional[date] = None,
    ) -> GetTenantChatStatsResponse:
        """Get chat statistics for a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/analytics/chat-stats"
        # Assemble request arguments
        kwargs = {}
        params = {"startDate": startDate, "endDate": endDate}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()
