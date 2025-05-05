from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class AgentCreate:
    """
    Data model for AgentCreate

    Attributes:
        name (str): The name of the agent
        description (Optional[str]): Optional description of the agent
        instructions (Optional[Dict[str, Any]]): Configuration instructions for the agent
        config (Optional[Dict[str, Any]]): Configuration for the agent
    """

    name: str
    description: Optional[str] = None
    instructions: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
