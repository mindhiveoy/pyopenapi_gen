from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class ChatCreate:
    """
    Schema for creating a new chat session
    """

    title: Optional[Optional[str]] = None  # Optional title for the chat session
    parentId: Optional[Optional[str]] = None  # ID of the parent chat if this is a reply
    agentId: str = field(
        default_factory=str
    )  # ID of the agent associated with this chat
    userId: Optional[Optional[str]] = None  # ID of the user who started the chat
    metadata: Optional[Optional[Dict[str, Any]]] = (
        None  # Optional metadata for the chat session
    )
    initialMessage: Optional[Optional[str]] = (
        None  # Optional first user message to start the conversation
    )
