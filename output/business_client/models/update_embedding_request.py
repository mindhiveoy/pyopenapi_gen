from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class UpdateEmbeddingRequest:
    """
    Data model for UpdateEmbeddingRequest

    Attributes:
        name (str): Display name for the embedding
        internal_name (str): Internal name for the embedding
        description (Optional[str]): Description of the embedding
        dimension (int): Dimension of the embedding vectors
        config (Optional[Any]): Configuration for the embedding
    """

    name: str
    internal_name: str
    dimension: int
    description: Optional[str] = None
    config: Optional[Any] = None
