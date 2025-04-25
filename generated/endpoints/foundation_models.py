from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.createfoundationmodelresponse import CreateFoundationModelResponse
from ..models.deletefoundationmodelresponse import DeleteFoundationModelResponse
from ..models.getfoundationmodelresponse import GetFoundationModelResponse
from ..models.listfoundationmodelsresponse import ListFoundationModelsResponse
from ..models.updatefoundationmodelresponse import UpdateFoundationModelResponse


class FoundationModelsClient:
    """Client for operations under the 'Foundation Models' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getFoundationModel(
        self,
        modelId: str,
    ) -> GetFoundationModelResponse:
        """Get a specific foundation model"""
        # Build URL
        url = f"{self.base_url}/foundation-models/{modelId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateFoundationModel(
        self,
        modelId: str,
        body: Dict[str, Any],
    ) -> UpdateFoundationModelResponse:
        """Update a foundation model"""
        # Build URL
        url = f"{self.base_url}/foundation-models/{modelId}"
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

    async def deleteFoundationModel(
        self,
        modelId: str,
    ) -> DeleteFoundationModelResponse:
        """Delete a foundation model"""
        # Build URL
        url = f"{self.base_url}/foundation-models/{modelId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def listFoundationModels(
        self,
    ) -> ListFoundationModelsResponse:
        """Get all foundation models"""
        # Build URL
        url = f"{self.base_url}/foundation-models"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createFoundationModel(
        self,
        body: Dict[str, Any],
    ) -> CreateFoundationModelResponse:
        """Create a new foundation model"""
        # Build URL
        url = f"{self.base_url}/foundation-models"
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
