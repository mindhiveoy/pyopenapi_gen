from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .agent_flat import AgentFlat
from .data_source import DataSource
from .user import User


@dataclass
class Tenant:
    """
    Tenant model for multi-tenant architecture. Represents an organization with its own users, agents, and resources. Core entity for tenant isolation and resource management.

    Attributes:
        id (Optional[str]): Unique identifier for the tenant organization
        name (Optional[str]): Display name of the organization
        domain (Optional[str]): Unique domain identifier for routing and access
        status (Optional[str]): Current operational status of the tenant. Draft: initial setup phase, Prospect: evaluation or trial, Active: fully operational, Archived: no longer active but data preserved.
        created_at (Optional[datetime]): Creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
        users (Optional[List[User]]): List of users associated with this tenant. Only included when requested with ?include=users.
        agents (Optional[List[AgentFlat]]): List of AI agents associated with this tenant. Only included when requested with ?include=agents.
        datasources (Optional[List[DataSource]]): List of data sources associated with this tenant. Only included when requested with ?include=datasources.
        count (Optional[Dict[str, Any]]): Count of related entities. Included automatically when related entities are requested.
    """

    id: Optional[str] = None
    name: Optional[str] = None
    domain: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    users: Optional[List[User]] = None
    agents: Optional[List[AgentFlat]] = None
    datasources: Optional[List[DataSource]] = None
    count: Optional[Dict[str, Any]] = None
