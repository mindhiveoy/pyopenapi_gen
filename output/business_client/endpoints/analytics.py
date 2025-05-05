from datetime import date
from typing import Any, Callable, Dict, Optional, cast
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes

class AnalyticsClient:
    """Client for Analytics endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_tenant_chat_stats(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> None:
        """
        Get chat statistics for a tenant
        
        Retrieves chat statistics including total chats, messages per agent, and average
        messages per chat
        
        Args:
            tenantId (str)           : 
            startDate (Optional[date]): 
            endDate (Optional[date]) : 
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/analytics/chat-stats"
        params: dict[str, Any] = {
            **({"startDate": start_date} if start_date is not None else {}),
            **({"endDate": end_date} if end_date is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return None