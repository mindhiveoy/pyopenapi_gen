from enum import Enum


class JobCreatePriorityEnum(Enum):
    """Execution priority"""

    LOW = "low"
    DEFAULT = "default"
    HIGH = "high"
