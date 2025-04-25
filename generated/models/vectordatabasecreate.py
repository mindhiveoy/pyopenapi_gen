from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class VectorDatabaseCreate:
    """
    Schema for creating a new vector database
    """

    name: str = field(default_factory=str)  # Name of the vector database
    type: str = field(default_factory=str)  # Type of vector database
    description: Optional[str] = None  # Description of the vector database
    config: Optional[Dict[str, Any]] = None  # Configuration for the vector database
