from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AddDebugMessageRequest:
    """
    Data model for AddDebugMessageRequest

    Attributes:
        messages (List[Dict[str, Any]]): Array of debug messages
    """
