from datetime import date
from typing import Any, Optional

from ..core.http_transport import HttpTransport


class DefaultClient:
    """Client for default endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def get_tenants_tenant_id_feedback(
        self,
        tenant_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Get all feedback for a tenant

        Retrieves paginated feedback data for a tenant with optional filtering

        Args:
            tenantId (str)           :
            startDate (Optional[date]): Start date for filtering (YYYY-MM-DD)
            endDate (Optional[date]) : End date for filtering (YYYY-MM-DD)
            page (Optional[int])     : Page number for pagination
            limit (Optional[int])    : Number of items per page
            agentId (Optional[str])  : Filter by agent ID

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/feedback"
        params: dict[str, Any] = {
            **({"startDate": start_date} if start_date is not None else {}),
            **({"endDate": end_date} if end_date is not None else {}),
            **({"page": page} if page is not None else {}),
            **({"limit": limit} if limit is not None else {}),
            **({"agentId": agent_id} if agent_id is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None
