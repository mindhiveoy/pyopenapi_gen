import json
from enum import Enum, unique

__all__ = ["JobExecutionCreateStatusEnum"]


@unique
class JobExecutionCreateStatusEnum(str, Enum):
    """Initial status of the execution"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @classmethod
    def from_json(cls, json_str: str) -> "JobExecutionCreateStatusEnum":
        """Create an instance from a JSON string"""
        return JobExecutionCreateStatusEnum(json.loads(json_str))
