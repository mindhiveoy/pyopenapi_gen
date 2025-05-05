from enum import Enum


class TenantCreateStatusEnum(Enum):
    """Current operational status of the tenant"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
