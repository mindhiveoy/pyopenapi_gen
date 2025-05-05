from enum import Enum


class JobExecutionCreateStatusEnum(Enum):
    """Initial status of the execution"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
