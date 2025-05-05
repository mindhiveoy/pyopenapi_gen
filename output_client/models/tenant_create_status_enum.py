import json
from enum import Enum, unique

__all__ = ["TenantCreateStatusEnum"]


@unique
class TenantCreateStatusEnum(str, Enum):
    """Current operational status of the tenant"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"

    @classmethod
    def from_json(cls, json_str: str) -> "TenantCreateStatusEnum":
        """Create an instance from a JSON string"""
        return TenantCreateStatusEnum(json.loads(json_str))
