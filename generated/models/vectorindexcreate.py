from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class VectorIndexCreate:
    """
    Schema for creating a new vector index
    """

    name: str = field(default_factory=str)  # Name of the vector index
    dimension: int = field(
        default_factory=str
    )  # Dimension of the vectors in this index
    description: Optional[Optional[str]] = None  # Description of the vector index
    metric: Optional[str] = None  # Distance metric used for similarity search
    config: Optional[Dict[str, Any]] = None  # Vector index specific configuration
