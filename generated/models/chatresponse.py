from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatResponse:
    id: str = field(default_factory=str)  # Unique identifier for the chat
    title: str = field(default_factory=str)  # Title of the chat
    description: Optional[str] = None  # Description of the chat
    agentId: Optional[str] = None  # ID of the agent this chat belongs to
    tenantId: Optional[str] = None  # ID of the tenant this chat belongs to
    createdAt: datetime = field(
        default_factory=str
    )  # Timestamp when the chat was created
    updatedAt: datetime = field(
        default_factory=str
    )  # Timestamp when the chat was last updated
    messageCount: Optional[int] = None  # Number of messages in the chat
    feedbackCount: Optional[int] = None  # Number of feedback messages in the chat
