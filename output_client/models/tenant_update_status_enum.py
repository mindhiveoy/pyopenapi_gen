import json
from enum import Enum, unique

__all__ = ["TenantUpdateStatusEnum"]


@unique
class TenantUpdateStatusEnum(str, Enum):
    """Current operational status of the tenant"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"

    @classmethod
    def from_json(cls, json_str: str) -> "TenantUpdateStatusEnum":
        """Create an instance from a JSON string"""
        return TenantUpdateStatusEnum(json.loads(json_str))
