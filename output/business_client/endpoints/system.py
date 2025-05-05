from typing import Any, Callable, Dict, Optional, cast
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes
from .get_system_health_status_response import GetSystemHealthStatusResponse

class SystemClient:
    """Client for System endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_system_health_status(
        self,
    ) -> GetSystemHealthStatusResponse:
        """
        Check system health status
        
        Returns the health status of the system and its dependent services. Checks connectivity
        with: - Database - Redis - AI Backend - Jobs Backend  The endpoint returns: - 200 if all
        services are healthy - 503 if any service is unhealthy - 500 if the health check itself
        fails
        
        Returns:
            GetSystemHealthStatusResponse: System is healthy
        
        Raises:
            HttpError:
                HTTPError: 500: Health check failed
                HTTPError: 503: One or more services are unhealthy
        """
        url = f"{self.base_url}/status"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return GetSystemHealthStatusResponse(**response.json())