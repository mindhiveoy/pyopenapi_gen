from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Tenant:
    """
    Tenant model for multi-tenant architecture. Represents an organization
    with its own users, agents, and resources. Core entity for tenant
    isolation and resource management.
    """

    id: Optional[str] = None  # Unique identifier for the tenant organization
    name: Optional[str] = None  # Display name of the organization
    domain: Optional[Optional[str]] = (
        None  # Unique domain identifier for routing and access
    )
    status: Optional[str] = (
        None  # Current operational status of the tenant. Draft: initial setup phase, Prospect: evaluation or trial, Active: fully operational, Archived: no longer active but data preserved.
    )
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
    users: Optional[Optional[List[User]]] = (
        None  # List of users associated with this tenant. Only included when requested with ?include=users.
    )
    agents: Optional[Optional[List[AgentSummary]]] = (
        None  # List of AI agents associated with this tenant. Only included when requested with ?include=agents.
    )
    datasources: Optional[Optional[List[DataSource]]] = (
        None  # List of data sources associated with this tenant. Only included when requested with ?include=datasources.
    )
    _count: Optional[Optional[Dict[str, Any]]] = (
        None  # Count of related entities. Included automatically when related entities are requested.
    )
