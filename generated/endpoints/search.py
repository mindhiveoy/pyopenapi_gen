from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.elaboratesearchphraseresponse import ElaborateSearchPhraseResponse


class SearchClient:
    """Client for operations under the 'Search' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def elaborateSearchPhrase(
        self,
        tenantId: str,
        agentId: str,
        dataSourceId: str,
        body: Dict[str, Any],
    ) -> ElaborateSearchPhraseResponse:
        """Search endpoint for datasource. It will return the elaborated search phrase and the search results."""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/datasources/{dataSourceId}/search"
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
