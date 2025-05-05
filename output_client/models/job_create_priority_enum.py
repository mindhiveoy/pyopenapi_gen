import json
from enum import Enum, unique

__all__ = ["JobCreatePriorityEnum"]


@unique
class JobCreatePriorityEnum(str, Enum):
    """Execution priority"""

    LOW = "low"
    DEFAULT = "default"
    HIGH = "high"

    @classmethod
    def from_json(cls, json_str: str) -> "JobCreatePriorityEnum":
        """Create an instance from a JSON string"""
        return JobCreatePriorityEnum(json.loads(json_str))
