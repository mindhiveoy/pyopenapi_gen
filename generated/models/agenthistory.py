from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentHistory:
    agentId: str = field(
        default_factory=str
    )  # The ID of the agent this revision belongs to
    revision: int = field(default_factory=str)  # The revision number
    name: str = field(default_factory=str)  # Agent name at the time of this revision
    description: Optional[str] = None  # Agent description at the time of this revision
    instructions: Optional[str] = (
        None  # Agent instructions at the time of this revision
    )
    config: Optional[Dict[str, Any]] = (
        None  # Agent configuration snapshot at the time of this revision (structure depends on agent type/settings)
    )
    createdAt: datetime = field(
        default_factory=str
    )  # Timestamp when this revision was created
    createdBy: Dict[str, Any] = field(default_factory=dict)  #
