from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class CreateEmbeddingRequest:
    name: str = field(default_factory=str)  # Display name for the embedding
    internalName: str = field(default_factory=str)  # Internal name for the embedding
    description: Optional[str] = None  # Description of the embedding
    dimension: int = field(default_factory=str)  # Dimension of the embedding vectors
    config: Optional[Dict[str, Any]] = None  # Configuration for the embedding
