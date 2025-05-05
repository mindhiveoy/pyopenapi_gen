from typing import Any, cast

from ..core.http_transport import HttpTransport
from ..models.elaborate_search_phrase_request import ElaborateSearchPhraseRequest
from ..models.elaborate_search_phrase_response import ElaborateSearchPhraseResponse


class SearchClient:
    """Client for Search endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def elaborate_search_phrase(
        self,
        tenant_id: str,
        agent_id: str,
        data_source_id: str,
        body: ElaborateSearchPhraseRequest,
    ) -> ElaborateSearchPhraseResponse:
        """
        Search endpoint for datasource. It will return the elaborated search phrase and the
        search results.

        Forwards search queries from the client to the main AI backend service.

        Args:
            tenantId (str)           : Tenant identifier.
            agentId (str)            : Agent identifier.
            dataSourceId (str)       : Data source identifier.
            body (ElaborateSearchPhraseRequest)
                                     : Request body.

        Returns:
            ElaborateSearchPhraseResponse: Successful response containing search results.

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/datasources/{data_source_id}/search"
        params: dict[str, Any] = {}
        json_body: ElaborateSearchPhraseRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(ElaborateSearchPhraseResponse, response.json())
