from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class Chat:
    """
    Chat model for conversation sessions. Represents interactive dialogues between users and AI assistants, including context and history.

    Attributes:
        id (Optional[str]): Unique identifier for the chat session
        title (Optional[str]): Optional display title for the chat session
        parent_id (Optional[str]): ID of the parent chat if this is a reply
        agent_id (Optional[str]): Reference to the associated AI agent
        user_id (Optional[str]): Reference to the associated user, if authenticated
        session_id (Optional[str]): Session identifier for anonymous users
        metadata (Any): Additional metadata about the chat, such as topic, language, or custom properties
        created_at (Optional[datetime]): Creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
    """

    id: Optional[str] = None
    title: Optional[str] = None
    parent_id: Optional[str] = None
    agent_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Any = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
