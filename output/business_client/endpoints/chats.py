import collections.abc
from typing import Any, AsyncIterator, Callable, Dict, Optional, cast
from .chat_create import ChatCreate
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import handle_stream, iter_bytes
from .create_chat_response import CreateChatResponse
from .get_chat_link_response import GetChatLinkResponse
from .get_chat_response import GetChatResponse
from .get_chats_response import GetChatsResponse

class ChatsClient:
    """Client for Chats endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_chat_link(
        self,
        tenant_id: str,
        agent_id: str,
    ) -> GetChatLinkResponse:
        """
        Get the chat link for an agent
        
        Returns the public chat URL for the specified agent. System users can access any
        tenant's agent links, while other users can only access their own tenant's agent links.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
        
        Returns:
            GetChatLinkResponse: Chat link URL
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chat-link"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return GetChatLinkResponse(**response.json())
    
    async def get_chat(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        include: Optional[str] = None,
    ) -> GetChatResponse:
        """
        Get a specific chat
        
        Returns a specific chat by ID. System users can access any tenant's chat, while other
        users can only access their own tenant's chats. Supports including related data through
        the include query parameter.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            include (Optional[str])  : Comma-separated list of relations to include
                                       (messages,agent)
        
        Returns:
            GetChatResponse: Chat details
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return GetChatResponse(**response.json())
    
    async def delete_chat(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
    ) -> None:
        """
        Delete a chat
        
        Deletes a chat and all its messages. System users can delete any tenant's chats, while
        other users can only delete their own tenant's chats.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def get_chats(
        self,
        tenant_id: str,
        agent_id: str,
        fields: Optional[str] = None,
        include: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
    ) -> GetChatsResponse:
        """
        Get chats for an agent
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            fields (Optional[str])   : Comma-separated list of fields to return
            include (Optional[str])  : Comma-separated list of relations to include (messages,
                                       agent, messageCount, feedbackCount)
            sortBy (Optional[str])   : Field to sort by
            order (Optional[str])    : Sort order (asc or desc)
        
        Returns:
            GetChatsResponse: List of chats
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats"
        params: dict[str, Any] = {
            **({"fields": fields} if fields is not None else {}),
            **({"include": include} if include is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"order": order} if order is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return GetChatsResponse(**response.json())
    
    async def create_chat(
        self,
        tenant_id: str,
        agent_id: str,
        body: ChatCreate,
    ) -> CreateChatResponse:
        """
        Create a new chat
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            body (ChatCreate)        : Request body.
        
        Returns:
            CreateChatResponse: Chat created successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats"
        params: dict[str, Any] = {
        }
        json_body: ChatCreate = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return CreateChatResponse(**response.json())
    
    async def get_chat_stream(
        self,
        tenant_id: str,
        agent_id: str,
        connection_id: str,
        session_token: str,
    ) -> AsyncIterator[str]:
        """
        Open a chat stream connection
        
        Opens a Server-Sent Events (SSE) stream for real-time chat communication by proxying the
        connection to the AI backend service. This endpoint acts as a pure bridge between the
        client and AI backend, with no additional business logic.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            connectionId (str)       : A unique identifier for this connection
            sessionToken (str)       : The session token for authentication
        
        Returns:
            AsyncIterator[str]: Stream connection established
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/stream"
        params: dict[str, Any] = {
            "connectionId": connection_id,
            "sessionToken": session_token,
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return handle_stream(response, str)