import json
from enum import Enum, unique

__all__ = ["JobStatusEnum"]


@unique
class JobStatusEnum(str, Enum):
    """Current status of the job"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

    @classmethod
    def from_json(cls, json_str: str) -> "JobStatusEnum":
        """Create an instance from a JSON string"""
        return JobStatusEnum(json.loads(json_str))
