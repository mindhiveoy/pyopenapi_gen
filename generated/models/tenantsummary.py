from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TenantSummary:
    id: Optional[str] = None  # Unique identifier for the tenant organization
    name: Optional[str] = None  # Display name of the organization
    status: Optional[str] = None  # Current operational status of the tenant
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
