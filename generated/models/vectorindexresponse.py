from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VectorIndexResponse:
    """
    Schema for vector index response
    """

    id: str = field(default_factory=str)  # Unique identifier for the vector index
    name: str = field(default_factory=str)  # Name of the vector index
    dimension: int = field(
        default_factory=str
    )  # Dimension of the vectors in this index
    description: Optional[str] = None  # Description of the vector index
    config: Optional[Dict[str, Any]] = None  # Configuration for the vector index
    vectorDatabaseId: Optional[str] = (
        None  # ID of the vector database this index belongs to
    )
    createdAt: datetime = field(
        default_factory=str
    )  # When the vector index was created
    updatedAt: datetime = field(
        default_factory=str
    )  # When the vector index was last updated
