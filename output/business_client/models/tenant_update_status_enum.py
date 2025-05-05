from enum import Enum


class TenantUpdateStatusEnum(Enum):
    """Current operational status of the tenant"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
