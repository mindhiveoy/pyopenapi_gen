from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from .message_content_type_enum import MessageContentTypeEnum
from .message_role_enum import MessageRoleEnum


@dataclass
class Message:
    """
    Message model representing individual exchanges between users and AI assistants.

    Attributes:
        id (Optional[str]): Unique identifier for the message
        chat_id (Optional[str]): ID of the chat this message belongs to
        role (Optional[MessageRoleEnum]): Role of the message sender
        content (Optional[str]): Message content
        content_type (Optional[MessageContentTypeEnum]): Format of the message content
        metadata (Optional[Any]): Additional message metadata
        token_count (Optional[int]): Count of tokens in this message
        response_token_count (Optional[int]): Count of tokens in the response to this message (for user messages)
        reference_id (Optional[str]): Reference to external ID for this message
        created_at (Optional[datetime]): Message creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
        parent_id (Optional[str]): ID of the parent message if this is a reply
        agent_id (Optional[str]): ID of the agent who sent the message
        user_id (Optional[str]): ID of the user who sent the message
        error (Optional[str]): Error message if the message failed to send
    """

    id: Optional[str] = None
    chat_id: Optional[str] = None
    role: Optional[MessageRoleEnum] = None
    content: Optional[str] = None
    content_type: Optional[MessageContentTypeEnum] = None
    metadata: Optional[Any] = None
    token_count: Optional[int] = None
    response_token_count: Optional[int] = None
    reference_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    parent_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    error: Optional[str] = None
