from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TenantCreate:
    """
    Data model for TenantCreate

    Attributes:
        name (str): The name of the tenant organization
        domain (str): Unique domain identifier for routing and access
        description (Optional[str]): Optional description of the tenant
        status (str): Current operational status of the tenant
        settings (Any): Custom settings for the tenant
        theme (Any): UI theme customization for the tenant
        active (Optional[bool]): Whether the tenant is currently active
    """

    name: str
    domain: str
    status: str
    description: Optional[str] = None
    settings: Any = None
    theme: Any = None
    active: Optional[bool] = None
