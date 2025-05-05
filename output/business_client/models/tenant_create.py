from dataclasses import dataclass
from typing import Any, Optional
from .tenant_create_status_enum import TenantCreateStatusEnum


@dataclass
class TenantCreate:
    """
    Data model for TenantCreate

    Attributes:
        name (str): The name of the tenant organization
        domain (str): Unique domain identifier for routing and access
        description (Optional[str]): Optional description of the tenant
        status (TenantCreateStatusEnum): Current operational status of the tenant
        settings (Optional[Any]): Custom settings for the tenant
        theme (Optional[Any]): UI theme customization for the tenant
        active (Optional[bool]): Whether the tenant is currently active
    """

    name: str
    domain: str
    status: TenantCreateStatusEnum
    description: Optional[str] = None
    settings: Optional[Any] = None
    theme: Optional[Any] = None
    active: Optional[bool] = None
