from dataclasses import dataclass


@dataclass
class MessageResponse:
    """
    Data model for MessageResponse

    Attributes:
        data (Dict[str, Any]): Message model representing individual exchanges between users and AI assistants.
    """
