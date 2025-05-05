import json
from enum import Enum, unique

__all__ = ["MessageRoleEnum"]


@unique
class MessageRoleEnum(str, Enum):
    """Role of the message sender"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"
    TOOL = "tool"

    @classmethod
    def from_json(cls, json_str: str) -> "MessageRoleEnum":
        """Create an instance from a JSON string"""
        return MessageRoleEnum(json.loads(json_str))
