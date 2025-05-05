import json
from enum import Enum, unique

__all__ = ["VectorIndexStatusEnum"]


@unique
class VectorIndexStatusEnum(str, Enum):
    """Status of the vector index"""

    ACTIVE = "active"
    CREATING = "creating"
    UPDATING = "updating"
    DELETING = "deleting"
    ERROR = "error"

    @classmethod
    def from_json(cls, json_str: str) -> "VectorIndexStatusEnum":
        """Create an instance from a JSON string"""
        return VectorIndexStatusEnum(json.loads(json_str))
