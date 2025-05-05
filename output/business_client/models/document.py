from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from .document_content_type_enum import DocumentContentTypeEnum
from .document_status_enum import DocumentStatusEnum


@dataclass
class Document:
    """
    Document model representing content units for AI knowledge retrieval and processing.

    Attributes:
        id (Optional[str]): Unique identifier for the document
        title (Optional[str]): Document title or name
        content (Optional[str]): Document textual content
        content_type (Optional[DocumentContentTypeEnum]): Format of the document content (e.g., text, markdown, html)
        metadata (Optional[Any]): Additional document metadata like author, tags, categories
        data_source_id (Optional[str]): Source system identifier
        tenant_id (Optional[str]): Associated tenant ID
        parent_id (Optional[str]): ID of the parent document if this is a child
        source_url (Optional[str]): Original source URL of the document
        status (Optional[DocumentStatusEnum]): Current processing status of the document
        created_at (Optional[datetime]): Creation timestamp
        updated_at (Optional[datetime]): Last update timestamp
        error (Optional[str]): Error message if the document failed to process
    """

    id: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[DocumentContentTypeEnum] = None
    metadata: Optional[Any] = None
    data_source_id: Optional[str] = None
    tenant_id: Optional[str] = None
    parent_id: Optional[str] = None
    source_url: Optional[str] = None
    status: Optional[DocumentStatusEnum] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error: Optional[str] = None
