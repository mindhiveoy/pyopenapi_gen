from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class UpdateAgentDataSourceRequest:
    """
    Data model for UpdateAgentDataSourceRequest

    Attributes:
        description (Optional[str]): No description provided.
        instructions (Optional[str]): No description provided.
        config (Optional[Any]): No description provided.
    """

    description: Optional[str] = None
    instructions: Optional[str] = None
    config: Optional[Any] = None
