from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class MessageResponse:
    """
    Data model for MessageResponse

    Attributes:
        data (Dict[str, Any]): Message model representing individual exchanges between users and AI assistants.
    """
