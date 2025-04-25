from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VectorDatabase:
    """
    Vector database model for systems that store and search vector
    embeddings for semantic retrieval.
    """

    id: Optional[str] = None  # Unique identifier for the vector database
    name: Optional[str] = None  # Human-readable name for the vector database
    type: Optional[str] = None  # Type of vector database system
    config: Optional[Optional[Dict[str, Any]]] = (
        None  # Configuration object for the vector database
    )
    status: Optional[str] = None  # Current connection status of the database
    description: Optional[Optional[str]] = None  # Description of the vector database
    tenantId: Optional[str] = None  # Associated tenant ID
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
