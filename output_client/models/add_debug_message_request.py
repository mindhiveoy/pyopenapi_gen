from dataclasses import dataclass


@dataclass
class AddDebugMessageRequest:
    """
    Data model for AddDebugMessageRequest

    Attributes:
        messages (List[Dict[str, Any]]): Array of debug messages
    """
