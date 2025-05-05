from typing import Any, Dict, List, Optional, cast

from ..core.http_transport import HttpTransport
from ..models.add_debug_message_request import AddDebugMessageRequest
from ..models.add_message_request import AddMessageRequest
from ..models.add_messages_request import AddMessagesRequest
from ..models.get_messages_response import GetMessagesResponse
from ..models.message import Message


class MessagesClient:
    """Client for Messages endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def add_debug_message(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        message_id: str,
        body: AddDebugMessageRequest,
    ) -> Dict[str, Any]:
        """
        Add debug messages to a message

        Adds debug messages to a specific message. Can only be accessed by internal system
        calls.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            messageId (str)          : The ID of the message
            body (AddDebugMessageRequest)
                                     : Request body.

        Returns:
            Dict[str, Any]: Debug messages added successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages/{message_id}/debug"
        params: dict[str, Any] = {}
        json_body: AddDebugMessageRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(Dict[str, Any], response.json())

    async def get_debug_messages(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        message_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Get debug messages for a message

        Retrieves all debug messages for a specific message. Can only be accessed by internal
        system calls.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            messageId (str)          : The ID of the message

        Returns:
            List[Dict[str, Any]]: Debug messages retrieved successfully

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages/{message_id}/debug"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(List[Dict[str, Any]], response.json())

    async def get_message(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        message_id: str,
        include: Optional[str] = None,
    ) -> Message:
        """
        Get a specific message

        Returns a specific message by ID. System users can access any tenant's message, while
        other users can only access their own tenant's messages. Supports including related data
        through the include query parameter.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            messageId (str)          : The ID of the message
            include (Optional[str])  : Comma-separated list of relations to include
                                       (chat,agent,feedback)

        Returns:
            Message: Message details

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages/{message_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(Message, response.json())

    async def add_messages(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        body: AddMessagesRequest,
        x_mainio_internal_token: Optional[str] = None,
    ) -> None:
        """
        Add multiple messages to a chat in a single transaction

        Adds multiple new messages to an existing chat in a single transaction. Can be accessed
        only via internal API token.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            x-mainio-internal-token (Optional[str])
                                     : Internal API token for backend-to-backend communication
            body (AddMessagesRequest): Request body.

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages/batch"
        params: dict[str, Any] = {}
        headers: dict[str, Any] = {}
        json_body: AddMessagesRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            headers=headers,
            json=json_body,
        )
        # Parse response into correct return type
        return None

    async def add_message(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        body: AddMessageRequest,
        x_mainio_internal_token: Optional[str] = None,
    ) -> None:
        """
        Add a message to a chat

        Adds a new message to an existing chat. Can be accessed either by users with tenant
        access or via internal API token.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            x-mainio-internal-token (Optional[str])
                                     : Internal API token for backend-to-backend communication
            body (AddMessageRequest) : Request body.

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages"
        params: dict[str, Any] = {}
        headers: dict[str, Any] = {}
        json_body: AddMessageRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            headers=headers,
            json=json_body,
        )
        # Parse response into correct return type
        return None

    async def get_messages(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        roles: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        include: Optional[str] = None,
    ) -> GetMessagesResponse:
        """
        Get messages from a chat

        Retrieves messages from an existing chat with pagination support. Can be accessed either
        by users with tenant access or via internal API token.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            cursor (Optional[str])   : Cursor for pagination (message ID)
            limit (Optional[int])    : Number of messages to return
            roles (Optional[str])    : Comma-separated list of roles to filter by
                                       (user,assistant,system,function,etc)
            sortBy (Optional[str])   : Field to sort by (must be indexed)
            sortOrder (Optional[str]): Sort order
            include (Optional[str])  : Comma-separated list of relations to include
                                       (chat,agent,feedback)

        Returns:
            GetMessagesResponse: Messages retrieved successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages"
        params: dict[str, Any] = {
            **({"cursor": cursor} if cursor is not None else {}),
            **({"limit": limit} if limit is not None else {}),
            **({"roles": roles} if roles is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"sortOrder": sort_order} if sort_order is not None else {}),
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return cast(GetMessagesResponse, response.json())
