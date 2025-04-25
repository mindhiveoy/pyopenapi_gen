from typing import Any, Dict, Optional

from httpx import AsyncClient

from ..models.agenthistorylistresponse import AgentHistoryListResponse
from ..models.agentlistresponse import AgentListResponse
from ..models.agentresponse import AgentResponse
from ..models.createagentresponse import CreateAgentResponse
from ..models.deleteagentresponse import DeleteAgentResponse
from ..models.getagentconfigresponse import GetAgentConfigResponse
from ..models.getagentresponse import GetAgentResponse
from ..models.listagentrevisionsresponse import ListAgentRevisionsResponse
from ..models.listagentsresponse import ListAgentsResponse
from ..models.patchagentjsonresponse import PatchAgentJsonResponse
from ..models.restoreagentrevisionresponse import RestoreAgentRevisionResponse
from ..models.updateagentresponse import UpdateAgentResponse


class AgentsClient:
    """Client for operations under the 'Agents' tag."""

    def __init__(self, client: AsyncClient, base_url: str) -> None:
        self.client = client
        self.base_url = base_url

    async def getAgentConfig(
        self,
        tenantId: str,
        agentId: str,
    ) -> GetAgentConfigResponse:
        """Get public chat configuration"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/config"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def restoreAgentRevision(
        self,
        tenantId: str,
        agentId: str,
        revision: int,
    ) -> AgentResponse:
        """Restore agent to a specific revision"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/revisions/{revision}/restore"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.post(url, **kwargs)
        return resp.json()

    async def listAgentRevisions(
        self,
        tenantId: str,
        agentId: str,
    ) -> AgentHistoryListResponse:
        """List agent revisions"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}/revisions"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def getAgent(
        self,
        tenantId: str,
        agentId: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        chatsSortBy: Optional[str] = None,
        chatsOrder: Optional[str] = None,
    ) -> AgentResponse:
        """Get a specific agent"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}"
        # Assemble request arguments
        kwargs = {}
        params = {
            "include": include,
            "fields": fields,
            "chatsSortBy": chatsSortBy,
            "chatsOrder": chatsOrder,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def updateAgent(
        self,
        tenantId: str,
        agentId: str,
        body: Dict[str, Any],
    ) -> AgentResponse:
        """Update a specific agent and create a new revision"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}"
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

    async def deleteAgent(
        self,
        tenantId: str,
        agentId: str,
    ) -> DeleteAgentResponse:
        """Delete a specific agent"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.delete(url, **kwargs)
        return resp.json()

    async def patchAgentJson(
        self,
        tenantId: str,
        agentId: str,
        body: Dict[str, Any],
    ) -> AgentResponse:
        """Partially update a specific agent's JSON fields and create a new revision"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents/{agentId}"
        # Assemble request arguments
        kwargs = {}
        params = {}
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        kwargs["json"] = body
        # Execute request
        resp = await self.client.patch(url, **kwargs)
        return resp.json()

    async def listAgents(
        self,
        tenantId: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        sortBy: Optional[str] = None,
        order: Optional[str] = None,
    ) -> AgentListResponse:
        """Get all agents for a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents"
        # Assemble request arguments
        kwargs = {}
        params = {
            "include": include,
            "fields": fields,
            "sortBy": sortBy,
            "order": order,
        }
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            kwargs["params"] = filtered
        # Execute request
        resp = await self.client.get(url, **kwargs)
        return resp.json()

    async def createAgent(
        self,
        tenantId: str,
        body: Dict[str, Any],
    ) -> AgentResponse:
        """Create a new agent for a tenant"""
        # Build URL
        url = f"{self.base_url}/tenants/{tenantId}/agents"
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
