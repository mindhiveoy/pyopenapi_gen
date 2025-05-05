from enum import Enum


class MessageContentTypeEnum(Enum):
    """Format of the message content"""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
