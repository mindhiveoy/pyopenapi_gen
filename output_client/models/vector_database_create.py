from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class VectorDatabaseCreate:
    """
    Schema for creating a new vector database

    Attributes:
        name (str): Name of the vector database
        type (str): Type of vector database
        description (Optional[str]): Description of the vector database
        config (Any): Configuration for the vector database
    """

    name: str
    type: str
    description: Optional[str] = None
    config: Any = None
