import json
from enum import Enum, unique

__all__ = ["JobPriorityEnum"]


@unique
class JobPriorityEnum(str, Enum):
    """Priority level of the job"""

    LOW = "low"
    DEFAULT = "default"
    HIGH = "high"

    @classmethod
    def from_json(cls, json_str: str) -> "JobPriorityEnum":
        """Create an instance from a JSON string"""
        return JobPriorityEnum(json.loads(json_str))
