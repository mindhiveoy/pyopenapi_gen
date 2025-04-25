from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Message:
    """
    Message model representing individual exchanges between users and AI
    assistants.
    """

    id: Optional[str] = None  # Unique identifier for the message
    chatId: Optional[Optional[str]] = None  # ID of the chat this message belongs to
    role: Optional[str] = None  # Role of the message sender
    content: Optional[Optional[str]] = None  # Message content
    contentType: Optional[Optional[str]] = None  # Format of the message content
    metadata: Optional[Optional[Dict[str, Any]]] = None  # Additional message metadata
    tokenCount: Optional[Optional[int]] = None  # Count of tokens in this message
    responseTokenCount: Optional[Optional[int]] = (
        None  # Count of tokens in the response to this message (for user messages)
    )
    referenceId: Optional[Optional[str]] = (
        None  # Reference to external ID for this message
    )
    createdAt: Optional[datetime] = None  # Message creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
    parentId: Optional[Optional[str]] = (
        None  # ID of the parent message if this is a reply
    )
    agentId: Optional[Optional[str]] = None  # ID of the agent who sent the message
    userId: Optional[Optional[str]] = None  # ID of the user who sent the message
    error: Optional[Optional[str]] = None  # Error message if the message failed to send
