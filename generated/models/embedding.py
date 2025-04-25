from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Embedding:
    """
    Embedding model for vector representations of text used in semantic
    search and retrieval.
    """

    id: Optional[str] = None  # Unique identifier for the embedding
    documentId: Optional[Optional[str]] = None  # Associated document ID
    chunk: Optional[Optional[str]] = None  # Text segment that was embedded
    chunkIndex: Optional[Optional[int]] = (
        None  # Position of this chunk within the original document
    )
    vectorDatabaseId: Optional[str] = None  # Associated vector database ID
    vectorIndexId: Optional[str] = None  # Associated vector index ID
    externalId: Optional[Optional[str]] = (
        None  # ID reference in the external vector store
    )
    modelId: Optional[str] = (
        None  # Embedding model identifier used to generate the vectors
    )
    metadata: Optional[Optional[Dict[str, Any]]] = (
        None  # Additional metadata about the embedding
    )
    tenantId: Optional[str] = None  # Associated tenant ID
    description: Optional[Optional[str]] = None  # Description of the embedding
    model: Optional[Optional[str]] = None  # Model used for the embedding
    status: Optional[Optional[str]] = None  # Status of the embedding
    error: Optional[Optional[str]] = None  # Error message if the embedding failed
    createdAt: Optional[Optional[datetime]] = None  # Creation timestamp
    updatedAt: Optional[Optional[datetime]] = None  # Last update timestamp
