from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TenantUpdate:
    """
    Data model for TenantUpdate

    Attributes:
        name (Optional[str]): The name of the tenant organization
        domain (Optional[str]): Unique domain identifier for routing and access
        description (Optional[str]): Optional description of the tenant
        status (Optional[str]): Current operational status of the tenant
        settings (Any): Custom settings for the tenant
        theme (Any): UI theme customization for the tenant
        active (Optional[bool]): Whether the tenant is currently active
    """

    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    settings: Any = None
    theme: Any = None
    active: Optional[bool] = None
