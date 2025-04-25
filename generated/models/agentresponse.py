from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentResponse:
    """
    Agent response with optional included relations
    """

    data: Optional[Agent] = (
        None  # AI assistant configuration model. Represents intelligent agents with their behavior settings, knowledge sources, and interaction capabilities.
    )
    revision: Optional[int] = None  # The new revision number after the update
