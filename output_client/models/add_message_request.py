from dataclasses import dataclass


@dataclass
class AddMessageRequest:
    """
    Data model for AddMessageRequest

    Attributes:
        message (str): The message content
        role (str): The role of the message sender
    """

    message: str
    role: str
