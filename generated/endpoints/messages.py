from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.adddebugmessageresponse import AddDebugMessageResponse
from ..models.addmessageresponse import AddMessageResponse
from ..models.addmessagesresponse import AddMessagesResponse
from ..models.getdebugmessagesresponse import GetDebugMessagesResponse
from ..models.getmessageresponse import GetMessageResponse
from ..models.getmessagesresponse import GetMessagesResponse


class MessagesClient:
    """Client for operations under the 'Messages' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def addDebugMessage(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        messageId: str,
        body: Dict[str, Any],
    ) -> AddDebugMessageResponse:
        """Add debug messages to a message"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/{messageId}/debug"
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

    async def getDebugMessages(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        messageId: str,
    ) -> GetDebugMessagesResponse:
        """Get debug messages for a message"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/{messageId}/debug"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def getMessage(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        messageId: str,
        include: Optional[str] = None,
    ) -> GetMessageResponse:
        """Get a specific message"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/{messageId}"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def addMessages(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        body: List[Dict[str, Any]],
    ) -> AddMessagesResponse:
        """Add multiple messages to a chat in a single transaction"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages/batch"
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

    async def addMessage(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        body: Dict[str, Any],
    ) -> AddMessageResponse:
        """Add a message to a chat"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages"
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

    async def getMessages(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        roles: Optional[str] = None,
        sortBy: Optional[str] = None,
        sortOrder: Optional[str] = None,
        include: Optional[str] = None,
    ) -> GetMessagesResponse:
        """Get messages from a chat"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}/messages"
        # Assemble request arguments
        kwargs = {}
        params = {
            "cursor": cursor,
            "limit": limit,
            "roles": roles,
            "sortBy": sortBy,
            "sortOrder": sortOrder,
            "include": include,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()
