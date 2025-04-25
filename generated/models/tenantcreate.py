from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class TenantCreate:
    name: str = field(default_factory=str)  # The name of the tenant organization
    domain: str = field(
        default_factory=str
    )  # Unique domain identifier for routing and access
    description: Optional[str] = None  # Optional description of the tenant
    status: str = field(default_factory=str)  # Current operational status of the tenant
    settings: Optional[Dict[str, Any]] = None  # Custom settings for the tenant
    theme: Optional[Dict[str, Any]] = None  # UI theme customization for the tenant
    active: Optional[bool] = None  # Whether the tenant is currently active
