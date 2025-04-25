from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.addfeedbackresponse import AddFeedbackResponse
from ..models.getfeedbackresponse import GetFeedbackResponse


class FeedbackClient:
    """Client for operations under the 'Feedback' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def addFeedback(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        messageId: str,
        body: Dict[str, Any],
    ) -> AddFeedbackResponse:
        """Add feedback to a message"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/{messageId}/feedback"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.post(url, **kwargs)
        return resp.json()

    async def getFeedback(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        messageId: str,
    ) -> GetFeedbackResponse:
        """Get feedback for a message"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/{messageId}/feedback"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()
