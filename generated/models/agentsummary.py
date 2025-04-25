from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentSummary:
    id: Optional[str] = None  # Unique identifier for the AI assistant
    name: Optional[str] = None  # Display name of the AI assistant
    status: Optional[str] = None  # Current operational status of the agent
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
