from enum import Enum


class JobPriorityEnum(Enum):
    """Priority level of the job"""

    LOW = "low"
    DEFAULT = "default"
    HIGH = "high"
