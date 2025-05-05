from typing import Any, Optional, cast

from ..core.http_transport import HttpTransport
from ..models.add_agent_data_source_request import AddAgentDataSourceRequest
from ..models.agent_data_source import AgentDataSource
from ..models.update_agent_data_source_request import UpdateAgentDataSourceRequest


class AgentDatasourcesClient:
    """Client for Agent Datasources endpoints. Uses HttpTransport for all HTTP and header management."""

    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url

    async def get_agent_data_source(
        self,
        tenant_id: str,
        agent_id: str,
        data_source_id: str,
        include: Optional[str] = None,
    ) -> None:
        """
        Get a specific agent data source

        Returns a specific data source associated with the agent. System users can access any
        tenant's agent data sources, while other users can only access their own tenant's agent
        data sources.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            dataSourceId (str)       : The ID of the agent data source
            include (Optional[str])  : Comma-separated list of relations to include
                                       (dataSource,dataSource.vectorDatabase,dataSource.vectorIn
                                       dex)

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/datasources/{data_source_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def update_agent_data_source(
        self,
        tenant_id: str,
        agent_id: str,
        data_source_id: str,
        body: UpdateAgentDataSourceRequest,
    ) -> None:
        """
        Update an agent data source

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            dataSourceId (str)       : The ID of the agent data source
            body (UpdateAgentDataSourceRequest)
                                     : Request body.

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/datasources/{data_source_id}"
        params: dict[str, Any] = {}
        json_body: UpdateAgentDataSourceRequest = body
        response = await self._transport.request(
            "PUT",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return None

    async def delete_agent_data_source(
        self,
        tenant_id: str,
        agent_id: str,
        data_source_id: str,
    ) -> None:
        """
        Remove a data source from an agent

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            dataSourceId (str)       : The ID of the agent data source

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/datasources/{data_source_id}"
        params: dict[str, Any] = {}
        response = await self._transport.request(
            "DELETE",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def get_agent_data_sources(
        self,
        tenant_id: str,
        agent_id: str,
        include: Optional[str] = None,
    ) -> None:
        """
        Get all data sources for an agent

        Returns all data sources associated with the specified agent. System users can access
        any tenant's agent data sources, while other users can only access their own tenant's
        agent data sources.

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            include (Optional[str])  : Comma-separated list of relations to include
                                       (vectorIndex, vectorDatabase, embedModel, tenant,
                                       documents, agents, events)

        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/datasources"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
        }
        response = await self._transport.request(
            "GET",
            url,
            params=params,
        )
        # Parse response into correct return type
        return None

    async def add_agent_data_source(
        self,
        tenant_id: str,
        agent_id: str,
        body: AddAgentDataSourceRequest,
    ) -> AgentDataSource:
        """
        Add a data source to an agent

        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            body (AddAgentDataSourceRequest)
                                     : Request body.

        Returns:
            AgentDataSource: Data source added successfully

        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/datasources"
        params: dict[str, Any] = {}
        json_body: AddAgentDataSourceRequest = body
        response = await self._transport.request(
            "POST",
            url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return cast(AgentDataSource, response.json())
