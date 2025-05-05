import json
from enum import Enum, unique

__all__ = ["DocumentStatusEnum"]


@unique
class DocumentStatusEnum(str, Enum):
    """Current processing status of the document"""

    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"

    @classmethod
    def from_json(cls, json_str: str) -> "DocumentStatusEnum":
        """Create an instance from a JSON string"""
        return DocumentStatusEnum(json.loads(json_str))
