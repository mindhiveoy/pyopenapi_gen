from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class UpdateDocumentRequest:
    """
    Data model for UpdateDocumentRequest

    Attributes:
        url (Optional[str]): The URL of the source document
        type (Optional[str]): The type of the document
        mime_type (Optional[str]): The MIME type of the document
        markdown (Optional[str]): The markdown content of the document
        html (Optional[str]): The HTML content of the document
        last_modified (Optional[str]): The last modified information from the source
        etag (Optional[str]): The etag information from the source
        metadata (Optional[Dict[str, Any]]): The metadata from the source
    """

    url: Optional[str] = None
    type: Optional[str] = None
    mime_type: Optional[str] = None
    markdown: Optional[str] = None
    html: Optional[str] = None
    last_modified: Optional[str] = None
    etag: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
