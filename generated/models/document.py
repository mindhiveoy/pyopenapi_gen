from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Document:
    """
    Document model representing content units for AI knowledge retrieval and
    processing.
    """

    id: Optional[str] = None  # Unique identifier for the document
    title: Optional[str] = None  # Document title or name
    content: Optional[str] = None  # Document textual content
    contentType: Optional[str] = (
        None  # Format of the document content (e.g., text, markdown, html)
    )
    metadata: Optional[Optional[Dict[str, Any]]] = (
        None  # Additional document metadata like author, tags, categories
    )
    dataSourceId: Optional[Optional[str]] = None  # Source system identifier
    tenantId: Optional[str] = None  # Associated tenant ID
    parentId: Optional[Optional[str]] = (
        None  # ID of the parent document if this is a child
    )
    sourceUrl: Optional[Optional[str]] = None  # Original source URL of the document
    status: Optional[str] = None  # Current processing status of the document
    createdAt: Optional[datetime] = None  # Creation timestamp
    updatedAt: Optional[datetime] = None  # Last update timestamp
    error: Optional[Optional[str]] = (
        None  # Error message if the document failed to process
    )
