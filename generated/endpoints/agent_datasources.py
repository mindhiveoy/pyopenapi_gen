from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.addagentdatasourceresponse import AddAgentDataSourceResponse
from ..models.agentdatasource import AgentDataSource
from ..models.deleteagentdatasourceresponse import DeleteAgentDataSourceResponse
from ..models.getagentdatasourceresponse import GetAgentDataSourceResponse
from ..models.getagentdatasourcesresponse import GetAgentDataSourcesResponse
from ..models.updateagentdatasourceresponse import UpdateAgentDataSourceResponse


class AgentDatasourcesClient:
    """Client for operations under the 'Agent Datasources' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getAgentDataSource(
        self,
        tenantId: str,
        agentId: str,
        dataSourceId: str,
        include: Optional[str] = None,
    ) -> GetAgentDataSourceResponse:
        """Get a specific agent data source"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/datasources/{dataSourceId}"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateAgentDataSource(
        self,
        tenantId: str,
        agentId: str,
        dataSourceId: str,
        body: Dict[str, Any],
    ) -> UpdateAgentDataSourceResponse:
        """Update an agent data source"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/datasources/{dataSourceId}"
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

    async def deleteAgentDataSource(
        self,
        tenantId: str,
        agentId: str,
        dataSourceId: str,
    ) -> DeleteAgentDataSourceResponse:
        """Remove a data source from an agent"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/datasources/{dataSourceId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def getAgentDataSources(
        self,
        tenantId: str,
        agentId: str,
        include: Optional[str] = None,
    ) -> GetAgentDataSourcesResponse:
        """Get all data sources for an agent"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/datasources"
        # Assemble request arguments
        kwargs = {}
        params = {"include": include}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def addAgentDataSource(
        self,
        tenantId: str,
        agentId: str,
        body: Dict[str, Any],
    ) -> AgentDataSource:
        """Add a data source to an agent"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/datasources"
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
