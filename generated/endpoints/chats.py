from typing import Any, AsyncIterator, Dict, Optional

from httpx import AsyncClient
from pyopenapi_gen.streaming_helpers import SSEEvent, iter_sse

from ..models.createchatresponse import CreateChatResponse
from ..models.deletechatresponse import DeleteChatResponse
from ..models.getchatlinkresponse import GetChatLinkResponse
from ..models.getchatresponse import GetChatResponse
from ..models.getchatsresponse import GetChatsResponse
from ..models.getchatstreamresponse import GetChatStreamResponse


class ChatsClient:
    """Client for operations under the 'Chats' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getChatLink(
        self,
        tenantId: str,
        agentId: str,
    ) -> GetChatLinkResponse:
        """Get the chat link for an agent"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chat-link"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def getChat(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
        include: Optional[str] = None,
    ) -> GetChatResponse:
        """Get a specific chat"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def deleteChat(
        self,
        tenantId: str,
        agentId: str,
        chatId: str,
    ) -> DeleteChatResponse:
        """Delete a chat"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/{chatId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def getChats(
        self,
        tenantId: str,
        agentId: str,
        fields: Optional[str] = None,
        include: Optional[str] = None,
        sortBy: Optional[str] = None,
        order: Optional[str] = None,
    ) -> GetChatsResponse:
        """Get chats for an agent"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats"
        # Assemble request arguments
        kwargs = {}
        params = {
            "fields": fields,
            "include": include,
            "sortBy": sortBy,
            "order": order,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createChat(
        self,
        tenantId: str,
        agentId: str,
        body: Dict[str, Any],
    ) -> CreateChatResponse:
        """Create a new chat"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats"
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

    async def getChatStream(
        self,
        tenantId: str,
        agentId: str,
        connectionId: Optional[str] = None,
        sessionToken: Optional[str] = None,
    ) -> AsyncIterator[bytes]:
        """Open a chat stream connection
        Stream format: event-stream
        Use the appropriate streaming helper.
        """
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/chats/stream"
        # Assemble request arguments
        kwargs = {}
        params = {"connectionId": connectionId, "sessionToken": sessionToken}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        async for event in iter_sse(resp):
            yield event
