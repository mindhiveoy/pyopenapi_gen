from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class AgentHistory:
    """
    Data model for AgentHistory

    Attributes:
        agent_id (str): The ID of the agent this revision belongs to
        revision (int): The revision number
        name (str): Agent name at the time of this revision
        description (Optional[str]): Agent description at the time of this revision
        instructions (Optional[str]): Agent instructions at the time of this revision
        config (Any): Agent configuration snapshot at the time of this revision (structure depends on agent type/settings)
        created_at (datetime): Timestamp when this revision was created
        created_by (Dict[str, Any]): No description provided.
    """

    agent_id: str
    revision: int
    name: str
    created_at: datetime
    description: Optional[str] = None
    instructions: Optional[str] = None
    config: Any = None
