from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class AgentUpdate:
    name: Optional[str] = None  # The name of the agent
    description: Optional[str] = None  # Optional description of the agent
    instructions: Optional[Dict[str, Any]] = (
        None  # Configuration instructions for the agent
    )
    config: Optional[Dict[str, Any]] = None  # Configuration for the agent
