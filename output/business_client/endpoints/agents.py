from typing import Any, Callable, Dict, Optional, Union, cast
from .agent_create import AgentCreate
from .agent_history_list_response import AgentHistoryListResponse
from .agent_list_response import AgentListResponse
from .agent_response import AgentResponse
from .agent_update import AgentUpdate
from .core.exceptions import ApiError
from .core.http_transport import HttpTransport
from .core.schemas import ApiResponse
from .core.streaming_helpers import iter_bytes
from .json_field_update_input import JsonFieldUpdateInput

class AgentsClient:
    """Client for Agents endpoints. Uses HttpTransport for all HTTP and header management."""
    
    def __init__(self, transport: HttpTransport, base_url: str) -> None:
        self._transport = transport
        self.base_url: str = base_url
    
    async def get_agent_config(
        self,
        tenant_id: str,
        agent_id: str,
    ) -> None:
        """
        Get public chat configuration
        
        Returns the public configuration parts of the chat for the client.
        
        Args:
            tenantId (str)           : 
            agentId (str)            : 
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/config"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def restore_agent_revision(
        self,
        tenant_id: str,
        agent_id: str,
        revision: int,
    ) -> Union[AgentResponse, Dict[str, Any]]:
        """
        Restore agent to a specific revision
        
        Restores an agent to a specific revision. System users can restore any tenant's agent,
        while other users can only restore their own tenant's agents.  When restoring an agent:
        - The agent's state is reverted to the specified revision - The agent's revision number
        is set to the restored revision - Future revisions are preserved until changes are made
        - Making changes to a restored state creates a new branch  Branching behavior: 1. When
        you restore to revision N 2. The agent is set to that state with revision = N 3. Future
        revisions (>N) remain in history 4. If you make changes after restoring:    - A new
        revision N+1 is created    - All revisions >N are deleted    - A new branch of history
        starts from N+1
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            revision (int)           : The revision number to restore to
        
        Returns:
            Union[AgentResponse, Dict[str, Any]]: Agent restored successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/revisions/{revision}/restore"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "POST", url,
            params=params,
        )
        # Parse response into correct return type
        return Union[AgentResponse, Dict[str, Any]](**response.json())
    
    async def list_agent_revisions(
        self,
        tenant_id: str,
        agent_id: str,
    ) -> AgentHistoryListResponse:
        """
        List agent revisions
        
        Returns a list of revisions for a specific agent. System users can access any tenant's
        agent revisions, while other users can only access their own tenant's agent revisions.
        Each revision represents a point in time when the agent was modified, including: - Full
        updates via PUT endpoint - Partial updates via PATCH endpoint - Restorations to previous
        versions  The list is ordered by revision number in descending order (newest first).
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
        
        Returns:
            AgentHistoryListResponse: List of agent revisions
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}/revisions"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return AgentHistoryListResponse(**response.json())
    
    async def get_agent(
        self,
        tenant_id: str,
        agent_id: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        chats_sort_by: Optional[str] = None,
        chats_order: Optional[str] = None,
    ) -> AgentResponse:
        """
        Get a specific agent
        
        Returns a specific agent by ID. System users can access any tenant's agent, while other
        users can only access their own tenant's agents. Supports including related data through
        the include query parameter. Supports selecting specific fields through the fields query
        parameter.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            include (Optional[str])  : Comma-separated list of relations to include (tenant,
                                       functions, datasources, chats)
            fields (Optional[str])   : Comma-separated list of fields to return. Available
                                       fields: id, tenantId, name, instructions, createdAt,
                                       updatedAt
            chatsSortBy (Optional[str])
                                     : Field to sort chats by (createdAt, title)
            chatsOrder (Optional[str]): Sort order for chats (asc or desc)
        
        Returns:
            AgentResponse: Agent details
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
            **({"fields": fields} if fields is not None else {}),
            **({"chatsSortBy": chats_sort_by} if chats_sort_by is not None else {}),
            **({"chatsOrder": chats_order} if chats_order is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return AgentResponse(**response.json())
    
    async def update_agent(
        self,
        tenant_id: str,
        agent_id: str,
        body: AgentUpdate,
    ) -> Union[AgentResponse, Dict[str, Any]]:
        """
        Update a specific agent and create a new revision
        
        Update a specific agent by ID and create a new revision. System users can update any
        tenant's agent, while other users can only update their own tenant's agents.  When
        updating an agent: - A new revision is automatically created - The revision number is
        incremented - The previous state is preserved in the revision history - If updating from
        a restored state, future revisions are cleaned up
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            body (AgentUpdate)       : Request body.
        
        Returns:
            Union[AgentResponse, Dict[str, Any]]: Agent updated successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}"
        params: dict[str, Any] = {
        }
        json_body: AgentUpdate = body
        response = await self._transport.request(
            "PUT", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return Union[AgentResponse, Dict[str, Any]](**response.json())
    
    async def delete_agent(
        self,
        tenant_id: str,
        agent_id: str,
    ) -> None:
        """
        Delete a specific agent
        
        Deletes a specific agent by ID. System users can delete any tenant's agents, while other
        users can only delete their own tenant's agents.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}"
        params: dict[str, Any] = {
        }
        response = await self._transport.request(
            "DELETE", url,
            params=params,
        )
        # Parse response into correct return type
        return None
    
    async def patch_agent_json(
        self,
        tenant_id: str,
        agent_id: str,
        body: JsonFieldUpdateInput,
    ) -> Union[AgentResponse, Dict[str, Any]]:
        """
        Partially update a specific agent's JSON fields and create a new revision
        
        Performs targeted updates to JSON fields of an agent and creates a new revision. Allows
        setting, deleting, or merging values at specific paths. System users can update any
        tenant's agent, while other users can only update their own tenant's agents.  When
        updating JSON fields: - A new revision is automatically created - The revision number is
        incremented - The previous state is preserved in the revision history - If updating from
        a restored state, future revisions are cleaned up  Supported JSON fields: - config:
        Agent configuration including theme, behavior settings, etc.
        
        Args:
            tenantId (str)           : The ID of the tenant
            agentId (str)            : The ID of the agent
            body (JsonFieldUpdateInput)
                                     : Request body.
        
        Returns:
            Union[AgentResponse, Dict[str, Any]]: Agent updated successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents/{agent_id}"
        params: dict[str, Any] = {
        }
        json_body: JsonFieldUpdateInput = body
        response = await self._transport.request(
            "PATCH", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return Union[AgentResponse, Dict[str, Any]](**response.json())
    
    async def list_agents(
        self,
        tenant_id: str,
        include: Optional[str] = None,
        fields: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: Optional[str] = None,
    ) -> AgentListResponse:
        """
        Get all agents for a tenant
        
        Returns all agents for the specified tenant. System users can access any tenant's
        agents, while other users can only access their own tenant's agents. Supports including
        related data through the include query parameter.
        
        Args:
            tenantId (str)           : The ID of the tenant
            include (Optional[str])  : Comma-separated list of relations to include (tenant,
                                       functions, datasources, chats)
            fields (Optional[str])   : Comma-separated list of fields to return
            sortBy (Optional[str])   : Field to sort by (name, createdAt, updatedAt)
            order (Optional[str])    : Sort order (asc or desc)
        
        Returns:
            AgentListResponse: List of agents
        
        Raises:
            HttpError:
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents"
        params: dict[str, Any] = {
            **({"include": include} if include is not None else {}),
            **({"fields": fields} if fields is not None else {}),
            **({"sortBy": sort_by} if sort_by is not None else {}),
            **({"order": order} if order is not None else {}),
        }
        response = await self._transport.request(
            "GET", url,
            params=params,
        )
        # Parse response into correct return type
        return AgentListResponse(**response.json())
    
    async def create_agent(
        self,
        tenant_id: str,
        body: AgentCreate,
    ) -> AgentResponse:
        """
        Create a new agent for a tenant
        
        Create a new agent for a tenant. System users can create agents for any tenant. Admin
        users can only create agents in their own tenant.
        
        Args:
            tenantId (str)           : The ID of the tenant
            body (AgentCreate)       : Request body.
        
        Returns:
            AgentResponse: Agent created successfully
        
        Raises:
            HttpError:
                HTTPError: 400: Validation error
                HTTPError: 401: Authentication is required and has failed or has not been
                           provided
                HTTPError: 403: Access denied due to insufficient permissions
                HTTPError: 404: The requested resource was not found
                HTTPError: 500: Internal server error occurred during request processing
        """
        url = f"{self.base_url}/tenants/{tenant_id}/agents"
        params: dict[str, Any] = {
        }
        json_body: AgentCreate = body
        response = await self._transport.request(
            "POST", url,
            params=params,
            json=json_body,
        )
        # Parse response into correct return type
        return AgentResponse(**response.json())