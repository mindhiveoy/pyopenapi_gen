from enum import Enum


class MessageRoleEnum(Enum):
    """Role of the message sender"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"
    TOOL = "tool"
