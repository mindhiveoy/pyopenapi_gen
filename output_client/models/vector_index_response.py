from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class VectorIndexResponse:
    """
    Schema for vector index response

    Attributes:
        id (str): Unique identifier for the vector index
        name (str): Name of the vector index
        dimension (int): Dimension of the vectors in this index
        description (Optional[str]): Description of the vector index
        config (Any): Configuration for the vector index
        vector_database_id (Optional[str]): ID of the vector database this index belongs to
        created_at (datetime): When the vector index was created
        updated_at (datetime): When the vector index was last updated
    """

    id: str
    name: str
    dimension: int
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    config: Any = None
    vector_database_id: Optional[str] = None
