import json
from enum import Enum, unique

__all__ = ["TenantStatusEnum"]


@unique
class TenantStatusEnum(str, Enum):
    """Current operational status of the tenant. Draft: initial setup phase, Prospect: evaluation or trial, Active: fully operational, Archived: no longer active but data preserved."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"

    @classmethod
    def from_json(cls, json_str: str) -> "TenantStatusEnum":
        """Create an instance from a JSON string"""
        return TenantStatusEnum(json.loads(json_str))
