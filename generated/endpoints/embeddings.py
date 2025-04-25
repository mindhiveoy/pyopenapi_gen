from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.createembeddingresponse import CreateEmbeddingResponse
from ..models.deleteembeddingresponse import DeleteEmbeddingResponse
from ..models.getembeddingresponse import GetEmbeddingResponse
from ..models.listembeddingsresponse import ListEmbeddingsResponse
from ..models.updateembeddingresponse import UpdateEmbeddingResponse


class EmbeddingsClient:
    """Client for operations under the 'Embeddings' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getEmbedding(
        self,
        embedModelId: str,
    ) -> GetEmbeddingResponse:
        """Get a specific embedding"""
        # Build URL
        url = f"{self.base_url}/embeddings/{embedModelId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateEmbedding(
        self,
        embedModelId: str,
        body: Dict[str, Any],
    ) -> UpdateEmbeddingResponse:
        """Update an embedding"""
        # Build URL
        url = f"{self.base_url}/embeddings/{embedModelId}"
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

    async def deleteEmbedding(
        self,
        embedModelId: str,
    ) -> DeleteEmbeddingResponse:
        """Delete an embedding"""
        # Build URL
        url = f"{self.base_url}/embeddings/{embedModelId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def listEmbeddings(
        self,
    ) -> ListEmbeddingsResponse:
        """Get all embeddings"""
        # Build URL
        url = f"{self.base_url}/embeddings"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createEmbedding(
        self,
        body: Dict[str, Any],
    ) -> CreateEmbeddingResponse:
        """Create a new embedding"""
        # Build URL
        url = f"{self.base_url}/embeddings"
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
