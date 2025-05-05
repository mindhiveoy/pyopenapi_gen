from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class UpdateFoundationModelRequest:
    """
    Data model for UpdateFoundationModelRequest

    Attributes:
        name (str): Display name for the foundation model
        internal_name (str): Internal name for the foundation model
        type (str): Type of the foundation model
        description (Optional[str]): Description of the foundation model
        context_window (int): Context window size for the foundation model
        max_output (Optional[int]): Maximum output size for the foundation model
        config (Optional[Any]): Configuration for the foundation model
    """

    name: str
    internal_name: str
    type: str
    context_window: int
    description: Optional[str] = None
    max_output: Optional[int] = None
    config: Optional[Any] = None
