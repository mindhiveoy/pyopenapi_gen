from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class VectorIndex:
    """
    Vector index model for organized collections of vectors within vector databases, optimized for efficient search.

    Attributes:
        id (Optional[str]): Unique identifier for the vector index
        name (Optional[str]): Human-readable name for the vector index
        vector_database_id (Optional[str]): Associated vector database ID
        config (Any): Configuration object for the vector index
        dimensions (Optional[int]): Vector dimension size for this index
        status (Optional[str]): Status of the vector index
        error (Optional[str]): Error message if the index failed
        description (Optional[str]): Description of the vector index
        metadata (Any): Additional metadata about the index
        external_id (Optional[str]): Reference ID in the external vector store
        tenant_id (Optional[str]): Associated tenant ID
        embeddin_count (Optional[int]): Number of embeddings stored in this index
        created_at (Optional[datetime]): Creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
        last_sync_at (Optional[datetime]): Timestamp of the last sync
        last_sync_status (Optional[str]): Status of the last sync
    """

    id: Optional[str] = None
    name: Optional[str] = None
    vector_database_id: Optional[str] = None
    config: Any = None
    dimensions: Optional[int] = None
    status: Optional[str] = None
    error: Optional[str] = None
    description: Optional[str] = None
    metadata: Any = None
    external_id: Optional[str] = None
    tenant_id: Optional[str] = None
    embeddin_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: Optional[str] = None
