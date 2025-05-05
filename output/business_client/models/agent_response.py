from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class AgentResponse:
    """
    Data model for AgentResponse

    Attributes:
        data (Dict[str, Any]): AI assistant configuration model. Represents intelligent agents with their behavior settings, knowledge sources, and interaction capabilities.
    """
