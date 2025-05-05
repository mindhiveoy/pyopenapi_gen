import json
from enum import Enum, unique

__all__ = ["JobUpdateStatusEnum"]


@unique
class JobUpdateStatusEnum(str, Enum):
    """Current status of the job"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

    @classmethod
    def from_json(cls, json_str: str) -> "JobUpdateStatusEnum":
        """Create an instance from a JSON string"""
        return JobUpdateStatusEnum(json.loads(json_str))
