from enum import Enum


class VectorIndexStatusEnum(Enum):
    """Status of the vector index"""

    ACTIVE = "active"
    CREATING = "creating"
    UPDATING = "updating"
    DELETING = "deleting"
    ERROR = "error"
