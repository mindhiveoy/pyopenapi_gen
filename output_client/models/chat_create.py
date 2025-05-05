from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ChatCreate:
    """
    Schema for creating a new chat session

    Attributes:
        title (Optional[str]): Optional title for the chat session
        parent_id (Optional[str]): ID of the parent chat if this is a reply
        agent_id (str): ID of the agent associated with this chat
        user_id (Optional[str]): ID of the user who started the chat
        metadata (Any): Optional metadata for the chat session
        initial_message (Optional[str]): Optional first user message to start the conversation
    """

    agent_id: str
    title: Optional[str] = None
    parent_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Any = None
    initial_message: Optional[str] = None
