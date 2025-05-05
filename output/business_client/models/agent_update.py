from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentUpdate:
    """
    Data model for AgentUpdate

    Attributes:
        name (Optional[str]): The name of the agent
        description (Optional[str]): Optional description of the agent
        instructions (Optional[Dict[str, Any]]): Configuration instructions for the agent
        config (Optional[Dict[str, Any]]): Configuration for the agent
    """

    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
