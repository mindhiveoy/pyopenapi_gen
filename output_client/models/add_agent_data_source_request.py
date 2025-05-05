from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AddAgentDataSourceRequest:
    """
    Data model for AddAgentDataSourceRequest

    Attributes:
        data_source_id (str): No description provided.
        description (Optional[str]): No description provided.
        instructions (Optional[str]): No description provided.
        config (Any): No description provided.
    """

    data_source_id: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    config: Any = None
