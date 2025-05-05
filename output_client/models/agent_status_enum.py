import json
from enum import Enum, unique

__all__ = ["AgentStatusEnum"]


@unique
class AgentStatusEnum(str, Enum):
    """Current operational status of the agent"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

    @classmethod
    def from_json(cls, json_str: str) -> "AgentStatusEnum":
        """Create an instance from a JSON string"""
        return AgentStatusEnum(json.loads(json_str))
