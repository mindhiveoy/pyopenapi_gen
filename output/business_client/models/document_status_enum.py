from enum import Enum


class DocumentStatusEnum(Enum):
    """Current processing status of the document"""

    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"
