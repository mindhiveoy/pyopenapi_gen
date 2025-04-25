from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Feedback:
    """
    Feedback model for capturing user evaluations of AI responses for
    quality improvement.
    """

    id: Optional[str] = None  # Unique identifier for the feedback entry
    userId: Optional[Optional[str]] = None  # ID of the user who gave the feedback
    agentId: Optional[Optional[str]] = None  # ID of the agent the feedback is about
    chatId: Optional[Optional[str]] = None  # ID of the chat session
    messageId: Optional[Optional[str]] = None  # ID of the message the feedback is about
    rating: Optional[Optional[int]] = None  # Numerical rating (typically 1-5)
    type: Optional[str] = None  # Type of feedback provided
    comment: Optional[Optional[str]] = None  # Optional detailed textual feedback
    tags: Optional[Optional[List[str]]] = None  # Categorization tags for the feedback
    tenantId: Optional[str] = None  # Associated tenant ID
    createdAt: Optional[datetime] = None  # Feedback submission timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
    user: Optional[Any] = None  # User object (if included)
    agent: Optional[Any] = None  # Agent object (if included)
    chat: Optional[Any] = None  # Chat object (if included)
    message: Optional[Any] = None  # Message object (if included)
