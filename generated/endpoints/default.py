from typing import Any, Dict, Optional

from datetime import date
from httpx import AsyncClient

from ..models.get_tenantstenantidfeedbackresponse import GET_TenantsTenantIdFeedbackResponse


class DefaultClient:
    """Client for operations under the 'default' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url


    async def GET_/tenants/{tenantId}/feedback(
        self,
        tenantId: str,        startDate: Optional[date] = None,        endDate: Optional[date] = None,        page: Optional[int] = None,        limit: Optional[int] = None,        agentId: Optional[str] = None,    ) -> GET_TenantsTenantIdFeedbackResponse:
        """Get all feedback for a tenant
        """
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/feedback"
        # Assemble request arguments
        kwargs = {}
        params = {
            'startDate': startDate,             'endDate': endDate,             'page': page,             'limit': limit,             'agentId': agentId        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs['params'] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()
