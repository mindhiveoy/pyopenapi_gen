from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from .agent_status_enum import AgentStatusEnum
from .chat import Chat
from .tenant_summary import TenantSummary


@dataclass
class Agent:
    """
    AI assistant configuration model. Represents intelligent agents with their behavior settings, knowledge sources, and interaction capabilities.

    Attributes:
        id (Optional[str]): Unique identifier for the AI assistant
        name (Optional[str]): Display name of the AI assistant
        description (Optional[str]): Description of the AI assistant and its purpose
        instructions (Optional[str]): Custom instructions for assistant behavior and responses
        tenant_id (Optional[str]): Reference to the associated tenant
        model_id (Optional[str]): Reference to the foundation model used by this agent
        status (Optional[AgentStatusEnum]): Current operational status of the agent
        settings (Optional[Any]): Agent's configuration including all required settings for theming and behavior
        created_at (Optional[datetime]): Creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
        tenant (Optional[TenantSummary]): The tenant this agent belongs to. Only included when requested with ?include=tenant.
        functions (Optional[List[Dict[str, Any]]]): Custom functions available to this agent. Only included when requested with ?include=functions.
        datasources (Optional[List[Dict[str, Any]]]): Data sources linked to this agent. Only included when requested with ?include=datasources.
        chats (Optional[List[Chat]]): Chat sessions with this agent. Only included when requested with ?include=chats.
        count (Optional[Dict[str, Any]]): Count of related entities. Included automatically when related entities are requested.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    tenant_id: Optional[str] = None
    model_id: Optional[str] = None
    status: Optional[AgentStatusEnum] = None
    settings: Optional[Any] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tenant: Optional[TenantSummary] = None
    functions: Optional[List[Dict[str, Any]]] = None
    datasources: Optional[List[Dict[str, Any]]] = None
    chats: Optional[List[Chat]] = None
    count: Optional[Dict[str, Any]] = None
