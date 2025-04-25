from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.createvectordatabaseresponse import CreateVectorDatabaseResponse
from ..models.createvectorindexresponse import CreateVectorIndexResponse
from ..models.listvectordatabasesresponse import ListVectorDatabasesResponse
from ..models.vectordatabaselistresponse import VectorDatabaseListResponse
from ..models.vectordatabaseresponse import VectorDatabaseResponse


class VectorDatabasesClient:
    """Client for operations under the 'Vector Databases' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def createVectorIndex(
        self,
        vectorDatabaseId: str,
        body: Dict[str, Any],
    ) -> CreateVectorIndexResponse:
        """Create a new vector index"""
        # Build URL
        url = f"{self.base_url}/vector-databases/{vectorDatabaseId}/indices"
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

    async def listVectorDatabases(
        self,
        fields: Optional[str] = None,
        sortBy: Optional[str] = None,
        order: Optional[str] = None,
    ) -> VectorDatabaseListResponse:
        """Get all vector databases"""
        # Build URL
        url = f"{self.base_url}/vector-databases"
        # Assemble request arguments
        kwargs = {}
        params = {"fields": fields, "sortBy": sortBy, "order": order}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createVectorDatabase(
        self,
        body: Dict[str, Any],
    ) -> VectorDatabaseResponse:
        """Create a new vector database"""
        # Build URL
        url = f"{self.base_url}/vector-databases"
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
