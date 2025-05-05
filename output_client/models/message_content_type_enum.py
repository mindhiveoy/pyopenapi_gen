import json
from enum import Enum, unique

__all__ = ["MessageContentTypeEnum"]


@unique
class MessageContentTypeEnum(str, Enum):
    """Format of the message content"""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"

    @classmethod
    def from_json(cls, json_str: str) -> "MessageContentTypeEnum":
        """Create an instance from a JSON string"""
        return MessageContentTypeEnum(json.loads(json_str))
