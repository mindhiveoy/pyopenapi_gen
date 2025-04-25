from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TenantResponse:
    """
    Tenant response with optional included relations
    """

    data: Optional[Tenant] = (
        None  # Tenant model for multi-tenant architecture. Represents an organization with its own users, agents, and resources. Core entity for tenant isolation and resource management.
    )
