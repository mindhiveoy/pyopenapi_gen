from enum import Enum


class TenantStatusEnum(Enum):
    """Current operational status of the tenant. Draft: initial setup phase, Prospect: evaluation or trial, Active: fully operational, Archived: no longer active but data preserved."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"
