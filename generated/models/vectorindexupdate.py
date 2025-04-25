from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class VectorIndexUpdate:
    """
    Schema for updating an existing vector index
    """

    name: Optional[str] = None  # Name of the vector index
    description: Optional[Optional[str]] = (
        None  # Optional description of the vector index
    )
    metric: Optional[str] = None  # Distance metric used for similarity search
    config: Optional[Dict[str, Any]] = None  # Vector index specific configuration
    embedModelId: Optional[Optional[str]] = (
        None  # ID of the embedding model to use for this index
    )
