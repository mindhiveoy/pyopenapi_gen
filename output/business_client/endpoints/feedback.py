from typing import Any, Callable, Dict, Optional, cast
from .add_feedback_request import AddFeedbackRequest
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes
from .get_feedback_response import GetFeedbackResponse

class FeedbackClient:
    """Client for Feedback endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def add_feedback(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        message_id: str,
        body: AddFeedbackRequest,
    ) -> None:
        """
        Add feedback to a message
        
        Adds feedback to a specific message. Can be accessed without authentication.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            messageId (str)          : The ID of the message
            body (AddFeedbackRequest): Request body.
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages/{message_id}/feedback"
        params: dict[str, Any] = {
        }
        json_body: AddFeedbackRequest = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None
    
    async def get_feedback(
        self,
        tenant_id: str,
        agent_id: str,
        chat_id: str,
        message_id: str,
    ) -> GetFeedbackResponse:
        """
        Get feedback for a message
        
        Retrieves all feedback for a specific message. Can be accessed by users with tenant
        access.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            chatId (str)             : The ID of the chat
            messageId (str)          : The ID of the message
        
        Returns:
            GetFeedbackResponse: Feedback retrieved successfully
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/chats/{chat_id}/messages/{message_id}/feedback"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return GetFeedbackResponse(**response.json())