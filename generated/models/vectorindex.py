from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class VectorIndex:
    """
    Vector index model for organized collections of vectors within vector
    databases, optimized for efficient search.
    """

    id: Optional[str] = None  # Unique identifier for the vector index
    name: Optional[str] = None  # Human-readable name for the vector index
    vectorDatabaseId: Optional[str] = None  # Associated vector database ID
    config: Optional[Optional[Dict[str, Any]]] = (
        None  # Configuration object for the vector index
    )
    dimensions: Optional[int] = None  # Vector dimension size for this index
    status: Optional[Optional[str]] = None  # Status of the vector index
    error: Optional[Optional[str]] = None  # Error message if the index failed
    description: Optional[Optional[str]] = None  # Description of the vector index
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata about the index
    externalId: Optional[str] = None  # Reference ID in the external vector store
    tenantId: Optional[str] = None  # Associated tenant ID
    embeddinCount: Optional[int] = None  # Number of embeddings stored in this index
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
    lastSyncAt: Optional[Optional[datetime]] = None  # Timestamp of the last sync
    lastSyncStatus: Optional[Optional[str]] = None  # Status of the last sync
