from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class TenantUpdate:
    name: Optional[str] = None  # The name of the tenant organization
    domain: Optional[str] = None  # Unique domain identifier for routing and access
    description: Optional[str] = None  # Optional description of the tenant
    status: Optional[str] = None  # Current operational status of the tenant
    settings: Optional[Dict[str, Any]] = None  # Custom settings for the tenant
    theme: Optional[Dict[str, Any]] = None  # UI theme customization for the tenant
    active: Optional[bool] = None  # Whether the tenant is currently active
