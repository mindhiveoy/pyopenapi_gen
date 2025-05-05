from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class VectorIndexUpdate:
    """
    Schema for updating an existing vector index

    Attributes:
        name (Optional[str]): Name of the vector index
        description (Optional[str]): Optional description of the vector index
        metric (Optional[str]): Distance metric used for similarity search
        config (Optional[Dict[str, Any]]): Vector index specific configuration
        embed_model_id (Optional[str]): ID of the embedding model to use for this index
    """

    name: Optional[str] = None
    description: Optional[str] = None
    metric: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    embed_model_id: Optional[str] = None
