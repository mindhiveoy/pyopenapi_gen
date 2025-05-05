from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserListResponse:
    """
    Data model for UserListResponse

    Attributes:
        id (str): Unique identifier for the chat
        title (str): Title of the chat
        description (Optional[str]): Description of the chat
        agent_id (Optional[str]): ID of the agent this chat belongs to
        tenant_id (Optional[str]): ID of the tenant this chat belongs to
        created_at (datetime): Timestamp when the chat was created
        updated_at (datetime): Timestamp when the chat was last updated
        message_count (Optional[int]): Number of messages in the chat
        feedback_count (Optional[int]): Number of feedback messages in the chat
    """

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    agent_id: Optional[str] = None
    tenant_id: Optional[str] = None
    message_count: Optional[int] = None
    feedback_count: Optional[int] = None
