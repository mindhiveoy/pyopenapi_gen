import json
from enum import Enum, unique

__all__ = ["JobCreateStatusEnum"]


@unique
class JobCreateStatusEnum(str, Enum):
    """Current status of the job"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"

    @classmethod
    def from_json(cls, json_str: str) -> "JobCreateStatusEnum":
        """Create an instance from a JSON string"""
        return JobCreateStatusEnum(json.loads(json_str))
