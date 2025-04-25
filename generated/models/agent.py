from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Agent:
    """
    AI assistant configuration model. Represents intelligent agents with
    their behavior settings, knowledge sources, and interaction
    capabilities.
    """

    id: Optional[str] = None  # Unique identifier for the AI assistant
    name: Optional[str] = None  # Display name of the AI assistant
    description: Optional[Optional[str]] = (
        None  # Description of the AI assistant and its purpose
    )
    instructions: Optional[str] = (
        None  # Custom instructions for assistant behavior and responses
    )
    tenantId: Optional[str] = None  # Reference to the associated tenant
    modelId: Optional[str] = (
        None  # Reference to the foundation model used by this agent
    )
    status: Optional[str] = None  # Current operational status of the agent
    settings: Optional[Dict[str, Any]] = (
        None  # Agent's configuration including all required settings for theming and behavior
    )
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
    tenant: Optional[Any] = (
        None  # The tenant this agent belongs to. Only included when requested with ?include=tenant.
    )
    functions: Optional[Optional[List[Dict[str, Any]]]] = (
        None  # Custom functions available to this agent. Only included when requested with ?include=functions.
    )
    datasources: Optional[Optional[List[Dict[str, Any]]]] = (
        None  # Data sources linked to this agent. Only included when requested with ?include=datasources.
    )
    chats: Optional[Optional[List[Chat]]] = (
        None  # Chat sessions with this agent. Only included when requested with ?include=chats.
    )
    _count: Optional[Optional[Dict[str, Any]]] = (
        None  # Count of related entities. Included automatically when related entities are requested.
    )
