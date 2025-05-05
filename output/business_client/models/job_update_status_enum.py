from enum import Enum


class JobUpdateStatusEnum(Enum):
    """Current status of the job"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SCHEDULED = "scheduled"
