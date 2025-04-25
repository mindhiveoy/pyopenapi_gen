from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.deletevectorindexresponse import DeleteVectorIndexResponse
from ..models.getvectorindexresponse import GetVectorIndexResponse
from ..models.listvectorindicesresponse import ListVectorIndicesResponse
from ..models.updatevectorindexresponse import UpdateVectorIndexResponse
from ..models.vectorindexlistresponse import VectorIndexListResponse
from ..models.vectorindexresponse import VectorIndexResponse


class IndicesClient:
    """Client for operations under the 'Indices' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getVectorIndex(
        self,
        vectorDatabaseId: str,
        indexId: str,
    ) -> VectorIndexResponse:
        """Get a specific vector index"""
        # Build URL
        url = f"{self.base_url}/vector-databases/{vectorDatabaseId}/indices/{indexId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateVectorIndex(
        self,
        vectorDatabaseId: str,
        indexId: str,
        body: Dict[str, Any],
    ) -> VectorIndexResponse:
        """Update a vector index"""
        # Build URL
        url = f"{self.base_url}/vector-databases/{vectorDatabaseId}/indices/{indexId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.put(url, **kwargs)
        return resp.json()

    async def deleteVectorIndex(
        self,
        vectorDatabaseId: str,
        indexId: str,
    ) -> DeleteVectorIndexResponse:
        """Delete a vector index"""
        # Build URL
        url = f"{self.base_url}/vector-databases/{vectorDatabaseId}/indices/{indexId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def listVectorIndices(
        self,
        vectorDatabaseId: str,
        fields: Optional[str] = None,
        sortBy: Optional[str] = None,
        order: Optional[str] = None,
        startsWith: Optional[str] = None,
        contains: Optional[str] = None,
        page: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> VectorIndexListResponse:
        """List vector indices for a database"""
        # Build URL
        url = f"{self.base_url}/vector-databases/{vectorDatabaseId}/indices"
        # Assemble request arguments
        kwargs = {}
        params = {
            "fields": fields,
            "sortBy": sortBy,
            "order": order,
            "startsWith": startsWith,
            "contains": contains,
            "page": page,
            "limit": limit,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()
