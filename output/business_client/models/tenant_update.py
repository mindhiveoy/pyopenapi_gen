from dataclasses import dataclass
from typing import Any, Optional
from .tenant_update_status_enum import TenantUpdateStatusEnum


@dataclass
class TenantUpdate:
    """
    Data model for TenantUpdate

    Attributes:
        name (Optional[str]): The name of the tenant organization
        domain (Optional[str]): Unique domain identifier for routing and access
        description (Optional[str]): Optional description of the tenant
        status (Optional[TenantUpdateStatusEnum]): Current operational status of the tenant
        settings (Optional[Any]): Custom settings for the tenant
        theme (Optional[Any]): UI theme customization for the tenant
        active (Optional[bool]): Whether the tenant is currently active
    """

    name: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TenantUpdateStatusEnum] = None
    settings: Optional[Any] = None
    theme: Optional[Any] = None
    active: Optional[bool] = None
