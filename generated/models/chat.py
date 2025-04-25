from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Chat:
    """
    Chat model for conversation sessions. Represents interactive dialogues
    between users and AI assistants, including context and history.
    """

    id: Optional[str] = None  # Unique identifier for the chat session
    title: Optional[Optional[str]] = None  # Optional display title for the chat session
    parentId: Optional[Optional[str]] = None  # ID of the parent chat if this is a reply
    agentId: Optional[Optional[str]] = None  # Reference to the associated AI agent
    userId: Optional[Optional[str]] = (
        None  # Reference to the associated user, if authenticated
    )
    sessionId: Optional[Optional[str]] = None  # Session identifier for anonymous users
    metadata: Optional[Dict[str, Any]] = (
        None  # Additional metadata about the chat, such as topic, language, or custom properties
    )
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
    messageCount: Optional[int] = (
        None  # Number of messages in the chat (included when messageCount is in include parameter)
    )
    feedbackCount: Optional[int] = (
        None  # Number of feedback messages in the chat (included when feedbackCount is in include parameter)
    )
