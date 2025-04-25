from typing import Any, Dict, List, Optional

from dataclasses import dataclass, field


@dataclass
class UpdateDocumentRequest:
    url: Optional[str] = None  # The URL of the source document
    type: Optional[str] = None  # The type of the document
    mimeType: Optional[str] = None  # The MIME type of the document
    markdown: Optional[str] = None  # The markdown content of the document
    html: Optional[str] = None  # The HTML content of the document
    lastModified: Optional[str] = None  # The last modified information from the source
    etag: Optional[str] = None  # The etag information from the source
    metadata: Optional[Dict[str, Any]] = None  # The metadata from the source
