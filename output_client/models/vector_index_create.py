from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class VectorIndexCreate:
    """
    Schema for creating a new vector index

    Attributes:
        name (str): Name of the vector index
        dimension (int): Dimension of the vectors in this index
        description (Optional[str]): Description of the vector index
        metric (Optional[str]): Distance metric used for similarity search
        config (Optional[Dict[str, Any]]): Vector index specific configuration
    """

    name: str
    dimension: int
    description: Optional[str] = None
    metric: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
